"""
Azure AI Vision (Read API) OCR adapter - cloud, API-key based.

The Read API is asynchronous: submit the image, then poll the returned
operation URL until it reports "succeeded" or "failed". Requires an Azure
Computer Vision resource endpoint + key, read from settings the same way
GeminiProvider/GoogleVisionOCRProvider read theirs.
"""

from __future__ import annotations

import asyncio

import httpx

from app.ocr.interfaces import OCRProvider

_READ_PATH = "/vision/v3.2/read/analyze"
_POLL_INTERVAL_SECONDS = 1.0
_MAX_POLL_ATTEMPTS = 30


class AzureVisionOCRProvider(OCRProvider):
    name = "azure_vision"

    def __init__(self, endpoint: str, api_key: str, timeout_seconds: int = 30) -> None:
        if not endpoint or not api_key:
            raise RuntimeError(
                "AzureVisionOCRProvider requires both an endpoint and an API key. Set "
                "AZURE_VISION_ENDPOINT and AZURE_VISION_KEY, or set ocr.provider to "
                "'tesseract' in configs/base.yaml."
            )
        self._endpoint = endpoint.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout_seconds

    def _headers(self) -> dict:
        return {"Ocp-Apim-Subscription-Key": self._api_key, "Content-Type": "application/octet-stream"}

    async def extract_text(self, image_bytes: bytes, languages: list[str]) -> str:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            submit = await client.post(f"{self._endpoint}{_READ_PATH}", content=image_bytes, headers=self._headers())
            submit.raise_for_status()
            operation_url = submit.headers["Operation-Location"]

            for _ in range(_MAX_POLL_ATTEMPTS):
                await asyncio.sleep(_POLL_INTERVAL_SECONDS)
                result = await client.get(operation_url, headers={"Ocp-Apim-Subscription-Key": self._api_key})
                result.raise_for_status()
                data = result.json()
                status = data.get("status")
                if status == "succeeded":
                    lines = [
                        line["text"]
                        for page in data["analyzeResult"]["readResults"]
                        for line in page["lines"]
                    ]
                    return "\n".join(lines)
                if status == "failed":
                    raise RuntimeError("Azure Vision Read API reported status=failed")

            raise TimeoutError("Azure Vision Read API did not complete in time")
