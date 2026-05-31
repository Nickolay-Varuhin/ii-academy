"""Провайдер GigaChat от Сбера.

GigaChat использует двухэтапную авторизацию:
  1. POST /api/v2/oauth с Basic-авторизацией (authorization_key)
     → получаем access_token, живёт 30 минут
  2. Обычные запросы к /api/v1/chat/completions с Bearer-авторизацией

Токен автоматически обновляется при истечении.

Для работы нужен:
  - Бесплатный аккаунт https://developers.sber.ru
  - Проект "GigaChat API" в личном кабинете Studio
  - Authorization Key (строка base64, одноразово генерируется в проекте)
"""
import base64
import json
import re
import ssl
import time
import uuid
from datetime import datetime
import httpx

from services.llm.base import (LLMProvider, AIResponse, FeedbackResult,
                                ScenarioContext)
from services.llm.prompts import (SYSTEM_PROMPT_DIALOG, SYSTEM_PROMPT_FEEDBACK,
                                   SYSTEM_PROMPT_SENTIMENT, LANGUAGE_REMINDER,
                                   format_transcript)


class GigaChatProvider(LLMProvider):
    name = "gigachat"

    # GigaChat возвращает сертификат, подписанный российским Минцифры.
    # Python по умолчанию его не знает и ругается SSL: CERTIFICATE_VERIFY_FAILED.
    # Для курсового проще всего отключить проверку сертификата (в production
    # так делать нельзя, но для обучения — допустимо).
    OAUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    API_URL = "https://gigachat.devices.sberbank.ru/api/v1"

    def __init__(self, authorization_key: str, scope: str = "GIGACHAT_API_PERS",
                 model: str = "GigaChat", temperature: float = 0.7,
                 timeout: float = 30.0, verify_ssl: bool = False):
        self.authorization_key = authorization_key
        self.scope = scope
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        self.verify_ssl = verify_ssl

        # Кэш токена
        self._access_token: str | None = None
        self._token_expires_at: float = 0.0

    # ─── Получение и обновление access_token ────────────

    async def _get_access_token(self) -> str:
        """Обменивает authorization_key на временный access_token (30 мин).
        Кэширует токен до истечения срока."""
        now = time.time()
        # Обновляем за 60 сек до истечения, чтобы не попасть в гонку
        if self._access_token and now < self._token_expires_at - 60:
            return self._access_token

        headers = {
            "Authorization": f"Basic {self.authorization_key}",
            "RqUID": str(uuid.uuid4()),
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }
        data = {"scope": self.scope}

        async with httpx.AsyncClient(
            timeout=self.timeout,
            verify=self.verify_ssl,
        ) as client:
            resp = await client.post(self.OAUTH_URL, headers=headers, data=data)
            resp.raise_for_status()
            payload = resp.json()

        self._access_token = payload["access_token"]
        # expires_at в миллисекундах unix-времени
        expires_ms = payload.get("expires_at", 0)
        self._token_expires_at = (expires_ms / 1000
                                    if expires_ms > 10**10
                                    else now + 30 * 60)
        return self._access_token

    # ─── Низкоуровневый chat-запрос ─────────────────────

    async def _chat(self, messages: list[dict], temperature: float | None = None,
                      max_tokens: int = 512) -> str:
        token = await self._get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        async with httpx.AsyncClient(
            timeout=self.timeout,
            verify=self.verify_ssl,
        ) as client:
            resp = await client.post(
                f"{self.API_URL}/chat/completions",
                headers=headers,
                json=payload,
            )
            # Если токен истёк — пробуем обновить и повторить один раз
            if resp.status_code == 401:
                self._access_token = None
                token = await self._get_access_token()
                headers["Authorization"] = f"Bearer {token}"
                resp = await client.post(
                    f"{self.API_URL}/chat/completions",
                    headers=headers,
                    json=payload,
                )
            resp.raise_for_status()
            data = resp.json()

        return (data["choices"][0]["message"]["content"] or "").strip()

    # ─── Генерация реплики в диалоге ────────────────────

    async def generate_reply(
        self,
        context: list[dict],
        scenario: ScenarioContext,
    ) -> AIResponse:
        start = time.time()

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

        # Подстраховка от дрейфа на английский
        if messages and messages[-1]["role"] == "user":
            messages[-1] = {
                "role": "user",
                "content": messages[-1]["content"] + LANGUAGE_REMINDER,
            }
        elif len(messages) == 1:
            messages.append({
                "role": "user",
                "content": ("Начни диалог первой репликой в роли своего персонажа."
                            + LANGUAGE_REMINDER),
            })

        text = await self._chat(messages, max_tokens=300)
        text = text.strip('"').strip("«»").strip()

        ms = int((time.time() - start) * 1000)
        return AIResponse(
            text=text or "...",
            sentiment_score=0.0,
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
        raw = await self._chat(
            [{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=700,
        )

        data = self._parse_json(raw)
        return FeedbackResult(
            overall_score=float(data.get("overall_score", 50)),
            skill_scores={k: float(v) for k, v in (data.get("skill_scores") or {}).items()},
            feedback_text=str(data.get("feedback_text", "")).strip(),
            recommendations=str(data.get("recommendations", "")).strip(),
        )

    # ─── Анализ тональности отдельного сообщения ────────

    async def analyze_sentiment(self, text: str) -> float:
        raw = await self._chat(
            [{"role": "user",
              "content": SYSTEM_PROMPT_SENTIMENT.format(text=text)}],
            temperature=0.0,
            max_tokens=10,
        )
        m = re.search(r"-?\d+(?:\.\d+)?", raw)
        if not m:
            return 0.0
        try:
            return max(-1.0, min(1.0, float(m.group())))
        except (ValueError, TypeError):
            return 0.0

    # ─── Парсинг JSON устойчивый к лишнему тексту ───────

    @staticmethod
    def _parse_json(raw: str) -> dict:
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "",
                          raw.strip(), flags=re.MULTILINE)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
        return {
            "overall_score": 50,
            "skill_scores": {},
            "feedback_text": "Не удалось проанализировать диалог автоматически.",
            "recommendations": "Попробуйте пройти сценарий ещё раз.",
        }
