"""Роутер AI-симулятора диалогов."""
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models import (User, Scenario, DialogSession, DialogFeedback,
                    DialogStatus)
from schemas import (ScenarioOut, StartDialogRequest, SendMessageRequest,
                     DialogSessionOut, DialogMessageOut, DialogFeedbackOut)
from auth import get_current_user
from services.dialog_service import DialogService
from config import AI_THINKING_DELAY_MS

router = APIRouter(prefix="/api/dialog", tags=["AI-Симулятор"])


def _session_to_out(s) -> DialogSessionOut:
    return DialogSessionOut(
        id=s.id,
        scenario_id=s.scenario_id,
        scenario_title=s.scenario.title if s.scenario else "",
        status=s.status.value if hasattr(s.status, "value") else s.status,
        started_at=s.started_at,
        ended_at=s.ended_at,
        messages=[
            DialogMessageOut(
                id=m.id,
                sender_type=(m.sender_type.value if hasattr(m.sender_type, "value") else m.sender_type),
                message_text=m.message_text,
                sentiment_score=m.sentiment_score,
                created_at=m.created_at,
            )
            for m in (s.messages or [])
        ],
    )


def _message_to_out(m) -> DialogMessageOut:
    return DialogMessageOut(
        id=m.id,
        sender_type=(m.sender_type.value if hasattr(m.sender_type, "value") else m.sender_type),
        message_text=m.message_text,
        sentiment_score=m.sentiment_score,
        created_at=m.created_at,
    )


@router.get("/scenarios", response_model=list[ScenarioOut])
async def list_scenarios(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Возвращает активные сценарии + историю попыток ТЕКУЩЕГО пользователя.
    Используется для показа галочек «пройдено» на карточках."""
    scenarios = await DialogService(db).get_scenarios()

    stats_r = await db.execute(
        select(
            DialogSession.scenario_id,
            func.count(DialogSession.id).label("attempts"),
            func.count(DialogFeedback.id).label("completed_count"),
            func.max(DialogFeedback.overall_score).label("best_score"),
        )
        .select_from(DialogSession)
        .join(DialogFeedback,
              DialogFeedback.session_id == DialogSession.id, isouter=True)
        .where(DialogSession.user_id == user.id)
        .group_by(DialogSession.scenario_id)
    )
    stats = {
        row[0]: {
            "attempts": row[1] or 0,
            "completed": (row[2] or 0) > 0,
            "best_score": float(row[3]) if row[3] is not None else None,
        }
        for row in stats_r.all()
    }

    return [
        ScenarioOut(
            id=s.id, title=s.title, description=s.description,
            difficulty=s.difficulty, skill_id=s.skill_id,
            max_turns=s.max_turns, is_active=s.is_active,
            completed=stats.get(s.id, {}).get("completed", False),
            attempts_count=stats.get(s.id, {}).get("attempts", 0),
            best_score=stats.get(s.id, {}).get("best_score"),
        )
        for s in scenarios
    ]


@router.post("/start", response_model=DialogSessionOut, status_code=201)
async def start(
    data: StartDialogRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        session = await DialogService(db).start_session(user.id, data.scenario_id)
        return _session_to_out(session)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/{session_id}/message", response_model=DialogMessageOut)
async def send_message(
    session_id: int,
    data: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        msg = await DialogService(db).save_user_message(
            session_id, user.id, data.message_text
        )
        return _message_to_out(msg)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/{session_id}/ai-reply")
async def generate_ai_reply(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await asyncio.sleep(AI_THINKING_DELAY_MS / 1000)

    try:
        ai_msg, completed, feedback = await DialogService(db).generate_ai_reply(
            session_id, user.id
        )
        result = {"message": _message_to_out(ai_msg).model_dump(mode="json"),
                  "session_completed": completed, "feedback": None}
        if feedback:
            result["feedback"] = {
                "overall_score": feedback.overall_score,
                "skill_scores": feedback.skill_scores,
                "ai_feedback_text": feedback.ai_feedback_text,
                "recommendations": feedback.recommendations,
            }
        return result
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/{session_id}/complete", response_model=DialogFeedbackOut)
async def complete(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        fb = await DialogService(db).complete_session(session_id, user.id)
        return DialogFeedbackOut(
            overall_score=fb.overall_score,
            skill_scores=fb.skill_scores,
            ai_feedback_text=fb.ai_feedback_text,
            recommendations=fb.recommendations,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/sessions", response_model=list[DialogSessionOut])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return [_session_to_out(s) for s in await DialogService(db).get_user_sessions(user.id)]


@router.get("/{session_id}", response_model=DialogSessionOut)
async def get_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return _session_to_out(await DialogService(db).get_session(session_id, user.id))
    except ValueError as e:
        raise HTTPException(404, str(e))
