"""Search Documents skill - the MCP-exposed entry point into hybrid retrieval."""

from __future__ import annotations

from app.mcp.skills.base import Skill
from app.retrieval.interfaces import Retriever


class SearchDocumentsSkill(Skill):
    name = "search_documents"
    description = "Search indexed documents using hybrid dense + BM25 retrieval."

    def __init__(self, retriever: Retriever) -> None:
        self._retriever = retriever

    async def run(self, query: str, top_k: int = 5, filters: dict | None = None) -> list[dict]:
        results = await self._retriever.retrieve(query, top_k=top_k, filters=filters)
        return [
            {"chunk_id": r.chunk_id, "text": r.text, "score": r.score, "document_id": r.metadata.document_id}
            for r in results
        ]
