"""
LLM Router.

Routes requests to the primary provider (local Ollama models by default),
with automatic retries, timeout handling and fallback to a secondary
provider (Groq) when the primary is unavailable or unhealthy. A lightweight
in-memory health cache avoids hitting the health endpoint on every request.
"""

from __future__ import annotations

import time
from collections.abc import AsyncIterator

import structlog
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import Settings
from app.llm.groq_provider import GroqProvider
from app.llm.interfaces import LLMProvider
from app.llm.ollama_provider import OllamaProvider

logger = structlog.get_logger(__name__)


class AllProvidersUnavailableError(RuntimeError):
    pass


class LLMRouter:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._primary: LLMProvider = OllamaProvider(
            base_url=settings.llm.ollama.base_url,
            default_model=settings.llm.ollama.models.get("default", "qwen3:8b"),
            timeout_seconds=settings.llm.router.request_timeout_seconds,
        )
        self._fallback: LLMProvider = GroqProvider(
            base_url=settings.llm.groq.base_url,
            api_key=settings.llm.groq.api_key,
            default_model=settings.llm.groq.model,
            timeout_seconds=settings.llm.router.request_timeout_seconds,
        )
        self._health_cache: dict[str, tuple[bool, float]] = {}

    def model_alias(self, alias: str) -> str | None:
        return self._settings.llm.ollama.models.get(alias)

    async def _healthy(self, provider: LLMProvider) -> bool:
        interval = self._settings.llm.router.health_check_interval_seconds
        cached = self._health_cache.get(provider.name)
        now = time.monotonic()
        if cached and now - cached[1] < interval:
            return cached[0]
        healthy = await provider.is_healthy()
        self._health_cache[provider.name] = (healthy, now)
        return healthy

    async def _select_provider(self) -> LLMProvider:
        if await self._healthy(self._primary):
            return self._primary
        logger.warning("primary_llm_unhealthy", provider=self._primary.name)
        if await self._healthy(self._fallback):
            return self._fallback
        raise AllProvidersUnavailableError("No healthy LLM provider available")

    async def complete(self, prompt: str, model_alias: str | None = None, **kwargs) -> tuple[str, str]:
        provider = await self._select_provider()
        model = self.model_alias(model_alias) if model_alias else None

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(self._settings.llm.router.max_retries + 1),
            wait=wait_exponential(multiplier=0.5, max=8),
            retry=retry_if_exception_type(Exception),
            reraise=True,
        ):
            with attempt:
                try:
                    result = await provider.complete(prompt, model=model, **kwargs)
                    return result, provider.name
                except Exception as exc:  # noqa: BLE001
                    logger.warning("llm_call_failed", provider=provider.name, error=str(exc))
                    if provider is self._primary:
                        self._health_cache[provider.name] = (False, time.monotonic())
                        if await self._healthy(self._fallback):
                            provider = self._fallback
                            continue
                    raise

        raise AllProvidersUnavailableError("Exhausted retries against all providers")

    async def stream(self, prompt: str, model_alias: str | None = None, **kwargs) -> AsyncIterator[tuple[str, str]]:
        provider = await self._select_provider()
        model = self.model_alias(model_alias) if model_alias else None
        try:
            async for token in provider.stream(prompt, model=model, **kwargs):
                yield token, provider.name
        except Exception as exc:  # noqa: BLE001
            logger.warning("llm_stream_failed", provider=provider.name, error=str(exc))
            if provider is self._primary and await self._healthy(self._fallback):
                async for token in self._fallback.stream(prompt, model=None, **kwargs):
                    yield token, self._fallback.name
            else:
                raise
