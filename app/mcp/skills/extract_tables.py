"""Extract Tables skill - pulls table elements out of an already-parsed document."""

from __future__ import annotations

from app.mcp.skills.base import Skill
from app.parsing.interfaces import DocumentParser


class ExtractTablesSkill(Skill):
    name = "extract_tables"
    description = "Extract structured table content from a document."

    def __init__(self, parser: DocumentParser) -> None:
        self._parser = parser

    async def run(self, file_path: str, document_id: str) -> list[dict]:
        parsed = await self._parser.parse(file_path, document_id)
        return [
            {"content": element.content, "page": element.page, "metadata": element.metadata}
            for element in parsed.elements
            if element.kind == "table"
        ]
