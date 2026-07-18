"""PostgreSQL connection pool and schema bootstrap for document/session metadata.

The vector store (Qdrant) holds embeddings and chunk payloads; Postgres
holds structured, relational metadata (document registry, ingestion
audit log, API keys) that benefits from real transactions and SQL joins.
"""

from __future__ import annotations

import asyncpg

from app.core.config import Settings

_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    document_id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    chunk_count INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    details JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


async def create_pool(settings: Settings) -> asyncpg.Pool:
    pool = await asyncpg.create_pool(dsn=settings.database.postgres_dsn, min_size=1, max_size=10)
    async with pool.acquire() as connection:
        await connection.execute(_SCHEMA)
    return pool
