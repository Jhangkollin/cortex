"""Redis client — async wrapper over redis-py."""

from __future__ import annotations

import json
from typing import Any

import structlog

from cortex_api.core.exceptions import CacheError


class RedisClient:
    """Thin async wrapper. JSON-encodes values; key namespacing is the caller's job."""

    def __init__(self, url: str, default_ttl: int = 300) -> None:
        self._logger = structlog.get_logger(__name__)
        self._url = url
        self._default_ttl = default_ttl
        self._client: Any = None  # populated lazily; type omitted to avoid hard import at scaffold time

    async def _ensure_client(self) -> Any:
        if self._client is None:
            # NOTE: lazy import keeps the scaffold importable without redis installed locally.
            from redis.asyncio import Redis

            self._client = Redis.from_url(self._url, decode_responses=True)
        return self._client

    async def get(self, key: str) -> Any | None:
        try:
            client = await self._ensure_client()
            raw = await client.get(key)
            return json.loads(raw) if raw is not None else None
        except Exception as e:
            self._logger.warning("redis_get_failed", key=key, error=str(e))
            raise CacheError(f"Redis GET failed for key={key}") from e

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        try:
            client = await self._ensure_client()
            await client.set(key, json.dumps(value), ex=ttl or self._default_ttl)
        except Exception as e:
            self._logger.warning("redis_set_failed", key=key, error=str(e))
            raise CacheError(f"Redis SET failed for key={key}") from e

    async def delete(self, key: str) -> None:
        try:
            client = await self._ensure_client()
            await client.delete(key)
        except Exception as e:
            self._logger.warning("redis_delete_failed", key=key, error=str(e))
            raise CacheError(f"Redis DEL failed for key={key}") from e

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
