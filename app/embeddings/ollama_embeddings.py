"""bge-m3 embeddings served locally through Ollama.

Kept behind the EmbeddingProvider interface so a different embedding
backend (OpenAI, a hosted API, a different local model) can be substituted
by editing configs/base.yaml only.
"""

from __future__ import annotations

import asyncio

import httpx

from app.core.config import Settings
from app.embeddings.interfaces import EmbeddingProvider


class OllamaEmbeddingProvider(EmbeddingProvider):
    def __init__(self, settings: Settings) -> None:
        self._base_url = settings.embeddings.ollama.base_url.rstrip("/")
        self._model = settings.embeddings.ollama.model
        self.dimension = settings.embeddings.ollama.dimension

    async def _embed_one(self, client: httpx.AsyncClient, text: str) -> list[float]:
        response = await client.post(
            f"{self._base_url}/api/embeddings",
            json={"model": self._model, "prompt": text},
        )
        response.raise_for_status()
        return response.json()["embedding"]

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        async with httpx.AsyncClient(timeout=60) as client:
            tasks = [self._embed_one(client, text) for text in texts]
            return await asyncio.gather(*tasks)
