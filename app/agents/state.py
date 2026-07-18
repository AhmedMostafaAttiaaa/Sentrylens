"""Shared state passed between nodes in the LangGraph agent graph."""

from __future__ import annotations

from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    session_id: str
    user_message: str
    conversation_history: list[dict[str, str]]
    guardrail_flags: list[str]
    blocked: bool
    retrieved_chunks: list[dict[str, Any]]
    answer: str
    used_provider: str
    citations: list[dict[str, str]]
