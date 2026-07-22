"""Gemini provider - Google's Generative Language API, usable as primary or fallback."""

from __future__ import annotations

import json as _json
from collections.abc import AsyncIterator

import httpx

from app.llm.interfaces import LLMProvider


class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(self, base_url: str, api_key: str, default_model: str, timeout_seconds: int = 60) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._default_model = default_model
        self._timeout = timeout_seconds

    def _url(self, model: str | None, method: str) -> str:
        return f"{self._base_url}/models/{model or self._default_model}:{method}"

    async def complete(self, prompt: str, model: str | None = None, **kwargs) -> str:
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                self._url(model, "generateContent"), params={"key": self._api_key}, json=payload
            )
            response.raise_for_status()
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    async def stream(self, prompt: str, model: str | None = None, **kwargs) -> AsyncIterator[str]:
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            async with client.stream(
                "POST",
                self._url(model, "streamGenerateContent"),
                params={"key": self._api_key, "alt": "sse"},
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    chunk = _json.loads(line.removeprefix("data:").strip())
                    parts = chunk["candidates"][0]["content"].get("parts", [])
                    for part in parts:
                        text = part.get("text")
                        if text:
                            yield text

    async def is_healthy(self) -> bool:
        if not self._api_key:
            return False
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self._base_url}/models", params={"key": self._api_key})
                return response.status_code == 200
        except httpx.HTTPError:
            return False
