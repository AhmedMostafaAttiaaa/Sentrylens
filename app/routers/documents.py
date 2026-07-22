"""Document ingestion and search endpoints."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from app.core.di import (
    get_document_parser,
    get_embedding_provider,
    get_ocr_provider,
    get_retriever,
    get_vector_store,
    get_vision_describer,
)
from app.core.config import get_settings
from app.schemas.documents import IngestionResult, SearchResponse, SearchResult
from app.services.ingestion_service import IngestionService

router = APIRouter(prefix="/documents", tags=["documents"])

_SUPPORTED_SUFFIXES = {".pdf", ".docx", ".pptx", ".xlsx", ".md", ".txt", ".html", ".htm"}


@router.post("/upload", response_model=IngestionResult)
async def upload_document(file: UploadFile = File(...)) -> IngestionResult:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in _SUPPORTED_SUFFIXES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix}")

    settings = get_settings()
    service = IngestionService(
        settings=settings,
        parser=get_document_parser(),
        vision_describer=get_vision_describer(),
        ocr_provider=get_ocr_provider(),
        embedding_provider=get_embedding_provider(),
        vector_store=get_vector_store(),
    )

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        result = await service.ingest_file(tmp_path, file.filename or "document")
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return result


@router.get("/search", response_model=SearchResponse)
async def search_documents(query: str = Query(..., min_length=1), top_k: int = Query(5, ge=1, le=50)) -> SearchResponse:
    retriever = get_retriever()
    results = await retriever.retrieve(query, top_k=top_k)
    return SearchResponse(
        query=query,
        results=[SearchResult(chunk_id=r.chunk_id, text=r.text, score=r.score, metadata=r.metadata) for r in results],
    )
