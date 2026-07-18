"""
Surya OCR adapter (primary OCR engine per configuration).

Surya gives strong layout-aware OCR (reading order, line/paragraph
detection) but pulls in a sizeable torch-based model download on first
use. The adapter is isolated here so the heavy dependency is only imported
if the user actually installs the `surya-ocr` package and selects this
provider; otherwise OCRFactory transparently falls back to Tesseract.
"""

from __future__ import annotations

import asyncio
import io

from app.ocr.interfaces import OCRProvider


class SuryaOCRProvider(OCRProvider):
    name = "surya"

    def __init__(self) -> None:
        try:
            import surya  # noqa: F401
        except ImportError as exc:
            raise RuntimeError(
                "surya-ocr is not installed. Run `uv pip install surya-ocr` "
                "or set ocr.provider to 'tesseract' in configs/base.yaml."
            ) from exc

    async def extract_text(self, image_bytes: bytes, languages: list[str]) -> str:
        return await asyncio.to_thread(self._extract_sync, image_bytes, languages)

    def _extract_sync(self, image_bytes: bytes, languages: list[str]) -> str:
        from PIL import Image
        from surya.ocr import run_ocr
        from surya.model.detection.model import load_model as load_det_model, load_processor as load_det_processor
        from surya.model.recognition.model import load_model as load_rec_model
        from surya.model.recognition.processor import load_processor as load_rec_processor

        image = Image.open(io.BytesIO(image_bytes))
        det_model, det_processor = load_det_model(), load_det_processor()
        rec_model, rec_processor = load_rec_model(), load_rec_processor()

        predictions = run_ocr(
            [image], [languages or ["en"]], det_model, det_processor, rec_model, rec_processor
        )
        lines = [line.text for page in predictions for line in page.text_lines]
        return "\n".join(lines)
