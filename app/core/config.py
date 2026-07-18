"""
Central configuration loader.

Configuration is layered: base.yaml is loaded first, then the file matching
APP_ENV (development / staging / production) is merged on top of it. Any
"${VAR_NAME}" placeholder found in the YAML is resolved against process
environment variables (and .env, loaded via python-dotenv-style parsing).

The result is validated into a typed Settings object so the rest of the
codebase never touches raw dicts.
"""

from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

CONFIG_DIR = Path(__file__).resolve().parents[2] / "configs"
ENV_VAR_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)\}")


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def _resolve_env(value: Any) -> Any:
    if isinstance(value, str):
        def _sub(match: re.Match) -> str:
            var_name = match.group(1)
            return os.environ.get(var_name, "")
        return ENV_VAR_PATTERN.sub(_sub, value)
    if isinstance(value, dict):
        return {k: _resolve_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_env(v) for v in value]
    return value


def _deep_merge(base: dict, override: dict) -> dict:
    merged = dict(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


class RouterConfig(BaseModel):
    primary_provider: str = "ollama"
    fallback_provider: str = "groq"
    request_timeout_seconds: int = 60
    max_retries: int = 2
    health_check_interval_seconds: int = 30


class OllamaLLMConfig(BaseModel):
    base_url: str
    models: dict[str, str] = Field(default_factory=dict)
    vision_models: dict[str, str] = Field(default_factory=dict)


class GroqConfig(BaseModel):
    base_url: str
    api_key: str = ""
    model: str = "llama-3.3-70b-versatile"


class LLMConfig(BaseModel):
    router: RouterConfig
    ollama: OllamaLLMConfig
    groq: GroqConfig


class OllamaEmbeddingConfig(BaseModel):
    base_url: str
    model: str = "bge-m3"
    dimension: int = 1024


class EmbeddingsConfig(BaseModel):
    provider: str = "ollama"
    ollama: OllamaEmbeddingConfig


class LlamaParseConfig(BaseModel):
    api_key: str = ""
    result_type: str = "markdown"


class ParsingConfig(BaseModel):
    provider: str = "local"
    llamaparse: LlamaParseConfig


class OCRConfig(BaseModel):
    provider: str = "tesseract"
    fallback_provider: str = "tesseract"
    languages: list[str] = Field(default_factory=lambda: ["eng"])


class VisionConfig(BaseModel):
    enabled: bool = True
    provider: str = "ollama"
    describe_figures: bool = True
    describe_tables: bool = True


class ChunkingConfig(BaseModel):
    strategy: str = "recursive"
    chunk_size: int = 1024
    chunk_overlap: int = 128
    sentence_window_size: int = 3


class QdrantConfig(BaseModel):
    url: str
    api_key: str = ""
    collection_name: str = "vision_rag_documents"
    distance: str = "cosine"


class VectorDBConfig(BaseModel):
    provider: str = "qdrant"
    qdrant: QdrantConfig


class RetrievalConfig(BaseModel):
    mode: str = "hybrid"
    top_k: int = 8
    dense_weight: float = 0.6
    bm25_weight: float = 0.4
    rerank: bool = True


class RerankerConfig(BaseModel):
    provider: str = "cross_encoder"
    model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    top_n: int = 5


class GuardrailsConfig(BaseModel):
    input_validation: bool = True
    output_validation: bool = True
    prompt_injection_detection: bool = True
    pii_detection: bool = True
    secrets_detection: bool = True
    toxicity_detection: bool = True
    hallucination_check: bool = True
    citation_validation: bool = True
    max_input_chars: int = 8000


class SecurityConfig(BaseModel):
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    rate_limit_per_minute: int = 60


class MemoryConfig(BaseModel):
    conversation_backend: str = "redis"
    max_turns: int = 20


class DatabaseConfig(BaseModel):
    postgres_dsn: str
    redis_url: str


class LangfuseConfig(BaseModel):
    public_key: str = ""
    secret_key: str = ""
    host: str = ""


class ObservabilityConfig(BaseModel):
    structured_logging: bool = True
    tracing_enabled: bool = False
    langfuse: LangfuseConfig = Field(default_factory=LangfuseConfig)


class AppMeta(BaseModel):
    name: str = "Enterprise Vision RAG"
    version: str = "0.1.0"
    debug: bool = False


class Settings(BaseModel):
    app: AppMeta
    llm: LLMConfig
    embeddings: EmbeddingsConfig
    parsing: ParsingConfig
    ocr: OCRConfig
    vision: VisionConfig
    chunking: ChunkingConfig
    vector_db: VectorDBConfig
    retrieval: RetrievalConfig
    reranker: RerankerConfig
    guardrails: GuardrailsConfig
    security: SecurityConfig
    memory: MemoryConfig
    database: DatabaseConfig
    observability: ObservabilityConfig
    environment: str = "development"


@lru_cache
def get_settings() -> Settings:
    _load_dotenv(CONFIG_DIR.parent / ".env")

    env = os.environ.get("APP_ENV", "development").lower()

    base = _load_yaml(CONFIG_DIR / "base.yaml")
    overlay = _load_yaml(CONFIG_DIR / f"{env}.yaml")
    merged = _deep_merge(base, overlay)
    resolved = _resolve_env(merged)
    resolved["environment"] = env

    return Settings.model_validate(resolved)
