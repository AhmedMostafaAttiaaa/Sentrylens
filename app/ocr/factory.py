"""Selects the configured OCR provider with graceful fallback to Tesseract."""

from __future__ import annotations

import os

import structlog

from app.core.config import Settings
from app.ocr.interfaces import OCRProvider
from app.ocr.tesseract_ocr import TesseractOCRProvider

logger = structlog.get_logger(__name__)


def build_ocr_provider(settings: Settings) -> OCRProvider:
    provider_name = settings.ocr.provider

    if provider_name == "surya":
        try:
            from app.ocr.surya_ocr import SuryaOCRProvider

            return SuryaOCRProvider()
        except Exception as exc:  # noqa: BLE001
            logger.warning("surya_ocr_unavailable_falling_back", error=str(exc))

    if provider_name == "paddle":
        try:
            from app.ocr.paddle_ocr import PaddleOCRProvider

            return PaddleOCRProvider()
        except Exception as exc:  # noqa: BLE001
            logger.warning("paddle_ocr_unavailable_falling_back", error=str(exc))

    if provider_name == "easyocr":
        try:
            from app.ocr.easy_ocr import EasyOCRProvider

            return EasyOCRProvider()
        except Exception as exc:  # noqa: BLE001
            logger.warning("easyocr_unavailable_falling_back", error=str(exc))

    if provider_name == "google_vision":
        try:
            from app.ocr.google_vision_ocr import GoogleVisionOCRProvider

            return GoogleVisionOCRProvider(api_key=os.environ.get("GOOGLE_VISION_API_KEY", ""))
        except Exception as exc:  # noqa: BLE001
            logger.warning("google_vision_ocr_unavailable_falling_back", error=str(exc))

    return TesseractOCRProvider()
