"""
BM25 (sparse, lexical) retrieval.

Builds an in-memory BM25 index from every chunk currently stored in the
vector store. Rebuilding is cheap enough for small-to-medium corpora; for
very large corpora this should be replaced with a persistent BM25 index
(for example, backed by OpenSearch) behind the same Retriever interface.
"""

from __future__ import annotations

from rank_bm25 import BM25Okapi

from app.retrieval.interfaces import Retriever
from app.schemas.documents import SearchResult
from app.vector_db.interfaces import VectorStore


class BM25Retriever(Retriever):
    def __init__(self, vector_store: VectorStore) -> None:
        self._vector_store = vector_store
        self._index: BM25Okapi | None = None
        self._chunks = []

    async def refresh_index(self) -> None:
        self._chunks = await self._vector_store.fetch_all_texts()
        tokenized = [chunk.text.lower().split() for chunk in self._chunks]
        self._index = BM25Okapi(tokenized) if tokenized else None

    async def retrieve(self, query: str, top_k: int, filters: dict | None = None) -> list[SearchResult]:
        if self._index is None:
            await self.refresh_index()
        if self._index is None or not self._chunks:
            return []

        scores = self._index.get_scores(query.lower().split())
        ranked = sorted(zip(self._chunks, scores, strict=True), key=lambda pair: pair[1], reverse=True)

        results: list[SearchResult] = []
        for chunk, score in ranked[:top_k]:
            if filters and not all(
                getattr(chunk.metadata, key, None) == value for key, value in filters.items()
            ):
                continue
            results.append(SearchResult(chunk_id=chunk.chunk_id, text=chunk.text, score=float(score), metadata=chunk.metadata))
        return results
