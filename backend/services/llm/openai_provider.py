"""OpenAI-совместимый LLM-провайдер.

Один и тот же код работает с:
  - OpenAI          (base_url="https://api.openai.com/v1")
  - Groq            (base_url="https://api.groq.com/openai/v1")           БЕСПЛАТНО
  - OpenRouter      (base_url="https://openrouter.ai/api/v1")             модели с :free
  - DeepSeek        (base_url="https://api.deepseek.com/v1")              дёшево
  - Together.ai     (base_url="https://api.together.xyz/v1")
  - Mistral         (base_url="https://api.mistral.ai/v1")
  - Fireworks, Anyscale, Moonshot, ...

Достаточно подставить нужный BASE_URL, API_KEY и MODEL в .env.

Если запрос к LLM падает — провайдер выбрасывает исключение, и dialog_service
сам откатится на MockProvider, чтобы чат не ломался."""
import json
import re
import time
from openai import AsyncOpenAI

from services.llm.base import (LLMProvider, AIResponse, FeedbackResult,
                                ScenarioContext)
from services.llm.prompts import (SYSTEM_PROMPT_DIALOG, SYSTEM_PROMPT_FEEDBACK,
                                   SYSTEM_PROMPT_SENTIMENT, format_transcript)


class OpenAIProvider(LLMProvider):
    name = "openai_compatible"

    def __init__(self, base_url: str, api_key: str, model: str,
                 temperature: float = 0.7, timeout: float = 30.0):
        self.client = AsyncOpenAI(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
        )
        self.model = model
        self.temperature = temperature

    # ─── Генерация реплики в диалоге ────────────────────

    async def generate_reply(
        self,
        context: list[dict],
        scenario: ScenarioContext,
    ) -> AIResponse:
        start = time.time()

        # Собираем историю в формате OpenAI
        messages = [{"role": "system", "content": SYSTEM_PROMPT_DIALOG.format(
            title=scenario.title,
            description=scenario.description or "(без описания)",
            initial_prompt=scenario.initial_prompt,
            skill_name=scenario.skill_name,
            difficulty=scenario.difficulty,
        )}]
        for m in context:
            role = "user" if m.get("sender") == "user" else "assistant"
            messages.append({"role": role, "content": m.get("text", "")})

        # Если история пуста — просим AI начать диалог
        if len(messages) == 1:
            messages.append({
                "role": "user",
                "content": "Начни диалог первой репликой в роли своего персонажа.",
            })

        completion = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=250,
        )
        text = (completion.choices[0].message.content or "").strip()

        # Чистим кавычки по краям, если LLM их зачем-то поставил
        text = text.strip('"').strip("«»").strip()

        ms = int((time.time() - start) * 1000)
        return AIResponse(
            text=text or "...",
            sentiment_score=0.0,  # отдельно не анализируем здесь
            intent_category="neutral",
            response_time_ms=ms,
        )

    # ─── Итоговая оценка ────────────────────────────────

    async def generate_feedback(
        self,
        messages: list[dict],
        scenario: ScenarioContext,
    ) -> FeedbackResult:
        prompt = SYSTEM_PROMPT_FEEDBACK.format(
            title=scenario.title,
            description=scenario.description or "(без описания)",
            skill_name=scenario.skill_name,
            transcript=format_transcript(messages),
        )

        completion = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,  # низкая — для стабильности JSON
            max_tokens=600,
            # Просим JSON-режим, если провайдер его поддерживает
            response_format={"type": "json_object"},
        )
        raw = (completion.choices[0].message.content or "").strip()

        data = self._parse_json_strict(raw)
        return FeedbackResult(
            overall_score=float(data.get("overall_score", 50)),
            skill_scores={k: float(v) for k, v in (data.get("skill_scores") or {}).items()},
            feedback_text=str(data.get("feedback_text", "")).strip(),
            recommendations=str(data.get("recommendations", "")).strip(),
        )

    # ─── Анализ сентимента одного сообщения ─────────────

    async def analyze_sentiment(self, text: str) -> float:
        completion = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user",
                        "content": SYSTEM_PROMPT_SENTIMENT.format(text=text)}],
            temperature=0.0,
            max_tokens=10,
        )
        raw = (completion.choices[0].message.content or "").strip()
        # Ищем число в ответе
        m = re.search(r"-?\d+(?:\.\d+)?", raw)
        if not m:
            return 0.0
        try:
            v = float(m.group())
            return max(-1.0, min(1.0, v))
        except (ValueError, TypeError):
            return 0.0

    # ─── Парсинг JSON с устойчивостью к лишнему ─────────

    @staticmethod
    def _parse_json_strict(raw: str) -> dict:
        """Пытается извлечь JSON, даже если модель добавила ```json или текст вокруг."""
        # Убираем markdown-обёртку
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Ищем первый JSON-объект в тексте
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
        # Если ничего не получилось — возвращаем дефолт
        return {
            "overall_score": 50,
            "skill_scores": {},
            "feedback_text": "Не удалось проанализировать диалог автоматически.",
            "recommendations": "Попробуйте пройти сценарий ещё раз.",
        }
