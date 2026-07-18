"""Tesseract-based OCR. Ships as the working default since it needs no GPU
and installs with a single apt package, making the project runnable
out of the box without downloading OCR-specific model weights."""

from __future__ import annotations

import asyncio
import io

from app.ocr.interfaces import OCRProvider


class TesseractOCRProvider(OCRProvider):
    name = "tesseract"

    async def extract_text(self, image_bytes: bytes, languages: list[str]) -> str:
        return await asyncio.to_thread(self._extract_sync, image_bytes, languages)

    def _extract_sync(self, image_bytes: bytes, languages: list[str]) -> str:
        import pytesseract
        from PIL import Image

        image = Image.open(io.BytesIO(image_bytes))
        lang_string = "+".join(languages) if languages else "eng"
        return pytesseract.image_to_string(image, lang=lang_string)
