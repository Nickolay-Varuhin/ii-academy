"""Конфигурация приложения. Все настройки читаются из .env."""
import os
from pathlib import Path


def _load_dotenv():
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

_load_dotenv()


# ─── База данных ──────────────────────────────────────────
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/soft_skills",
)

# ─── JWT ──────────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "soft-skills-platform-secret-key-2026-CHANGE-ME")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "24"))

# ─── CORS ─────────────────────────────────────────────────
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# ─── Режим ────────────────────────────────────────────────
DEBUG = os.getenv("DEBUG", "true").lower() in ("1", "true", "yes")
SQL_ECHO = os.getenv("SQL_ECHO", "false").lower() in ("1", "true", "yes")

# ─── AI-имитация ──────────────────────────────────────────
AI_TYPING_SPEED_MS = int(os.getenv("AI_TYPING_SPEED_MS", "40"))
AI_THINKING_DELAY_MS = int(os.getenv("AI_THINKING_DELAY_MS", "700"))

# ─── LLM-провайдер ────────────────────────────────────────
# Варианты: mock | gigachat | openai | ollama
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mock").lower()

# OpenAI-совместимые провайдеры
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))

# Локальный Ollama
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

# GigaChat от Сбера
GIGACHAT_AUTH_KEY = os.getenv("GIGACHAT_AUTH_KEY", "")
GIGACHAT_SCOPE = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
GIGACHAT_MODEL = os.getenv("GIGACHAT_MODEL", "GigaChat")
GIGACHAT_VERIFY_SSL = os.getenv("GIGACHAT_VERIFY_SSL", "false").lower() in ("1", "true", "yes")
