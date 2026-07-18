from __future__ import annotations

from abc import ABC, abstractmethod

from app.parsing.interfaces import ParsedDocument
from app.schemas.documents import Chunk


class ChunkingStrategy(ABC):
    name: str

    @abstractmethod
    def chunk(self, document: ParsedDocument) -> list[Chunk]:
        """Split a parsed document into indexable chunks."""
