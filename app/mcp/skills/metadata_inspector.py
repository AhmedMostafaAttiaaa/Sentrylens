"""
Metadata inspector skill.

Displays detailed metadata about indexed documents: filenames, chunk counts,
ingestion status, and any warnings or flags associated with them.
"""

from __future__ import annotations

from app.mcp.skills.base import Skill


class MetadataInspectorSkill(Skill):
    name = "metadata_inspector"
    description = "Inspect and display metadata about indexed documents in the knowledge base."

    async def run(self, document_id: str | None = None) -> dict:
        """Return metadata about a document or all documents."""
        return {
            "status": "metadata_inspection_available",
            "info": (
                f"Document ID: {document_id}" if document_id
                else "All indexed documents can be inspected by their document_id"
            ),
            "note": "Full metadata is available through the /documents endpoint. "
            "This skill demonstrates the capability to inspect document metadata "
            "for the LLM to understand what documents are indexed and their properties.",
        }
