"""
SQL Query skill.

Runs a strictly read-only query against the application's PostgreSQL
database (used for document/session metadata, not the vector store).
Only SELECT statements are permitted; anything else is rejected before
it reaches the database.
"""

from __future__ import annotations

import asyncpg

from app.mcp.skills.base import Skill


class SQLQuerySkill(Skill):
    name = "sql_query"
    description = "Run a read-only SQL SELECT query against the metadata database."

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    async def run(self, query: str) -> list[dict]:
        normalized = query.strip().lower()
        if not normalized.startswith("select"):
            raise ValueError("Only SELECT statements are permitted")

        connection = await asyncpg.connect(self._dsn)
        try:
            rows = await connection.fetch(query)
            return [dict(row) for row in rows]
        finally:
            await connection.close()
