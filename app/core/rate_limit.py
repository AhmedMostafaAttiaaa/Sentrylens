"""Simple sliding-window rate limiter backed by Redis."""

from __future__ import annotations

import time

from redis.asyncio import Redis


class RateLimiter:
    def __init__(self, redis_client: Redis, requests_per_minute: int) -> None:
        self._redis = redis_client
        self._limit = requests_per_minute

    async def check(self, identity: str) -> bool:
        key = f"rate_limit:{identity}:{int(time.time() // 60)}"
        current = await self._redis.incr(key)
        if current == 1:
            await self._redis.expire(key, 60)
        return current <= self._limit
