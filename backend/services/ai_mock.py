"""Mock AI-тьютор — имитация ответов LLM.
Имеет краткосрочную «память» контекста диалога и эволюцию сложности
реплик по мере развития беседы."""
import random
import time
from dataclasses import dataclass


@dataclass
class AIResponse:
    text: str
    sentiment_score: float
    intent_category: str
    response_time_ms: int


@dataclass
class FeedbackResult:
    overall_score: float
    skill_scores: dict
    feedback_text: str
    recommendations: str


# Приветствия по сценариям (ключевое слово → вступление)
GREETINGS = {
    "критик": [
        "Добрый день! Вы хотели обсудить мою работу? Я вас слушаю.",
        "Здравствуйте. Понимаю, у вас ко мне вопросы по поводу сроков. Слушаю.",
    ],
    "переговор": [
        "Здравствуйте! Нам с вами давно надо поговорить. Я разочарован — задержка уже две недели. Что вы собираетесь делать?",
        "Алло, здравствуйте. Это невыносимо. Мы теряем деньги из-за ваших сроков.",
    ],
    "конфликт": [
        "Вот вы пришли — хорошо. У нас с Денисом категорически разные взгляды на проект. Так продолжаться не может.",
        "Добрый день. Мы хотели, чтобы вы нас рассудили. Каждый считает свой подход единственно правильным.",
    ],
    "презентац": [
        "Прошу, у меня пять минут. Убедите меня — почему я должен вложить бюджет в вашу автоматизацию?",
        "Слушаю вас. Только конкретно — цифры, эффект, сроки. Лирика мне не нужна.",
    ],
    "стресс": [
        "Коллеги, я хочу вернуться к отчёту, который только что показали. Там серьёзные ошибки. Как это объясните?",
        "Извините, но цифры в вашем отчёте не бьются. При всём уважении — это халатность. Что скажете?",
    ],
    "default": [
        "Давайте начнём. Как вы видите ситуацию?",
        "Слушаю вас внимательно. С чего начнёте?",
    ],
}

POSITIVE = [
    "Хороший подход. Признание вклада — всегда сильный ход. А что будем делать с конкретными сроками?",
    "Это правильно — вы показали эмпатию. Но я всё ещё не слышу, какое решение вы предлагаете.",
    "Вижу, вы стараетесь понять мою позицию. Давайте двигаться дальше — что конкретно изменится?",
    "Согласен, в этом есть здравое зерно. Но меня волнует другое — гарантии. Что вы можете пообещать?",
    "Это конструктивный тон, мне нравится. А теперь — ваши предложения по решению?",
]

NEUTRAL = [
    "Хорошо, я вас услышал. Но пока не вижу, что конкретно изменится.",
    "Допустим. А если я скажу, что у меня другая точка зрения — как вы будете аргументировать?",
    "Понимаю. Но для меня важнее факты, а не намерения. Можете привести цифры?",
    "Ладно. Давайте посмотрим с другой стороны — а что скажут мои коллеги?",
    "Интересно. Но это не решает главной проблемы. Что дальше?",
]

CHALLENGING = [
    "Стоп. Вы сейчас говорите это, чтобы меня успокоить, или реально готовы что-то менять?",
    "Знаете, это звучит как формальная отписка. Я ожидал большего.",
    "Мне кажется, вы не до конца понимаете серьёзность ситуации. Давайте ещё раз — что я получу в итоге?",
    "Меня не устраивает такой ответ. Попробуйте ещё раз — но без общих фраз.",
    "Вы повышаете голос — это плохая стратегия в переговорах. Давайте спокойнее.",
]

CLOSING = [
    "Хорошо, я готов обдумать ваше предложение. Зафиксируем итоги нашего разговора?",
    "Ладно, меня это более-менее устраивает. Давайте подытожим, о чём договорились.",
    "Окей. Я вижу, что вы серьёзно настроены. Резюмируем основные пункты?",
]


