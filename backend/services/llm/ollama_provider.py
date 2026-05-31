"""Провайдер локального Ollama (https://ollama.com).

Полностью бесплатный, работает оффлайн. Нужно установить Ollama и скачать модель:
  > ollama pull llama3.1:8b    (или qwen2.5:7b — лучше для русского)
  > ollama serve               (обычно запускается автоматически)

После этого в .env:
  LLM_PROVIDER=ollama
  OLLAMA_MODEL=llama3.1:8b"""
import json
import re
import time
import httpx

from services.llm.base import (LLMProvider, AIResponse, FeedbackResult,
                                ScenarioContext)
from services.llm.prompts import (SYSTEM_PROMPT_DIALOG, SYSTEM_PROMPT_FEEDBACK,
                                   SYSTEM_PROMPT_SENTIMENT, format_transcript)


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self, base_url: str = "http://localhost:11434",
                 model: str = "llama3.1:8b", temperature: float = 0.7,
                 timeout: float = 60.0):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.timeout = timeout

    async def _chat(self, messages: list[dict], json_mode: bool = False) -> str:
        """Отправляет запрос в Ollama /api/chat."""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": self.temperature},
        }
        if json_mode:
            payload["format"] = "json"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(f"{self.base_url}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
            return (data.get("message", {}).get("content") or "").strip()

    # ─── Генерация реплики ──────────────────────────────

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

        if len(messages) == 1:
            messages.append({
                "role": "user",
                "content": "Начни диалог первой репликой в роли своего персонажа.",
            })

        text = await self._chat(messages)
        text = text.strip('"').strip("«»").strip()
        ms = int((time.time() - start) * 1000)

        return AIResponse(
            text=text or "...",
            sentiment_score=0.0,
            intent_category="neutral",
            response_time_ms=ms,
        )

    # ─── Оценка ─────────────────────────────────────────

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
            json_mode=True,
        )
        data = self._parse_json(raw)
        return FeedbackResult(
            overall_score=float(data.get("overall_score", 50)),
            skill_scores={k: float(v) for k, v in (data.get("skill_scores") or {}).items()},
            feedback_text=str(data.get("feedback_text", "")).strip(),
            recommendations=str(data.get("recommendations", "")).strip(),
        )

    async def analyze_sentiment(self, text: str) -> float:
        raw = await self._chat(
            [{"role": "user",
              "content": SYSTEM_PROMPT_SENTIMENT.format(text=text)}],
        )
        m = re.search(r"-?\d+(?:\.\d+)?", raw)
        if not m:
            return 0.0
        try:
            return max(-1.0, min(1.0, float(m.group())))
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def _parse_json(raw: str) -> dict:
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
        return {"overall_score": 50, "skill_scores": {},
                 "feedback_text": "Не удалось проанализировать.",
                 "recommendations": ""}
