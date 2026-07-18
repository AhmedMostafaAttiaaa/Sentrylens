from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas.documents import Chunk, SearchResult


class VectorStore(ABC):
    @abstractmethod
    async def ensure_collection(self) -> None:
        """Create the backing collection if it does not already exist."""

    @abstractmethod
    async def upsert_chunks(self, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        """Persist chunks and their embeddings."""

    @abstractmethod
    async def search(
        self, query_vector: list[float], top_k: int, filters: dict | None = None
    ) -> list[SearchResult]:
        """Dense vector search, optionally constrained by metadata filters."""

    @abstractmethod
    async def fetch_all_texts(self) -> list[Chunk]:
        """Return every stored chunk - used to (re)build the BM25 index."""
