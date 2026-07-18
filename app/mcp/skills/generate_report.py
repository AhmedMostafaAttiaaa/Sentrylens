"""Generate Report skill - turns retrieved context into a structured markdown report."""

from __future__ import annotations

from app.llm.router import LLMRouter
from app.mcp.skills.base import Skill
from app.retrieval.interfaces import Retriever

_REPORT_PROMPT = (
    "Write a structured markdown report answering the following topic, using only "
    "the provided context. Include section headings. Do not invent facts not present "
    "in the context.\n\nTopic: {topic}\n\nContext:\n{context}"
)


class GenerateReportSkill(Skill):
    name = "generate_report"
    description = "Generate a structured markdown report grounded in retrieved documents."

    def __init__(self, retriever: Retriever, llm_router: LLMRouter) -> None:
        self._retriever = retriever
        self._router = llm_router

    async def run(self, topic: str, top_k: int = 8) -> dict:
        results = await self._retriever.retrieve(topic, top_k=top_k)
        context = "\n\n".join(f"[{r.chunk_id}] {r.text}" for r in results)
        prompt = _REPORT_PROMPT.format(topic=topic, context=context)
        report, provider = await self._router.complete(prompt, model_alias="reasoning")
        return {"report": report.strip(), "provider": provider, "sources": [r.chunk_id for r in results]}
