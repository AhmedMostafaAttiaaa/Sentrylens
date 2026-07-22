"""
Dependency injection wiring.

This module builds the object graph once (per-process) and exposes small
FastAPI dependency functions so routers never construct services themselves.
Everything is built from Settings, so swapping an implementation is a
one-line config change, not a code change.
"""

from __future__ import annotations

from functools import lru_cache

from qdrant_client import AsyncQdrantClient
from redis.asyncio import Redis, from_url as redis_from_url

from app.core.config import get_settings
from app.embeddings.ollama_embeddings import OllamaEmbeddingProvider
from app.embeddings.interfaces import EmbeddingProvider
from app.guardrails.pipeline import GuardrailsPipeline
from app.llm.router import LLMRouter
from app.mcp.skills.base import SkillRegistry
from app.memory.conversation_memory import ConversationMemory
from app.ocr.factory import build_ocr_provider
from app.parsing.factory import build_document_parser
from app.reranker.cross_encoder_reranker import CrossEncoderReranker
from app.retrieval.hybrid_retriever import HybridRetriever
from app.vector_db.qdrant_store import QdrantVectorStore
from app.vision.ollama_vision import OllamaVisionDescriber


@lru_cache
def get_llm_router() -> LLMRouter:
    return LLMRouter(get_settings())


@lru_cache
def get_embedding_provider() -> EmbeddingProvider:
    return OllamaEmbeddingProvider(get_settings())


@lru_cache
def get_qdrant_client() -> AsyncQdrantClient:
    settings = get_settings()
    return AsyncQdrantClient(url=settings.vector_db.qdrant.url, api_key=settings.vector_db.qdrant.api_key or None)


@lru_cache
def get_vector_store() -> QdrantVectorStore:
    return QdrantVectorStore(get_settings(), get_qdrant_client())


@lru_cache
def get_reranker() -> CrossEncoderReranker:
    return CrossEncoderReranker(get_settings())


@lru_cache
def get_retriever() -> HybridRetriever:
    return HybridRetriever(
        settings=get_settings(),
        vector_store=get_vector_store(),
        embedding_provider=get_embedding_provider(),
        reranker=get_reranker(),
    )


@lru_cache
def get_document_parser():
    return build_document_parser(get_settings())


@lru_cache
def get_ocr_provider():
    return build_ocr_provider(get_settings())


@lru_cache
def get_vision_describer() -> OllamaVisionDescriber:
    return OllamaVisionDescriber(get_settings(), get_llm_router())


@lru_cache
def get_guardrails_pipeline() -> GuardrailsPipeline:
    return GuardrailsPipeline(get_settings())


@lru_cache
def get_skill_registry() -> SkillRegistry:
    from app.mcp.skills.search_documents import SearchDocumentsSkill
    from app.mcp.skills.summarize import SummarizeSkill
    from app.mcp.skills.translate import TranslateSkill
    from app.mcp.skills.calculator import CalculatorSkill

    registry = SkillRegistry()
    registry.register(SearchDocumentsSkill(get_retriever()))
    registry.register(SummarizeSkill(get_llm_router()))
    registry.register(TranslateSkill(get_llm_router()))
    registry.register(CalculatorSkill())
    return registry


@lru_cache
def get_redis_client() -> Redis:
    settings = get_settings()
    return redis_from_url(settings.database.redis_url, decode_responses=True)


@lru_cache
def get_conversation_memory() -> ConversationMemory:
    return ConversationMemory(get_settings(), get_redis_client())
