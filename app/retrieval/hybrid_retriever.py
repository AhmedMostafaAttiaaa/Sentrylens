"""
Hybrid retriever.

Combines dense (embedding) and BM25 (lexical) retrieval with weighted
score fusion, then applies an optional context-compressing reranker on top
of the fused candidate set. Weights and top_k come from configuration so
the retrieval strategy can be tuned without code changes.
"""

from __future__ import annotations

from app.core.config import Settings
from app.embeddings.interfaces import EmbeddingProvider
from app.reranker.interfaces import Reranker
from app.retrieval.bm25_retriever import BM25Retriever
from app.retrieval.dense_retriever import DenseRetriever
from app.retrieval.interfaces import Retriever
from app.schemas.documents import SearchResult
from app.vector_db.interfaces import VectorStore


def _normalize(results: list[SearchResult]) -> dict[str, float]:
    if not results:
        return {}
    scores = [r.score for r in results]
    lo, hi = min(scores), max(scores)
    span = hi - lo or 1.0
    return {r.chunk_id: (r.score - lo) / span for r in results}


class HybridRetriever(Retriever):
    def __init__(
        self,
        settings: Settings,
        vector_store: VectorStore,
        embedding_provider: EmbeddingProvider,
        reranker: Reranker | None = None,
    ) -> None:
        self._settings = settings
        self._dense = DenseRetriever(vector_store, embedding_provider)
        self._bm25 = BM25Retriever(vector_store)
        self._reranker = reranker

    async def retrieve(self, query: str, top_k: int | None = None, filters: dict | None = None) -> list[SearchResult]:
        cfg = self._settings.retrieval
        k = top_k or cfg.top_k
        candidate_pool = max(k * 4, 20)

        mode = cfg.mode
        dense_results: list[SearchResult] = []
        bm25_results: list[SearchResult] = []

        if mode in {"dense", "hybrid"}:
            dense_results = await self._dense.retrieve(query, candidate_pool, filters)
        if mode in {"bm25", "hybrid"}:
            bm25_results = await self._bm25.retrieve(query, candidate_pool, filters)

        if mode == "dense":
            fused = dense_results
        elif mode == "bm25":
            fused = bm25_results
        else:
            fused = self._fuse(dense_results, bm25_results, cfg.dense_weight, cfg.bm25_weight)

        fused = fused[:candidate_pool]

        if cfg.rerank and self._reranker is not None and fused:
            fused = await self._reranker.rerank(query, fused, top_n=k)
        else:
            fused = fused[:k]

        return fused

    def _fuse(
        self,
        dense_results: list[SearchResult],
        bm25_results: list[SearchResult],
        dense_weight: float,
        bm25_weight: float,
    ) -> list[SearchResult]:
        dense_norm = _normalize(dense_results)
        bm25_norm = _normalize(bm25_results)

        by_id: dict[str, SearchResult] = {r.chunk_id: r for r in dense_results}
        for r in bm25_results:
            by_id.setdefault(r.chunk_id, r)

        fused_scores = {}
        for chunk_id in by_id:
            fused_scores[chunk_id] = (
                dense_weight * dense_norm.get(chunk_id, 0.0) + bm25_weight * bm25_norm.get(chunk_id, 0.0)
            )

        ordered_ids = sorted(fused_scores, key=lambda cid: fused_scores[cid], reverse=True)
        fused_results = []
        for chunk_id in ordered_ids:
            result = by_id[chunk_id]
            fused_results.append(result.model_copy(update={"score": fused_scores[chunk_id]}))
        return fused_results
