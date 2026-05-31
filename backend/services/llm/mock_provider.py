"""Mock-провайдер. Работает как раньше — шаблонными ответами.

Используется либо явно (LLM_PROVIDER=mock), либо как fallback при ошибках
реального LLM — чтобы чат не ломался во время демонстрации."""
import random
import re
import time

from services.llm.base import (LLMProvider, AIResponse, FeedbackResult,
                                ScenarioContext)


# Подбор первой реплики по ключевому слову в промпте сценария
GREETINGS = {
    "критик": [
        "Добрый день! Вы хотели обсудить мою работу? Я вас слушаю.",
        "Здравствуйте. Понимаю, у вас ко мне вопросы по срокам. Слушаю.",
    ],
    "переговор": [
        "Здравствуйте! Нам давно пора поговорить. Я разочарован — задержка уже две недели.",
        "Алло, здравствуйте. Это невыносимо. Мы теряем деньги из-за ваших сроков.",
    ],
    "конфликт": [
        "Вот вы пришли — хорошо. У нас с Денисом категорически разные взгляды на проект.",
        "Добрый день. Мы хотели, чтобы вы нас рассудили.",
    ],
    "презентац": [
        "Прошу, у меня пять минут. Почему я должен вложиться в вашу автоматизацию?",
        "Слушаю. Только конкретно — цифры, эффект, сроки.",
    ],
    "стресс": [
        "Коллеги, я хочу вернуться к отчёту. Там серьёзные ошибки. Как это объясните?",
        "Цифры в вашем отчёте не бьются. Что скажете?",
    ],
    "default": [
        "Давайте начнём. Как вы видите ситуацию?",
        "Слушаю вас внимательно. С чего начнёте?",
    ],
}

POSITIVE_REPLIES = [
    "Хороший подход. Признание вклада — сильный ход. А что будем делать со сроками?",
    "Это правильно, вы показали эмпатию. Но какое решение вы предлагаете?",
    "Вижу, вы стараетесь понять мою позицию. Что конкретно изменится?",
    "Согласен, в этом есть смысл. Но меня волнуют гарантии. Что пообещаете?",
]

NEUTRAL_REPLIES = [
    "Хорошо, я услышал. Но пока не вижу, что конкретно изменится.",
    "Допустим. А если у меня другая точка зрения — как будете аргументировать?",
    "Понимаю. Но для меня важнее факты. Можете привести цифры?",
    "Ладно. А что скажут мои коллеги?",
]

CHALLENGING_REPLIES = [
    "Стоп. Вы говорите это, чтобы меня успокоить, или готовы что-то менять?",
    "Это звучит как формальная отписка. Я ожидал большего.",
    "Кажется, вы не до конца понимаете серьёзность ситуации.",
    "Меня не устраивает такой ответ. Попробуйте ещё раз, но без общих фраз.",
]


POSITIVE_WORDS = {"спасибо", "согласен", "понимаю", "хорошо", "давайте",
                   "предлагаю", "решение", "конечно", "правы", "признаю"}
NEGATIVE_WORDS = {"нет", "неправильно", "невозможно", "плохо", "против",
                   "всегда", "никогда", "бесполезно"}


def _classify(text: str) -> str:
    t = (text or "").lower()
    pos = sum(1 for w in POSITIVE_WORDS if w in t)
    neg = sum(1 for w in NEGATIVE_WORDS if w in t)
    if pos > neg: return "positive"
    if neg > pos: return "challenging"
    return "neutral"


class MockProvider(LLMProvider):
    name = "mock"

    async def generate_reply(
        self,
        context: list[dict],
        scenario: ScenarioContext,
    ) -> AIResponse:
        start = time.time()

        if not context:
            # Приветствие — подбираем по ключевому слову в промпте сценария
            prompt_lower = (scenario.initial_prompt or "").lower()
            pool = GREETINGS["default"]
            for key, options in GREETINGS.items():
                if key != "default" and key in prompt_lower:
                    pool = options
                    break
            text = random.choice(pool)
            category = "greeting"
        else:
            last_user = next(
                (m["text"] for m in reversed(context) if m.get("sender") == "user"),
                "",
            )
            category = _classify(last_user)
            pool = {
                "positive": POSITIVE_REPLIES,
                "neutral": NEUTRAL_REPLIES,
                "challenging": CHALLENGING_REPLIES,
            }[category]
            text = random.choice(pool)

        ms = int((time.time() - start) * 1000) + random.randint(200, 500)
        return AIResponse(
            text=text,
            sentiment_score={"positive": 0.5, "neutral": 0.1, "challenging": -0.3,
                              "greeting": 0.0}[category],
            intent_category=category,
            response_time_ms=ms,
        )

    async def generate_feedback(
        self,
        messages: list[dict],
        scenario: ScenarioContext,
    ) -> FeedbackResult:
        user_msgs = [m for m in messages if m.get("sender") == "user"]
        count = len(user_msgs)
        avg_len = sum(len(m.get("text", "")) for m in user_msgs) / max(count, 1)

        # Простая эвристика — чем длиннее и позитивнее ответы, тем выше балл
        score = min(40 + count * 8 + avg_len * 0.1, 95)
        all_text = " ".join(m.get("text", "").lower() for m in user_msgs)
        score += sum(2 for w in POSITIVE_WORDS if w in all_text)
        score -= sum(3 for w in NEGATIVE_WORDS if w in all_text)
        score = round(max(20, min(98, score + random.uniform(-3, 3))), 1)

        if score >= 75:
            text = ("Хорошая работа. Вы продемонстрировали активное слушание, "
                     "эмпатию и конструктивный подход.")
            rec = ("Обратите внимание на технику «Я-высказываний» "
                    "и практику перефразирования позиции оппонента.")
        elif score >= 50:
            text = ("Средний результат. Базовые навыки есть, но есть пространство "
                     "для роста в управлении эмоциями и структурировании аргументов.")
            rec = "Попробуйте пройти ещё несколько сценариев с фокусом на слабых зонах."
        else:
            text = ("Есть над чем поработать. Наблюдались сложности с эмпатией "
                     "и удержанием спокойного тона.")
            rec = "Начните с базового курса по активному слушанию."

        return FeedbackResult(
            overall_score=score,
            skill_scores={
                "Эмпатия":             round(max(20, min(98, score * random.uniform(0.85, 1.1))), 1),
                "Аргументация":        round(max(20, min(98, score * random.uniform(0.80, 1.05))), 1),
                "Управление эмоциями": round(max(20, min(98, score * random.uniform(0.80, 1.05))), 1),
                "Активное слушание":   round(max(20, min(98, score * random.uniform(0.85, 1.1))), 1),
            },
            feedback_text=text,
            recommendations=rec,
        )

    async def analyze_sentiment(self, text: str) -> float:
        base = {"positive": 0.6, "neutral": 0.1, "challenging": -0.3}
        return round(base[_classify(text)] + random.uniform(-0.2, 0.2), 2)
