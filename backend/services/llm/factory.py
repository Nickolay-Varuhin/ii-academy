"""Фабрика LLM-провайдеров с понятными сообщениями об ошибках."""
import logging
from typing import Optional

from services.llm.base import LLMProvider
from services.llm.mock_provider import MockProvider

log = logging.getLogger("llm")


def _format_error(e: Exception) -> str:
    """Превращает исключение в полезное сообщение для лога."""
    name = type(e).__name__
    msg = str(e).strip()
    if not msg:
        msg = repr(e)
    return f"{name}: {msg}"


class FallbackProvider(LLMProvider):
    """Оборачивает основной провайдер и падает на MockProvider при ошибках."""

    name = "fallback"

    def __init__(self, primary: LLMProvider, backup: LLMProvider):
        self.primary = primary
        self.backup = backup

    async def generate_reply(self, context, scenario):
        try:
            return await self.primary.generate_reply(context, scenario)
        except Exception as e:
            log.warning("LLM (%s) failed на generate_reply: %s. Откат на mock.",
                         self.primary.name, _format_error(e))
            return await self.backup.generate_reply(context, scenario)

    async def generate_feedback(self, messages, scenario):
        try:
            return await self.primary.generate_feedback(messages, scenario)
        except Exception as e:
            log.warning("LLM (%s) failed на generate_feedback: %s. Откат на mock.",
                         self.primary.name, _format_error(e))
            return await self.backup.generate_feedback(messages, scenario)

    async def analyze_sentiment(self, text):
        try:
            return await self.primary.analyze_sentiment(text)
        except Exception:
            return await self.backup.analyze_sentiment(text)


_cached_provider: Optional[LLMProvider] = None


def get_llm_provider() -> LLMProvider:
    global _cached_provider
    if _cached_provider is not None:
        return _cached_provider

    from config import (LLM_PROVIDER, LLM_API_KEY, LLM_BASE_URL, LLM_MODEL,
                         LLM_TEMPERATURE, OLLAMA_BASE_URL, OLLAMA_MODEL,
                         GIGACHAT_AUTH_KEY, GIGACHAT_SCOPE, GIGACHAT_MODEL,
                         GIGACHAT_VERIFY_SSL)

    mock = MockProvider()

    if LLM_PROVIDER == "mock":
        log.info("LLM-провайдер: mock (шаблонные ответы)")
        _cached_provider = mock
        return mock

    if LLM_PROVIDER == "gigachat":
        if not GIGACHAT_AUTH_KEY:
            log.warning("LLM_PROVIDER=gigachat, но GIGACHAT_AUTH_KEY не указан. Использую mock.")
            _cached_provider = mock
            return mock
        from services.llm.gigachat_provider import GigaChatProvider
        primary = GigaChatProvider(
            authorization_key=GIGACHAT_AUTH_KEY,
            scope=GIGACHAT_SCOPE,
            model=GIGACHAT_MODEL,
            temperature=LLM_TEMPERATURE,
            verify_ssl=GIGACHAT_VERIFY_SSL,
        )
        log.info("LLM-провайдер: GigaChat (scope=%s, model=%s)",
                  GIGACHAT_SCOPE, GIGACHAT_MODEL)
        _cached_provider = FallbackProvider(primary, mock)
        return _cached_provider

    if LLM_PROVIDER == "openai":
        if not LLM_API_KEY:
            log.warning("LLM_PROVIDER=openai, но LLM_API_KEY не указан. Использую mock.")
            _cached_provider = mock
            return mock
        from services.llm.openai_provider import OpenAIProvider
        primary = OpenAIProvider(
            base_url=LLM_BASE_URL,
            api_key=LLM_API_KEY,
            model=LLM_MODEL,
            temperature=LLM_TEMPERATURE,
        )
        log.info("LLM-провайдер: openai-compatible (%s, model=%s)",
                  LLM_BASE_URL, LLM_MODEL)
        _cached_provider = FallbackProvider(primary, mock)
        return _cached_provider

    if LLM_PROVIDER == "ollama":
        from services.llm.ollama_provider import OllamaProvider
        primary = OllamaProvider(
            base_url=OLLAMA_BASE_URL,
            model=OLLAMA_MODEL,
            temperature=LLM_TEMPERATURE,
        )
        log.info("LLM-провайдер: ollama (%s, model=%s)",
                  OLLAMA_BASE_URL, OLLAMA_MODEL)
        _cached_provider = FallbackProvider(primary, mock)
        return _cached_provider

    log.warning("Неизвестный LLM_PROVIDER=%s. Использую mock.", LLM_PROVIDER)
    _cached_provider = mock
    return mock
