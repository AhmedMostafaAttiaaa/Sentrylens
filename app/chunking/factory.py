"""Selects the configured chunking strategy."""

from __future__ import annotations

from app.chunking.parent_child import ParentChildChunkingStrategy
from app.chunking.recursive import RecursiveChunkingStrategy
from app.chunking.sentence_window import SentenceWindowChunkingStrategy
from app.chunking.semantic import SemanticChunkingStrategy
from app.core.config import Settings
from app.embeddings.interfaces import EmbeddingProvider


def build_chunking_strategy(settings: Settings, embedding_provider: EmbeddingProvider | None = None):
    strategy = settings.chunking.strategy

    if strategy == "recursive":
        return RecursiveChunkingStrategy(settings.chunking.chunk_size, settings.chunking.chunk_overlap)
    if strategy == "sentence_window":
        return SentenceWindowChunkingStrategy(settings.chunking.sentence_window_size)
    if strategy == "parent_child":
        return ParentChildChunkingStrategy()
    if strategy == "semantic":
        return SemanticChunkingStrategy(embedding_provider)

    raise ValueError(f"Unknown chunking strategy: {strategy}")
