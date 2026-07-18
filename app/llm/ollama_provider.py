"""Ollama provider - talks to a locally running Ollama daemon."""

from __future__ import annotations

from collections.abc import AsyncIterator

import httpx

from app.llm.interfaces import LLMProvider


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self, base_url: str, default_model: str, timeout_seconds: int = 60) -> None:
        self._base_url = base_url.rstrip("/")
        self._default_model = default_model
        self._timeout = timeout_seconds

    async def complete(self, prompt: str, model: str | None = None, **kwargs) -> str:
        payload = {
            "model": model or self._default_model,
            "prompt": prompt,
            "stream": False,
            "options": {k: v for k, v in kwargs.items() if k in {"temperature", "top_p", "num_ctx"}},
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(f"{self._base_url}/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")

    async def stream(self, prompt: str, model: str | None = None, **kwargs) -> AsyncIterator[str]:
        payload = {
            "model": model or self._default_model,
            "prompt": prompt,
            "stream": True,
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            async with client.stream("POST", f"{self._base_url}/api/generate", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    import json as _json

                    chunk = _json.loads(line)
                    token = chunk.get("response", "")
                    if token:
                        yield token
                    if chunk.get("done"):
                        break

    async def is_healthy(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self._base_url}/api/tags")
                return response.status_code == 200
        except httpx.HTTPError:
            return False
