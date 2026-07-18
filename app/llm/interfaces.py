"""Abstract contract every LLM provider must satisfy.

Keeping this interface small (complete + stream) means new providers
(Anthropic, OpenAI, vLLM, etc.) can be dropped in without touching the
router or any calling code.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator


class LLMProvider(ABC):
    name: str

    @abstractmethod
    async def complete(self, prompt: str, model: str | None = None, **kwargs) -> str:
        """Return a full completion for the given prompt."""

    @abstractmethod
    async def stream(self, prompt: str, model: str | None = None, **kwargs) -> AsyncIterator[str]:
        """Yield completion tokens/chunks as they are produced."""

    @abstractmethod
    async def is_healthy(self) -> bool:
        """Cheap health check used by the router before routing traffic here."""
