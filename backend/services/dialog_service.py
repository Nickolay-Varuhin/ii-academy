"""Бизнес-логика диалогового симулятора.
Важные особенности:
1. Отправка сообщения пользователя и генерация ответа AI — ДВА разных шага.
   Это даёт мгновенный UX: фронт видит своё сообщение сразу, потом ждёт AI.
2. Все обращения к AI идут через LLMProvider (см. services/llm/).
   Если провайдер упадёт — FallbackProvider переключится на MockProvider."""
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from models import (Scenario, DialogSession, DialogMessage, DialogFeedback,
                    UserSkillLevel, DialogStatus, SenderType, MasteryStatus,
                    Skill)
from services.llm import get_llm_provider
from services.llm.base import ScenarioContext


class DialogService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm = get_llm_provider()

    # ─── Вспомогательное: собираем ScenarioContext для LLM ──

    async def _build_scenario_context(self, scenario: Scenario) -> ScenarioContext:
        # Название навыка нужно подгрузить отдельно, если не пришло с eager-loading
        skill_name = "soft-skills"
        if scenario.skill_id:
            r = await self.db.execute(
                select(Skill.name).where(Skill.id == scenario.skill_id)
            )
            skill_name = r.scalar() or "soft-skills"
        return ScenarioContext(
            title=scenario.title,
            description=scenario.description,
            initial_prompt=scenario.initial_prompt,
            skill_name=skill_name,
            difficulty=scenario.difficulty or 1,
            max_turns=scenario.max_turns or 10,
        )

    # ─── Запросы на чтение ───────────────────────────────

    async def get_scenarios(self):
        r = await self.db.execute(
            select(Scenario).where(Scenario.is_active == True).order_by(Scenario.difficulty)
        )
        return r.scalars().all()

    async def get_session(self, session_id: int, user_id: int):
        r = await self.db.execute(
            select(DialogSession).options(
                selectinload(DialogSession.messages),
                selectinload(DialogSession.scenario),
                selectinload(DialogSession.feedback),
            ).where(
                DialogSession.id == session_id,
                DialogSession.user_id == user_id,
            )
        )
        session = r.scalar_one_or_none()
        if not session:
            raise ValueError("Сессия не найдена")
        return session

    async def get_user_sessions(self, user_id: int):
        r = await self.db.execute(
            select(DialogSession).options(selectinload(DialogSession.scenario))
            .where(DialogSession.user_id == user_id)
            .order_by(DialogSession.started_at.desc())
        )
        return r.scalars().all()

    # ─── Старт сессии ────────────────────────────────────

    async def start_session(self, user_id: int, scenario_id: int) -> DialogSession:
        scenario = await self.db.get(Scenario, scenario_id)
        if not scenario or not scenario.is_active:
            raise ValueError("Сценарий не найден")

        # Автозавершение предыдущих активных сессий пользователя
        r = await self.db.execute(
            select(DialogSession).where(
                DialogSession.user_id == user_id,
                DialogSession.status == DialogStatus.ACTIVE,
            )
        )
        for active in r.scalars().all():
            active.status = DialogStatus.ABANDONED
            active.ended_at = datetime.utcnow()

        session = DialogSession(
            user_id=user_id,
            scenario_id=scenario_id,
            ai_model_used=self.llm.name,
        )
        self.db.add(session)
        await self.db.flush()

        # Первое сообщение — от AI (вступительная реплика)
        scen_ctx = await self._build_scenario_context(scenario)
        ai_resp = await self.llm.generate_reply([], scen_ctx)
        self.db.add(DialogMessage(
            session_id=session.id,
            sender_type=SenderType.AI,
            message_text=ai_resp.text,
            sentiment_score=ai_resp.sentiment_score,
            intent_category=ai_resp.intent_category,
            ai_response_time_ms=ai_resp.response_time_ms,
        ))
        await self.db.commit()
        return await self.get_session(session.id, user_id)

    # ─── Шаг 1: сохранение сообщения пользователя ───────

    async def save_user_message(self, session_id: int, user_id: int,
                                 text: str) -> DialogMessage:
        session = await self._get_active_session(session_id, user_id)
        sentiment = await self.llm.analyze_sentiment(text)

        msg = DialogMessage(
            session_id=session_id,
            sender_type=SenderType.USER,
            message_text=text,
            sentiment_score=sentiment,
            intent_category="user_input",
        )
        self.db.add(msg)
        await self.db.commit()
        await self.db.refresh(msg)
        return msg

    # ─── Шаг 2: генерация ответа AI ─────────────────────

    async def generate_ai_reply(self, session_id: int, user_id: int):
        session = await self._get_active_session(session_id, user_id)

        scen_ctx = await self._build_scenario_context(session.scenario)
        ctx = [
            {"sender": m.sender_type.value, "text": m.message_text}
            for m in session.messages
        ]
        ai_resp = await self.llm.generate_reply(ctx, scen_ctx)

        ai_msg = DialogMessage(
            session_id=session_id,
            sender_type=SenderType.AI,
            message_text=ai_resp.text,
            sentiment_score=ai_resp.sentiment_score,
            intent_category=ai_resp.intent_category,
            ai_response_time_ms=ai_resp.response_time_ms,
        )
        self.db.add(ai_msg)
        await self.db.flush()

        # Проверка лимита ходов — возможно, сессия сразу закрывается
        user_turns = sum(1 for m in session.messages
                          if m.sender_type == SenderType.USER)
        feedback = None
        if user_turns >= session.scenario.max_turns:
            ctx.append({"sender": "ai", "text": ai_resp.text})
            feedback = await self._complete_internal(session, ctx, scen_ctx)

        await self.db.commit()
        await self.db.refresh(ai_msg)
        return ai_msg, feedback is not None, feedback

    # ─── Принудительное завершение ──────────────────────

    async def complete_session(self, session_id: int, user_id: int):
        session = await self._get_active_session(session_id, user_id)
        scen_ctx = await self._build_scenario_context(session.scenario)
        ctx = [
            {"sender": m.sender_type.value, "text": m.message_text}
            for m in session.messages
        ]
        fb = await self._complete_internal(session, ctx, scen_ctx)
        await self.db.commit()
        return fb

    # ─── Внутреннее ─────────────────────────────────────

    async def _get_active_session(self, session_id: int, user_id: int):
        session = await self.get_session(session_id, user_id)
        if session.status != DialogStatus.ACTIVE:
            raise ValueError("Сессия уже завершена")
        return session

    async def _complete_internal(self, session: DialogSession,
                                   ctx: list[dict],
                                   scen_ctx: ScenarioContext):
        session.status = DialogStatus.COMPLETED
        session.ended_at = datetime.utcnow()
        fb = await self.llm.generate_feedback(ctx, scen_ctx)
        feedback = DialogFeedback(
            session_id=session.id,
            overall_score=fb.overall_score,
            skill_scores=fb.skill_scores,
            ai_feedback_text=fb.feedback_text,
            recommendations=fb.recommendations,
        )
        self.db.add(feedback)
        await self._update_skill_level(session.user_id, session.scenario.skill_id,
                                         fb.overall_score)
        return feedback

    async def _update_skill_level(self, user_id: int, skill_id: int, score: float):
        r = await self.db.execute(
            select(UserSkillLevel).where(
                UserSkillLevel.user_id == user_id,
                UserSkillLevel.skill_id == skill_id,
            )
        )
        level = r.scalar_one_or_none()
        delta = (score - 50) * 0.15

        if level:
            new_level = max(0, min(100, level.current_level + delta))
            level.current_level = round(new_level, 1)
            level.level_confidence = min(1.0, round(level.level_confidence + 0.05, 3))
            level.attempts_count += 1
            level.last_assessed = datetime.utcnow()
            level.mastery_status = (
                MasteryStatus.MASTERED if new_level >= 85
                else MasteryStatus.IN_PROGRESS if new_level >= 40
                else MasteryStatus.NOT_STARTED
            )
        else:
            initial = max(0, min(100, 50 + delta))
            self.db.add(UserSkillLevel(
                user_id=user_id,
                skill_id=skill_id,
                current_level=round(initial, 1),
                level_confidence=0.3,
                attempts_count=1,
                last_assessed=datetime.utcnow(),
                mastery_status=MasteryStatus.IN_PROGRESS,
            ))
