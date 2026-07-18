"""
Sentence-window chunking.

Each chunk is a single sentence, but its metadata carries the surrounding
window of sentences (before and after). At query time the retriever can
return the precise matching sentence while the window gives the LLM extra
context to reason over - improving both retrieval precision and answer
grounding.
"""

from __future__ import annotations

import re
import uuid

from app.chunking.interfaces import ChunkingStrategy
from app.parsing.interfaces import ParsedDocument
from app.schemas.documents import Chunk, DocumentMetadata

_SENTENCE_PATTERN = re.compile(r"(?<=[.!?])\s+")


class SentenceWindowChunkingStrategy(ChunkingStrategy):
    name = "sentence_window"

    def __init__(self, window_size: int = 3) -> None:
        self._window_size = window_size

    def chunk(self, document: ParsedDocument) -> list[Chunk]:
        chunks: list[Chunk] = []
        for element in document.elements:
            sentences = [s.strip() for s in _SENTENCE_PATTERN.split(element.content) if s.strip()]
            for index, sentence in enumerate(sentences):
                start = max(0, index - self._window_size)
                end = min(len(sentences), index + self._window_size + 1)
                window_text = " ".join(sentences[start:end])
                chunks.append(
                    Chunk(
                        chunk_id=str(uuid.uuid4()),
                        text=sentence,
                        metadata=DocumentMetadata(
                            document_id=document.document_id,
                            filename=document.filename,
                            page=element.page,
                            section=element.section,
                            entities=[],
                        ).model_copy(update={"header": window_text[:500]}),
                    )
                )
        return chunks
