"""Extract Images skill - returns the raw images embedded in a parsed document."""

from __future__ import annotations

import base64

from app.mcp.skills.base import Skill
from app.parsing.interfaces import DocumentParser


class ExtractImagesSkill(Skill):
    name = "extract_images"
    description = "Extract embedded images from a document as base64 payloads."

    def __init__(self, parser: DocumentParser) -> None:
        self._parser = parser

    async def run(self, file_path: str, document_id: str) -> list[str]:
        parsed = await self._parser.parse(file_path, document_id)
        return [base64.b64encode(image_bytes).decode("utf-8") for image_bytes in parsed.raw_images]
