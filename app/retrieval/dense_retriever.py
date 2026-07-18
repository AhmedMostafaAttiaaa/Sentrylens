"""Dense (embedding similarity) retrieval against the vector store."""

from __future__ import annotations

from app.embeddings.interfaces import EmbeddingProvider
from app.retrieval.interfaces import Retriever
from app.schemas.documents import SearchResult
from app.vector_db.interfaces import VectorStore


class DenseRetriever(Retriever):
    def __init__(self, vector_store: VectorStore, embedding_provider: EmbeddingProvider) -> None:
        self._vector_store = vector_store
        self._embeddings = embedding_provider

    async def retrieve(self, query: str, top_k: int, filters: dict | None = None) -> list[SearchResult]:
        query_vector = await self._embeddings.embed_query(query)
        return await self._vector_store.search(query_vector, top_k, filters)
