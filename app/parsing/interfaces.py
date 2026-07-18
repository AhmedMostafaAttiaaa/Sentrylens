from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ParsedElement:
    """One structural unit extracted from a document: a paragraph, table,
    figure caption, heading, etc. Chunkers operate on lists of these."""

    kind: str  # text | heading | table | figure | caption | list
    content: str
    page: int | None = None
    section: str | None = None
    metadata: dict = field(default_factory=dict)


@dataclass
class ParsedDocument:
    document_id: str
    filename: str
    elements: list[ParsedElement]
    raw_images: list[bytes] = field(default_factory=list)


class DocumentParser(ABC):
    supported_extensions: set[str]

    @abstractmethod
    async def parse(self, file_path: str, document_id: str) -> ParsedDocument:
        """Parse a document on disk into structured elements."""
