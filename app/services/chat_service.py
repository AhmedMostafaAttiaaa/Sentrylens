"""
Chat Service.

Thin orchestration layer between the FastAPI chat router and the LangGraph
Coordinator Agent graph. Responsible for loading conversation memory
before the graph runs and persisting the new turn afterward.
"""

from __future__ import annotations

from app.agents.graph import build_chat_graph
from app.core.config import Settings
from app.guardrails.pipeline import GuardrailsPipeline
from app.llm.router import LLMRouter
from app.memory.conversation_memory import ConversationMemory
from app.retrieval.interfaces import Retriever
from app.schemas.chat import ChatMessage, ChatRequest, ChatResponse, Citation


class ChatService:
    def __init__(
        self,
        settings: Settings,
        retriever: Retriever,
        llm_router: LLMRouter,
        guardrails: GuardrailsPipeline,
        memory: ConversationMemory,
    ) -> None:
        self._settings = settings
        self._memory = memory
        self._graph = build_chat_graph(settings, retriever, llm_router, guardrails)

    async def handle_message(self, request: ChatRequest) -> ChatResponse:
        history = await self._memory.get_history(request.session_id)

        state = {
            "session_id": request.session_id,
            "user_message": request.message,
            "conversation_history": [m.model_dump() for m in history],
        }
        result = await self._graph.ainvoke(state)

        await self._memory.append(request.session_id, ChatMessage(role="user", content=request.message))
        await self._memory.append(request.session_id, ChatMessage(role="assistant", content=result["answer"]))

        citations = [Citation(**c) for c in result.get("citations", [])]
        return ChatResponse(
            session_id=request.session_id,
            answer=result["answer"],
            citations=citations,
            used_provider=result.get("used_provider", "none"),
            guardrail_flags=result.get("guardrail_flags", []),
        )
