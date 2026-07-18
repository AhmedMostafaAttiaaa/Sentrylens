from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas.documents import SearchResult


class Retriever(ABC):
    @abstractmethod
    async def retrieve(self, query: str, top_k: int, filters: dict | None = None) -> list[SearchResult]:
        """Return the top_k most relevant chunks for the query."""
