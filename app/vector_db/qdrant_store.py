"""
Qdrant-backed vector store.

Wraps the async Qdrant client behind the VectorStore interface. Supports
metadata (payload) filters and stores the full chunk text plus metadata as
payload so results can be rendered without a second database round trip.
"""

from __future__ import annotations

import uuid

from qdrant_client import AsyncQdrantClient, models

from app.core.config import Settings
from app.schemas.documents import Chunk, DocumentMetadata, SearchResult
from app.vector_db.interfaces import VectorStore


class QdrantVectorStore(VectorStore):
    def __init__(self, settings: Settings, client: AsyncQdrantClient) -> None:
        self._client = client
        self._collection = settings.vector_db.qdrant.collection_name
        self._dimension = settings.embeddings.ollama.dimension
        distance_name = settings.vector_db.qdrant.distance.upper()
        self._distance = getattr(models.Distance, distance_name, models.Distance.COSINE)

    async def ensure_collection(self) -> None:
        exists = await self._client.collection_exists(self._collection)
        if not exists:
            await self._client.create_collection(
                collection_name=self._collection,
                vectors_config=models.VectorParams(size=self._dimension, distance=self._distance),
            )

    async def upsert_chunks(self, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        points = []
        for chunk, vector in zip(chunks, vectors, strict=True):
            payload = {"text": chunk.text, **chunk.metadata.model_dump(mode="json")}
            points.append(
                models.PointStruct(id=str(uuid.uuid4()), vector=vector, payload=payload)
            )
        if points:
            await self._client.upsert(collection_name=self._collection, points=points)

    def _build_filter(self, filters: dict | None) -> models.Filter | None:
        if not filters:
            return None
        conditions = [
            models.FieldCondition(key=key, match=models.MatchValue(value=value))
            for key, value in filters.items()
        ]
        return models.Filter(must=conditions)

    async def search(
        self, query_vector: list[float], top_k: int, filters: dict | None = None
    ) -> list[SearchResult]:
        response = await self._client.query_points(
            collection_name=self._collection,
            query=query_vector,
            limit=top_k,
            query_filter=self._build_filter(filters),
            with_payload=True,
        )
        results: list[SearchResult] = []
        for point in response.points:
            payload = dict(point.payload or {})
            text = payload.pop("text", "")
            metadata = DocumentMetadata.model_validate(payload)
            results.append(
                SearchResult(chunk_id=str(point.id), text=text, score=point.score, metadata=metadata)
            )
        return results

    async def fetch_all_texts(self) -> list[Chunk]:
        chunks: list[Chunk] = []
        next_offset = None
        while True:
            points, next_offset = await self._client.scroll(
                collection_name=self._collection, limit=256, offset=next_offset, with_payload=True
            )
            for point in points:
                payload = dict(point.payload or {})
                text = payload.pop("text", "")
                metadata = DocumentMetadata.model_validate(payload)
                chunks.append(Chunk(chunk_id=str(point.id), text=text, metadata=metadata))
            if next_offset is None:
                break
        return chunks
