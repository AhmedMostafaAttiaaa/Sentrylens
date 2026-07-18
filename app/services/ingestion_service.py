"""
Ingestion Agent / Vision Agent pipeline.

Coordinates the full document -> chunks -> embeddings -> vector store path:

  1. Parse the document (LlamaParse or local parser)
  2. For each figure/image element, run the Vision Agent (vision LLM) to
     produce a text description and fold it back in as a text element
  3. Chunk using the configured strategy
  4. Embed every chunk
  5. Upsert into the vector store
  6. Register the document + audit entry in Postgres
"""

from __future__ import annotations

import uuid

import structlog

from app.chunking.factory import build_chunking_strategy
from app.chunking.semantic import SemanticChunkingStrategy
from app.core.config import Settings
from app.embeddings.interfaces import EmbeddingProvider
from app.ocr.interfaces import OCRProvider
from app.parsing.interfaces import DocumentParser, ParsedElement
from app.repositories.document_repository import DocumentRepository
from app.schemas.documents import IngestionResult
from app.vector_db.interfaces import VectorStore
from app.vision.interfaces import VisionDescriber

logger = structlog.get_logger(__name__)


class IngestionService:
    def __init__(
        self,
        settings: Settings,
        parser: DocumentParser,
        vision_describer: VisionDescriber,
        ocr_provider: OCRProvider,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
        document_repository: DocumentRepository | None = None,
    ) -> None:
        self._settings = settings
        self._parser = parser
        self._vision = vision_describer
        self._ocr = ocr_provider
        self._embeddings = embedding_provider
        self._vector_store = vector_store
        self._document_repository = document_repository

    async def ingest_file(self, file_path: str, filename: str) -> IngestionResult:
        warnings: list[str] = []
        document_id = str(uuid.uuid4())

        parsed = await self._parser.parse(file_path, document_id)
        parsed.filename = filename

        if self._settings.vision.enabled and parsed.raw_images:
            for image_bytes in parsed.raw_images:
                try:
                    description = await self._vision.describe_image(image_bytes)
                    parsed.elements.append(ParsedElement(kind="figure", content=description))
                except Exception as exc:  # noqa: BLE001
                    warnings.append(f"vision_description_failed: {exc}")

        chunker = build_chunking_strategy(self._settings, self._embeddings)
        if isinstance(chunker, SemanticChunkingStrategy):
            chunks = await chunker.chunk_async(parsed)
        else:
            chunks = chunker.chunk(parsed)

        if not chunks:
            warnings.append("no_extractable_content")

        await self._vector_store.ensure_collection()

        if chunks:
            vectors = await self._embeddings.embed_texts([c.text for c in chunks])
            await self._vector_store.upsert_chunks(chunks, vectors)

        status = "indexed" if chunks else "empty"
        if self._document_repository is not None:
            await self._document_repository.register_document(document_id, filename, len(chunks), status)
            await self._document_repository.record_audit(
                actor="ingestion_service", action="ingest_document", details={"document_id": document_id, "filename": filename}
            )

        logger.info("document_ingested", document_id=document_id, filename=filename, chunk_count=len(chunks))

        return IngestionResult(
            document_id=document_id, filename=filename, chunk_count=len(chunks), status=status, warnings=warnings
        )
