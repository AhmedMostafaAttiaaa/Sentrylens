"""Summarize skill - condenses arbitrary text using the LLM router."""

from __future__ import annotations

from app.llm.router import LLMRouter
from app.mcp.skills.base import Skill

_PROMPT_TEMPLATE = (
    "Summarize the following text in {max_sentences} sentences or fewer. "
    "Be factual, do not add information that is not present in the text.\n\n"
    "Text:\n{text}"
)


class SummarizeSkill(Skill):
    name = "summarize"
    description = "Summarize a block of text into a small number of sentences."

    def __init__(self, llm_router: LLMRouter) -> None:
        self._router = llm_router

    async def run(self, text: str, max_sentences: int = 3) -> dict:
        prompt = _PROMPT_TEMPLATE.format(max_sentences=max_sentences, text=text)
        summary, provider = await self._router.complete(prompt, model_alias="general")
        return {"summary": summary.strip(), "provider": provider}
