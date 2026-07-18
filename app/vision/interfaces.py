from __future__ import annotations

from abc import ABC, abstractmethod


class VisionDescriber(ABC):
    @abstractmethod
    async def describe_image(self, image_bytes: bytes, context_hint: str = "") -> str:
        """Return a natural-language description of an image (figure, chart,
        table screenshot, photo) to be indexed alongside the surrounding text."""
