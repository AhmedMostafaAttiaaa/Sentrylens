"""
Parent-child chunking.

Large elements are kept as "parent" chunks for context, while smaller
"child" chunks (used for embedding and matching) are linked back to their
parent via parent_chunk_id in metadata. Retrieval matches on children for
precision, then the calling service can expand to the parent for a fuller
answer context.
"""

from __future__ import annotations

import uuid

from app.chunking.interfaces import ChunkingStrategy
from app.chunking.recursive import _split_text
from app.parsing.interfaces import ParsedDocument
from app.schemas.documents import Chunk, DocumentMetadata


class ParentChildChunkingStrategy(ChunkingStrategy):
    name = "parent_child"

    def __init__(self, parent_size: int = 2048, child_size: int = 400, overlap: int = 50) -> None:
        self._parent_size = parent_size
        self._child_size = child_size
        self._overlap = overlap

    def chunk(self, document: ParsedDocument) -> list[Chunk]:
        chunks: list[Chunk] = []
        for element in document.elements:
            parent_pieces = _split_text(element.content, self._parent_size, 0, ["\n\n", "\n"])
            for parent_text in parent_pieces:
                parent_id = str(uuid.uuid4())
                chunks.append(
                    Chunk(
                        chunk_id=parent_id,
                        text=parent_text.strip(),
                        metadata=DocumentMetadata(
                            document_id=document.document_id,
                            filename=document.filename,
                            page=element.page,
                            section=element.section,
                        ),
                    )
                )
                child_pieces = _split_text(parent_text, self._child_size, self._overlap, [". ", " "])
                for child_text in child_pieces:
                    if not child_text.strip():
                        continue
                    chunks.append(
                        Chunk(
                            chunk_id=str(uuid.uuid4()),
                            text=child_text.strip(),
                            metadata=DocumentMetadata(
                                document_id=document.document_id,
                                filename=document.filename,
                                page=element.page,
                                section=element.section,
                                parent_chunk_id=parent_id,
                            ),
                        )
                    )
        return chunks
