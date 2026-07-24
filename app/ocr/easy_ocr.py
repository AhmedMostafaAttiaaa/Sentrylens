"""
EasyOCR adapter - local, no API key, no Docker/GPU requirement (CPU works
fine for small workloads). Isolated for the same reason as Surya/Paddle:
easyocr pulls in a sizeable torch-based model download on first use, so
the heavy dependency is only imported if the user actually installs it
and selects this provider; otherwise OCRFactory falls back to Tesseract.
"""

from __future__ import annotations

import asyncio
import io

from app.ocr.interfaces import OCRProvider


class EasyOCRProvider(OCRProvider):
    name = "easyocr"

    def __init__(self) -> None:
        try:
            import easyocr  # noqa: F401
        except ImportError as exc:
            raise RuntimeError(
                "easyocr is not installed. Run `uv pip install easyocr` "
                "or set ocr.provider to 'tesseract' in configs/base.yaml."
            ) from exc
        self._reader = None

    @staticmethod
    def _to_easyocr_lang(code: str) -> str:
        # EasyOCR expects 2-letter codes; the project's default config uses
        # Tesseract-style 3-letter codes (e.g. "eng"), so map the common case.
        return "en" if code == "eng" else code

    def _get_reader(self, languages: list[str]):
        import easyocr

        if self._reader is None:
            codes = [self._to_easyocr_lang(c) for c in (languages or ["en"])]
            self._reader = easyocr.Reader(codes, gpu=False)
        return self._reader

    async def extract_text(self, image_bytes: bytes, languages: list[str]) -> str:
        return await asyncio.to_thread(self._extract_sync, image_bytes, languages)

    def _extract_sync(self, image_bytes: bytes, languages: list[str]) -> str:
        import numpy as np
        from PIL import Image

        reader = self._get_reader(languages)
        image = np.array(Image.open(io.BytesIO(image_bytes)).convert("RGB"))
        results = reader.readtext(image, detail=0)
        return "\n".join(results)
