"""
PaddleOCR adapter (fallback OCR engine per configuration).

Isolated for the same reason as the Surya adapter: paddleocr/paddlepaddle
are heavy dependencies that most local development setups will not want
installed by default.
"""

from __future__ import annotations

import asyncio
import io

from app.ocr.interfaces import OCRProvider


class PaddleOCRProvider(OCRProvider):
    name = "paddle"

    def __init__(self) -> None:
        try:
            import paddleocr  # noqa: F401
        except ImportError as exc:
            raise RuntimeError(
                "paddleocr is not installed. Run `uv pip install paddleocr paddlepaddle` "
                "or set ocr.provider to 'tesseract' in configs/base.yaml."
            ) from exc

    async def extract_text(self, image_bytes: bytes, languages: list[str]) -> str:
        return await asyncio.to_thread(self._extract_sync, image_bytes, languages)

    def _extract_sync(self, image_bytes: bytes, languages: list[str]) -> str:
        import numpy as np
        from PIL import Image
        from paddleocr import PaddleOCR

        lang = "en" if not languages else languages[0]
        ocr_engine = PaddleOCR(use_angle_cls=True, lang=lang, show_log=False)
        image = np.array(Image.open(io.BytesIO(image_bytes)).convert("RGB"))
        result = ocr_engine.ocr(image, cls=True)
        lines = [entry[1][0] for block in result for entry in block]
        return "\n".join(lines)
