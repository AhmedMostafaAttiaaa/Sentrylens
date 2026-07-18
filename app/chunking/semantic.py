"""
Semantic chunking.

Groups consecutive sentences together while their embedding similarity
stays above a threshold, splitting into a new chunk when the topic shifts.
This trades some indexing-time cost (one embedding call per sentence) for
chunks that are more topically coherent than fixed-size splitting.

Falls back to recursive chunking automatically if no embedding provider is
supplied, so the strategy still works in low-dependency environments.
"""

from __future__ import annotations

import re
import uuid

import numpy as np

from app.chunking.interfaces import ChunkingStrategy
from app.embeddings.interfaces import EmbeddingProvider
from app.parsing.interfaces import ParsedDocument
from app.schemas.documents import Chunk, DocumentMetadata

_SENTENCE_PATTERN = re.compile(r"(?<=[.!?])\s+")


def _cosine(a: list[float], b: list[float]) -> float:
    a_arr, b_arr = np.array(a), np.array(b)
    denom = np.linalg.norm(a_arr) * np.linalg.norm(b_arr)
    return float(np.dot(a_arr, b_arr) / denom) if denom else 0.0


class SemanticChunkingStrategy(ChunkingStrategy):
    name = "semantic"

    def __init__(self, embedding_provider: EmbeddingProvider | None, similarity_threshold: float = 0.55) -> None:
        self._embeddings = embedding_provider
        self._threshold = similarity_threshold

    async def chunk_async(self, document: ParsedDocument) -> list[Chunk]:
        if self._embeddings is None:
            from app.chunking.recursive import RecursiveChunkingStrategy

            return RecursiveChunkingStrategy().chunk(document)

        chunks: list[Chunk] = []
        for element in document.elements:
            sentences = [s.strip() for s in _SENTENCE_PATTERN.split(element.content) if s.strip()]
            if not sentences:
                continue
            vectors = await self._embeddings.embed_texts(sentences)

            groups: list[list[str]] = [[sentences[0]]]
            for i in range(1, len(sentences)):
                similarity = _cosine(vectors[i - 1], vectors[i])
                if similarity >= self._threshold:
                    groups[-1].append(sentences[i])
                else:
                    groups.append([sentences[i]])

            for group in groups:
                chunks.append(
                    Chunk(
                        chunk_id=str(uuid.uuid4()),
                        text=" ".join(group),
                        metadata=DocumentMetadata(
                            document_id=document.document_id,
                            filename=document.filename,
                            page=element.page,
                            section=element.section,
                        ),
                    )
                )
        return chunks

    def chunk(self, document: ParsedDocument) -> list[Chunk]:
        raise RuntimeError("SemanticChunkingStrategy requires async execution; call chunk_async instead")
