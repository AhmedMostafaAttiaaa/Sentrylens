"""Repository for document registry rows and ingestion audit entries in Postgres."""

from __future__ import annotations

import json

import asyncpg


class DocumentRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def register_document(self, document_id: str, filename: str, chunk_count: int, status: str) -> None:
        async with self._pool.acquire() as connection:
            await connection.execute(
                """
                INSERT INTO documents (document_id, filename, chunk_count, status)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (document_id) DO UPDATE
                SET chunk_count = EXCLUDED.chunk_count, status = EXCLUDED.status
                """,
                document_id,
                filename,
                chunk_count,
                status,
            )

    async def list_documents(self) -> list[dict]:
        async with self._pool.acquire() as connection:
            rows = await connection.fetch("SELECT * FROM documents ORDER BY created_at DESC")
            return [dict(row) for row in rows]

    async def record_audit(self, actor: str, action: str, details: dict) -> None:
        async with self._pool.acquire() as connection:
            await connection.execute(
                "INSERT INTO audit_log (actor, action, details) VALUES ($1, $2, $3)",
                actor,
                action,
                json.dumps(details),
            )
