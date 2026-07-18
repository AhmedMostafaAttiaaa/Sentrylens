"""Recursive character/token chunking.

Splits on a priority list of separators (paragraphs, then lines, then
sentences, then words), recursing into oversized pieces until every chunk
fits within chunk_size, with chunk_overlap characters shared between
consecutive chunks to preserve context across boundaries.
"""

from __future__ import annotations

import uuid

from app.chunking.interfaces import ChunkingStrategy
from app.parsing.interfaces import ParsedDocument
from app.schemas.documents import Chunk, DocumentMetadata

_SEPARATORS = ["\n\n", "\n", ". ", " "]


def _split_text(text: str, chunk_size: int, overlap: int, separators: list[str]) -> list[str]:
    if len(text) <= chunk_size:
        return [text]

    if not separators:
        return [text[i : i + chunk_size] for i in range(0, len(text), max(chunk_size - overlap, 1))]

    separator, remaining_separators = separators[0], separators[1:]
    pieces = text.split(separator)

    chunks: list[str] = []
    current = ""
    for piece in pieces:
        candidate = current + separator + piece if current else piece
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current:
                chunks.append(current)
            if len(piece) > chunk_size:
                chunks.extend(_split_text(piece, chunk_size, overlap, remaining_separators))
                current = ""
            else:
                current = piece
    if current:
        chunks.append(current)

    if overlap > 0 and len(chunks) > 1:
        overlapped = [chunks[0]]
        for chunk in chunks[1:]:
            tail = overlapped[-1][-overlap:]
            overlapped.append(tail + chunk)
        return overlapped

    return chunks


class RecursiveChunkingStrategy(ChunkingStrategy):
    name = "recursive"

    def __init__(self, chunk_size: int = 1024, chunk_overlap: int = 128) -> None:
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def chunk(self, document: ParsedDocument) -> list[Chunk]:
        chunks: list[Chunk] = []
        for element in document.elements:
            pieces = _split_text(element.content, self._chunk_size, self._chunk_overlap, list(_SEPARATORS))
            for piece in pieces:
                if not piece.strip():
                    continue
                chunks.append(
                    Chunk(
                        chunk_id=str(uuid.uuid4()),
                        text=piece.strip(),
                        metadata=DocumentMetadata(
                            document_id=document.document_id,
                            filename=document.filename,
                            page=element.page,
                            section=element.section,
                        ),
                    )
                )
        return chunks
