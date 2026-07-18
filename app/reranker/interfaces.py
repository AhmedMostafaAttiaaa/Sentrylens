from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas.documents import SearchResult


class Reranker(ABC):
    @abstractmethod
    async def rerank(self, query: str, candidates: list[SearchResult], top_n: int) -> list[SearchResult]:
        """Re-order candidates by relevance to the query and return the top_n."""
