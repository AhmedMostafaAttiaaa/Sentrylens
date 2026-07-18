from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    document_id: str
    filename: str
    page: int | None = None
    section: str | None = None
    header: str | None = None
    language: str | None = None
    author: str | None = None
    created_at: datetime | None = None
    entities: list[str] = Field(default_factory=list)
    image_refs: list[str] = Field(default_factory=list)
    table_refs: list[str] = Field(default_factory=list)
    parent_chunk_id: str | None = None


class Chunk(BaseModel):
    chunk_id: str
    text: str
    metadata: DocumentMetadata


class IngestionResult(BaseModel):
    document_id: str
    filename: str
    chunk_count: int
    status: str
    warnings: list[str] = Field(default_factory=list)


class SearchResult(BaseModel):
    chunk_id: str
    text: str
    score: float
    metadata: DocumentMetadata


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
