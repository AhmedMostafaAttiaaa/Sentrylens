"""
Conversation memory backed by Redis.

Stores the last N turns of a chat session as a JSON list, keyed by
session_id. Redis gives cheap TTL-based expiry so stale sessions clean
themselves up automatically. Document memory (which chunks were surfaced
in a session) and user memory (long-lived preferences) follow the same
pattern and can be added as sibling classes here without touching callers.
"""

from __future__ import annotations

import json

from redis.asyncio import Redis

from app.core.config import Settings
from app.schemas.chat import ChatMessage

_SESSION_TTL_SECONDS = 60 * 60 * 24


class ConversationMemory:
    def __init__(self, settings: Settings, redis_client: Redis) -> None:
        self._redis = redis_client
        self._max_turns = settings.memory.max_turns

    def _key(self, session_id: str) -> str:
        return f"conversation:{session_id}"

    async def get_history(self, session_id: str) -> list[ChatMessage]:
        raw = await self._redis.get(self._key(session_id))
        if not raw:
            return []
        data = json.loads(raw)
        return [ChatMessage.model_validate(item) for item in data]

    async def append(self, session_id: str, message: ChatMessage) -> None:
        history = await self.get_history(session_id)
        history.append(message)
        history = history[-self._max_turns :]
        await self._redis.set(
            self._key(session_id),
            json.dumps([m.model_dump() for m in history]),
            ex=_SESSION_TTL_SECONDS,
        )

    async def clear(self, session_id: str) -> None:
        await self._redis.delete(self._key(session_id))
