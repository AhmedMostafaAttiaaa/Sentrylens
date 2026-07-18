"""Translate skill - translates text to a target language via the LLM router."""

from __future__ import annotations

from app.llm.router import LLMRouter
from app.mcp.skills.base import Skill

_PROMPT_TEMPLATE = (
    "Translate the following text into {target_language}. "
    "Return only the translated text, nothing else.\n\nText:\n{text}"
)


class TranslateSkill(Skill):
    name = "translate"
    description = "Translate text into a target language."

    def __init__(self, llm_router: LLMRouter) -> None:
        self._router = llm_router

    async def run(self, text: str, target_language: str) -> dict:
        prompt = _PROMPT_TEMPLATE.format(target_language=target_language, text=text)
        translated, provider = await self._router.complete(prompt, model_alias="general")
        return {"translated_text": translated.strip(), "provider": provider}
