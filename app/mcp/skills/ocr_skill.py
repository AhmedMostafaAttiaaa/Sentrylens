"""OCR skill - exposes the configured OCR provider (Surya, PaddleOCR or
Tesseract fallback) as an MCP tool."""

from __future__ import annotations

import base64

from app.mcp.skills.base import Skill
from app.ocr.interfaces import OCRProvider


class OCRSkill(Skill):
    name = "ocr"
    description = "Extract text from an image using the configured OCR engine."

    def __init__(self, ocr_provider: OCRProvider, languages: list[str]) -> None:
        self._ocr = ocr_provider
        self._languages = languages

    async def run(self, image_base64: str) -> dict:
        image_bytes = base64.b64decode(image_base64)
        text = await self._ocr.extract_text(image_bytes, self._languages)
        return {"text": text, "provider": self._ocr.name}
