"""Vision Analysis skill - describes an image using the configured vision LLM."""

from __future__ import annotations

import base64

from app.mcp.skills.base import Skill
from app.vision.interfaces import VisionDescriber


class VisionAnalysisSkill(Skill):
    name = "vision_analysis"
    description = "Describe the contents of an image (figure, chart, table, photo)."

    def __init__(self, vision_describer: VisionDescriber) -> None:
        self._vision = vision_describer

    async def run(self, image_base64: str, context_hint: str = "") -> dict:
        image_bytes = base64.b64decode(image_base64)
        description = await self._vision.describe_image(image_bytes, context_hint)
        return {"description": description}
