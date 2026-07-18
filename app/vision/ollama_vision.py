"""
Vision understanding via a vision-capable Ollama model (for example
qwen2.5-vl or gemma3 vision variants). Descriptions produced here are
appended to the document's text elements before chunking, so figures,
charts and tables become searchable through the same retrieval path as
regular text.
"""

from __future__ import annotations

import base64

import httpx

from app.core.config import Settings
from app.llm.router import LLMRouter
from app.vision.interfaces import VisionDescriber


class OllamaVisionDescriber(VisionDescriber):
    def __init__(self, settings: Settings, llm_router: LLMRouter) -> None:
        self._base_url = settings.llm.ollama.base_url.rstrip("/")
        self._model = settings.llm.ollama.vision_models.get("default", "qwen2.5-vl:7b")
        self._router = llm_router

    async def describe_image(self, image_bytes: bytes, context_hint: str = "") -> str:
        encoded = base64.b64encode(image_bytes).decode("utf-8")
        prompt = (
            "Describe this image factually for a document search index. "
            "If it is a chart or table, summarize the key data points and trend. "
            "Do not speculate beyond what is visible."
        )
        if context_hint:
            prompt += f" Context: {context_hint}"

        payload = {
            "model": self._model,
            "prompt": prompt,
            "images": [encoded],
            "stream": False,
        }
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(f"{self._base_url}/api/generate", json=payload)
            response.raise_for_status()
            return response.json().get("response", "").strip()
