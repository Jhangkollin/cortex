"""Redis-backed cache for the F2 eligible-brands API.

Cache shape:
  key = ``eligible_brands:{publisher_uuid}:{lang}``
  value = JSON-encoded list of EligibleBrandDTO dicts
  TTL = 300s (5 min, matches AD3)

Invalidation is write-through from BrandPlacementComposer on every successful
compose. SCAN + DEL is bounded by the number of distinct (publisher, lang)
scope rows for the brand (single-digit at MVP).

Failure mode: Redis-down on get → return None (degrades to cache miss, caller
hits DB). Redis-down on invalidate → log + swallow (compose still succeeds;
F2 serves stale for up to 300s).
"""

from __future__ import annotations

import json
from typing import Any, Protocol, cast
from uuid import UUID

import structlog

_LOG = structlog.get_logger(__name__)

_KEY_PREFIX = "eligible_brands"
_TTL_SECONDS = 300


class _KeyValueStore(Protocol):
    """Narrow port the cache depends on (3 methods).

    Decoupling from the concrete ``redis.asyncio.Redis`` class lets the cache
    be exercised against any KV substitute (in-memory fake, alternate driver)
    without committing test substitutes to the full Redis surface.

    Return types are ``Any`` so the protocol structurally accepts the
    ``redis.asyncio.Redis`` class (whose return types are declared
    ``Awaitable[Any] | Any`` due to sync/async overload). Callers await and
    treat the values as the narrower types the methods document below.
    """

    def get(self, key: str) -> Any:
        """Awaitable; resolves to ``bytes | str | None``."""

    def setex(self, key: str, ttl: int, value: str) -> Any:
        """Awaitable; return value is unused."""

    def delete(self, *keys: str) -> Any:
        """Awaitable; return value is unused."""


class _ScopeRepo(Protocol):
    """Minimal interface ``EligibleBrandsCache`` depends on."""

    async def find_publishers_for_brand(self, brand_id: UUID) -> list[tuple[UUID, str]]:
        """Return (publisher_uuid, lang) pairs for active scope rows."""
        ...


class EligibleBrandsCache:
    """Cache-aside store keyed by (publisher, lang)."""

    def __init__(self, redis_client: _KeyValueStore, scope_repo: _ScopeRepo) -> None:
        self._redis = redis_client
        self._scope_repo = scope_repo

    @staticmethod
    def _key(publisher_uuid: UUID, lang: str) -> str:
        return f"{_KEY_PREFIX}:{publisher_uuid}:{lang}"

    async def get(self, publisher_uuid: UUID, lang: str) -> list[dict[str, Any]] | None:
        key = self._key(publisher_uuid, lang)
        try:
            raw = await self._redis.get(key)
        except Exception as exc:
            _LOG.warning("eligible_brands_cache_get_failed", key=key, error=str(exc))
            return None
        if raw is None:
            return None
        return cast(list[dict[str, Any]], json.loads(raw))

    async def set(self, publisher_uuid: UUID, lang: str, value: list[dict[str, Any]]) -> None:
        key = self._key(publisher_uuid, lang)
        try:
            await self._redis.setex(key, _TTL_SECONDS, json.dumps(value))
        except Exception as exc:
            _LOG.warning("eligible_brands_cache_set_failed", key=key, error=str(exc))

    async def invalidate_for_brand(self, brand_id: UUID) -> None:
        """DEL every (publisher_uuid, lang) key for the brand's active scope rows."""
        try:
            pairs = await self._scope_repo.find_publishers_for_brand(brand_id)
        except Exception as exc:
            _LOG.warning(
                "eligible_brands_cache_invalidate_scope_lookup_failed",
                brand_id=str(brand_id),
                error=str(exc),
            )
            return
        for publisher_uuid, lang in pairs:
            key = self._key(publisher_uuid, lang)
            try:
                await self._redis.delete(key)
            except Exception as exc:
                _LOG.warning("eligible_brands_cache_invalidate_failed", key=key, error=str(exc))