POSITIVE_KEYWORDS = {
    "спасибо", "согласен", "понимаю", "хорошо", "давайте",
    "предлагаю", "решение", "конечно", "вы правы", "верно",
    "действительно", "признаю", "извините",
}

NEGATIVE_KEYWORDS = {
    "нет", "неправильно", "отказ", "невозможно", "плохо",
    "против", "ужасно", "всегда", "никогда", "бесполезно",
}


def _classify(text: str) -> str:
    t = text.lower()
    p = sum(1 for w in POSITIVE_KEYWORDS if w in t)
    n = sum(1 for w in NEGATIVE_KEYWORDS if w in t)
    if p > n:
        return "positive"
    if n > p:
        return "challenging"
    return "neutral"


def calculate_sentiment(text: str) -> float:
    base = {"positive": 0.6, "neutral": 0.1, "challenging": -0.3}
    return round(base[_classify(text)] + random.uniform(-0.2, 0.2), 2)


def _pick_greeting(scenario_prompt: str) -> str:
    prompt_lower = scenario_prompt.lower() if scenario_prompt else ""
    for key, options in GREETINGS.items():
        if key != "default" and key in prompt_lower:
            return random.choice(options)
    return random.choice(GREETINGS["default"])


async def generate_response(context: list[dict], scenario_prompt: str) -> AIResponse:
    """Генерирует ответ AI на основе контекста диалога.

    context: [{"sender": "user"|"ai", "text": "..."}, ...]
    scenario_prompt: начальный промпт сценария (для выбора приветствия)
    """
    start = time.time()

    if not context:
        text = _pick_greeting(scenario_prompt)
        category = "greeting"
    else:
        last_user_msg = next(
            (m["text"] for m in reversed(context) if m["sender"] == "user"), ""
        )
        category = _classify(last_user_msg)
        user_turn_count = sum(1 for m in context if m["sender"] == "user")

        # На последних ходах — закрывающие реплики
        if user_turn_count >= 5 and category == "positive":
            text = random.choice(CLOSING)
        else:
            pool = {"positive": POSITIVE, "neutral": NEUTRAL, "challenging": CHALLENGING}
            text = random.choice(pool.get(category, NEUTRAL))

    ms = int((time.time() - start) * 1000) + random.randint(300, 900)
    return AIResponse(
        text=text,
        sentiment_score=random.uniform(0.1, 0.8),
        intent_category=category,
        response_time_ms=ms,
    )


async def generate_feedback(messages: list[dict], scenario_title: str) -> FeedbackResult:
    """Формирует итоговую оценку диалога."""
    user_msgs = [m for m in messages if m.get("sender") == "user"]
    count = len(user_msgs)
    avg_len = sum(len(m.get("text", "")) for m in user_msgs) / max(count, 1)

    # Базовая формула: больше реплик + развёрнутые ответы = выше балл
    score = min(40 + count * 8 + avg_len * 0.1, 95)
    # Учитываем позитивные / негативные формулировки
    all_text = " ".join(m.get("text", "").lower() for m in user_msgs)
    positive_words = sum(1 for w in POSITIVE_KEYWORDS if w in all_text)
    negative_words = sum(1 for w in NEGATIVE_KEYWORDS if w in all_text)
    score += positive_words * 2 - negative_words * 3
    score = round(max(20, min(98, score + random.uniform(-3, 3))), 1)

    if score >= 75:
        text = ("Отличная работа! Вы продемонстрировали хорошие навыки коммуникации: "
                "активное слушание, эмпатию и конструктивный подход.")
        rec = "Рекомендуем обратить внимание на технику «Я-высказываний» и практику перефразирования."
    elif score >= 50:
        text = ("Неплохой результат. Базовые навыки коммуникации есть, "
                "но остаётся пространство для роста в управлении эмоциями.")
        rec = "Советуем пройти дополнительные симуляции по управлению конфликтами."
    else:
        text = ("Есть над чем поработать. Наблюдались сложности с эмпатией "
                "и структурированием аргументов.")
        rec = "Рекомендуем начать с базового курса по активному слушанию."

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
