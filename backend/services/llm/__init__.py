"""Модуль интеграции с LLM-провайдерами.

Поддерживает любой OpenAI-совместимый API (OpenAI, Groq, OpenRouter, DeepSeek,
Together.ai, Mistral и др.) плюс локальный Ollama и моковый fallback.

Выбор провайдера — через переменную LLM_PROVIDER в .env."""
from services.llm.base import LLMProvider, AIResponse, FeedbackResult
from services.llm.factory import get_llm_provider

__all__ = ["LLMProvider", "AIResponse", "FeedbackResult", "get_llm_provider"]
