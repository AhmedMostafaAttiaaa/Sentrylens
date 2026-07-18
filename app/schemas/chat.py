from __future__ import annotations

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    session_id: str
    message: str
    top_k: int | None = None


class Citation(BaseModel):
    chunk_id: str
    document_id: str
    snippet: str


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    used_provider: str
    guardrail_flags: list[str] = Field(default_factory=list)
