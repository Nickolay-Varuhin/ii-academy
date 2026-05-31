"""Абстрактный интерфейс LLM-провайдера.

Любая реализация должна уметь:
  - generate_reply(context, scenario) — сгенерировать ответ в роли персонажа
  - generate_feedback(messages, scenario) — проанализировать диалог и выставить оценки
  - analyze_sentiment(text) — оценить тональность сообщения пользователя"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class AIResponse:
    """Ответ AI в диалоге."""
    text: str
    sentiment_score: float  # -1.0..1.0
    intent_category: str    # "positive"|"neutral"|"challenging"|"greeting"
    response_time_ms: int


@dataclass
class FeedbackResult:
    """Итоговая оценка всего диалога."""
    overall_score: float              # 0..100
    skill_scores: dict                # {"Эмпатия": 78, ...}
    feedback_text: str                # Текстовая обратная связь
    recommendations: str              # Конкретные рекомендации


@dataclass
class ScenarioContext:
    """Контекст сценария — передаётся в каждый запрос."""
    title: str
    description: Optional[str]
    initial_prompt: str
    skill_name: str
    difficulty: int  # 1..5
    max_turns: int


class LLMProvider(ABC):
    """Абстрактный провайдер LLM. Реализации — в отдельных файлах."""

    # Краткое имя провайдера для логов
    name: str = "abstract"

    @abstractmethod
    async def generate_reply(
        self,
        context: list[dict],
        scenario: ScenarioContext,
    ) -> AIResponse:
        """Сгенерировать ответ AI.
        context — история диалога в формате [{"sender": "user|ai", "text": "..."}]"""
        ...

    @abstractmethod
    async def generate_feedback(
        self,
        messages: list[dict],
        scenario: ScenarioContext,
    ) -> FeedbackResult:
        """Оценить весь диалог и выставить баллы."""
        ...

    @abstractmethod
    async def analyze_sentiment(self, text: str) -> float:
        """Оценить тональность отдельного сообщения (-1.0 .. 1.0)."""
        ...
