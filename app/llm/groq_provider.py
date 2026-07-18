"""Groq provider - OpenAI-compatible chat completions endpoint, used as fallback."""

from __future__ import annotations

from collections.abc import AsyncIterator

import httpx

from app.llm.interfaces import LLMProvider


class GroqProvider(LLMProvider):
    name = "groq"

    def __init__(self, base_url: str, api_key: str, default_model: str, timeout_seconds: int = 60) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._default_model = default_model
        self._timeout = timeout_seconds

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}

    async def complete(self, prompt: str, model: str | None = None, **kwargs) -> str:
        payload = {
            "model": model or self._default_model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._base_url}/chat/completions", json=payload, headers=self._headers()
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def stream(self, prompt: str, model: str | None = None, **kwargs) -> AsyncIterator[str]:
        payload = {
            "model": model or self._default_model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            async with client.stream(
                "POST", f"{self._base_url}/chat/completions", json=payload, headers=self._headers()
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data_str = line.removeprefix("data:").strip()
                    if data_str == "[DONE]":
                        break
                    import json as _json

                    chunk = _json.loads(data_str)
                    delta = chunk["choices"][0]["delta"].get("content")
                    if delta:
                        yield delta

    async def is_healthy(self) -> bool:
        if not self._api_key:
            return False
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self._base_url}/models", headers=self._headers())
                return response.status_code == 200
        except httpx.HTTPError:
            return False
