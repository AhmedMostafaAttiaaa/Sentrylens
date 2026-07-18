"""
Cross-encoder reranker.

Loads a sentence-transformers CrossEncoder model lazily (only on first
use, and only if the optional `sentence-transformers` dependency is
installed) so the platform still starts up without it. Also documents
where BGE Reranker / Jina Reranker would plug in - both are also
cross-encoder style models and can be used simply by changing
reranker.model in configuration, since they share the same API shape
through sentence-transformers.
"""

from __future__ import annotations

import asyncio

import structlog

from app.core.config import Settings
from app.reranker.interfaces import Reranker
from app.schemas.documents import SearchResult

logger = structlog.get_logger(__name__)


class CrossEncoderReranker(Reranker):
    def __init__(self, settings: Settings) -> None:
        self._model_name = settings.reranker.model
        self._enabled = settings.reranker.provider != "none"
        self._model = None

    def _load_model(self):
        if self._model is not None:
            return self._model
        try:
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(self._model_name)
        except Exception as exc:  # noqa: BLE001
            logger.warning("reranker_model_unavailable", error=str(exc))
            self._model = False
        return self._model

    async def rerank(self, query: str, candidates: list[SearchResult], top_n: int) -> list[SearchResult]:
        if not self._enabled or not candidates:
            return candidates[:top_n]

        model = await asyncio.to_thread(self._load_model)
        if not model:
            return candidates[:top_n]

        pairs = [(query, candidate.text) for candidate in candidates]
        scores = await asyncio.to_thread(model.predict, pairs)

        reranked = sorted(zip(candidates, scores, strict=True), key=lambda pair: pair[1], reverse=True)
        return [candidate.model_copy(update={"score": float(score)}) for candidate, score in reranked[:top_n]]
