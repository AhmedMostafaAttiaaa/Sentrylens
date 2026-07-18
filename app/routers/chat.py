"""Chat endpoint - streaming and non-streaming, backed by the agent graph."""

from __future__ import annotations

import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.core.config import get_settings
from app.core.di import (
    get_conversation_memory,
    get_guardrails_pipeline,
    get_llm_router,
    get_retriever,
)
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


def _build_service() -> ChatService:
    return ChatService(
        settings=get_settings(),
        retriever=get_retriever(),
        llm_router=get_llm_router(),
        guardrails=get_guardrails_pipeline(),
        memory=get_conversation_memory(),
    )


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    service = _build_service()
    return await service.handle_message(request)


@router.post("/stream")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    service = _build_service()

    async def event_generator():
        response = await service.handle_message(request)
        for word in response.answer.split(" "):
            yield f"data: {json.dumps({'token': word + ' '})}\n\n"
        yield f"data: {json.dumps({'done': True, 'citations': [c.model_dump() for c in response.citations], 'used_provider': response.used_provider})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
