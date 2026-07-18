from __future__ import annotations

from abc import ABC, abstractmethod


class OCRProvider(ABC):
    name: str

    @abstractmethod
    async def extract_text(self, image_bytes: bytes, languages: list[str]) -> str:
        """Return the text found in an image."""
