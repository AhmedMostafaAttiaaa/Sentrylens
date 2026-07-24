"""
Google Cloud Vision API OCR adapter - cloud, API-key based, no local model
weights or GPU needed. Good fit for deployments that would rather pay
per-request than host an OCR model. Requires a Vision API key (project
must have the Cloud Vision API enabled); read from GOOGLE_VISION_API_KEY
via settings the same way GeminiProvider reads its own key.
"""

from __future__ import annotations

import base64

import httpx

from app.ocr.interfaces import OCRProvider

_DEFAULT_BASE_URL = "https://vision.googleapis.com/v1"


class GoogleVisionOCRProvider(OCRProvider):
    name = "google_vision"

    def __init__(self, api_key: str, base_url: str = _DEFAULT_BASE_URL, timeout_seconds: int = 30) -> None:
        if not api_key:
            raise RuntimeError(
                "GoogleVisionOCRProvider requires an API key. Set GOOGLE_VISION_API_KEY "
                "or set ocr.provider to 'tesseract' in configs/base.yaml."
            )
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds

    async def extract_text(self, image_bytes: bytes, languages: list[str]) -> str:
        payload = {
            "requests": [
                {
                    "image": {"content": base64.b64encode(image_bytes).decode("ascii")},
                    "features": [{"type": "TEXT_DETECTION"}],
                    "imageContext": {"languageHints": languages} if languages else {},
                }
            ]
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._base_url}/images:annotate", params={"key": self._api_key}, json=payload
            )
            response.raise_for_status()
            data = response.json()
            annotations = data["responses"][0].get("textAnnotations", [])
            return annotations[0]["description"] if annotations else ""
