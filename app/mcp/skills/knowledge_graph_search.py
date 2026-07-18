"""
Knowledge Graph Search skill.

Minimal in-memory entity relationship index built from document metadata
(the `entities` field populated during ingestion). This is intentionally
lightweight - it is a starting point for graph-style lookups, not a full
graph database. Swap in Neo4j or a similar store behind this same
interface for production-scale knowledge graphs.
"""

from __future__ import annotations

from collections import defaultdict

from app.mcp.skills.base import Skill
from app.vector_db.interfaces import VectorStore


class KnowledgeGraphSearchSkill(Skill):
    name = "knowledge_graph_search"
    description = "Find documents and chunks related to a given entity."

    def __init__(self, vector_store: VectorStore) -> None:
        self._vector_store = vector_store

    async def run(self, entity: str) -> list[dict]:
        chunks = await self._vector_store.fetch_all_texts()
        index: dict[str, list[str]] = defaultdict(list)
        for chunk in chunks:
            for candidate_entity in chunk.metadata.entities:
                index[candidate_entity.lower()].append(chunk.chunk_id)

        matching_ids = index.get(entity.lower(), [])
        by_id = {chunk.chunk_id: chunk for chunk in chunks}
        return [
            {"chunk_id": cid, "text": by_id[cid].text, "document_id": by_id[cid].metadata.document_id}
            for cid in matching_ids
            if cid in by_id
        ]
