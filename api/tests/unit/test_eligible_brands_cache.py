"""Unit tests for EligibleBrandsCache."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from cortex_api.service.placement.cache.eligible_brands_cache import EligibleBrandsCache


@pytest.fixture
def redis_mock() -> AsyncMock:
    """Redis client double; methods are AsyncMock."""
    m = AsyncMock()
    return m


@pytest.fixture
def scope_repo_mock() -> AsyncMock:
    return AsyncMock()


class TestEligibleBrandsCacheGetSet:
    @pytest.mark.asyncio
    async def test_get_returns_none_on_miss(self, redis_mock: AsyncMock, scope_repo_mock: AsyncMock) -> None:
        redis_mock.get.return_value = None
        cache = EligibleBrandsCache(redis_client=redis_mock, scope_repo=scope_repo_mock)
        out = await cache.get(publisher_uuid=UUID(int=1), lang="zh-tw")
        assert out is None
        redis_mock.get.assert_awaited_once_with("eligible_brands:00000000-0000-0000-0000-000000000001:zh-tw")

    @pytest.mark.asyncio
    async def test_get_returns_decoded_list_on_hit(self, redis_mock: AsyncMock, scope_repo_mock: AsyncMock) -> None:
        payload = [{"brand_uuid": "abc", "brand_name": "Acme"}]
        redis_mock.get.return_value = json.dumps(payload).encode("utf-8")
        cache = EligibleBrandsCache(redis_client=redis_mock, scope_repo=scope_repo_mock)
        out = await cache.get(publisher_uuid=UUID(int=2), lang="en-us")
        assert out == payload

    @pytest.mark.asyncio
    async def test_set_calls_setex_with_300s_ttl(self, redis_mock: AsyncMock, scope_repo_mock: AsyncMock) -> None:
        cache = EligibleBrandsCache(redis_client=redis_mock, scope_repo=scope_repo_mock)
        await cache.set(publisher_uuid=UUID(int=3), lang="zh-tw", value=[{"a": 1}])
        redis_mock.setex.assert_awaited_once()
        args = redis_mock.setex.call_args
        assert args.args[0] == "eligible_brands:00000000-0000-0000-0000-000000000003:zh-tw"
        assert args.args[1] == 300
        assert json.loads(args.args[2]) == [{"a": 1}]


class TestEligibleBrandsCacheInvalidate:
    @pytest.mark.asyncio
    async def test_invalidate_for_brand_dels_each_publisher_lang_key(
        self, redis_mock: AsyncMock, scope_repo_mock: AsyncMock
    ) -> None:
        scope_repo_mock.find_publishers_for_brand.return_value = [
            (UUID(int=10), "zh-tw"),
            (UUID(int=10), "en-us"),
            (UUID(int=11), "zh-tw"),
        ]
        cache = EligibleBrandsCache(redis_client=redis_mock, scope_repo=scope_repo_mock)
        await cache.invalidate_for_brand(brand_id=UUID(int=99))
        assert redis_mock.delete.await_count == 3
        called_keys = [c.args[0] for c in redis_mock.delete.await_args_list]
        assert "eligible_brands:00000000-0000-0000-0000-00000000000a:zh-tw" in called_keys
        assert "eligible_brands:00000000-0000-0000-0000-00000000000a:en-us" in called_keys
        assert "eligible_brands:00000000-0000-0000-0000-00000000000b:zh-tw" in called_keys

    @pytest.mark.asyncio
    async def test_invalidate_swallows_redis_errors(self, redis_mock: AsyncMock, scope_repo_mock: AsyncMock) -> None:
        scope_repo_mock.find_publishers_for_brand.return_value = [(UUID(int=1), "zh-tw")]
        redis_mock.delete.side_effect = ConnectionError("redis down")
        cache = EligibleBrandsCache(redis_client=redis_mock, scope_repo=scope_repo_mock)
        # Must NOT raise
        await cache.invalidate_for_brand(brand_id=UUID(int=99))


class TestEligibleBrandsCacheGetDegradesOnRedisError:
    @pytest.mark.asyncio
    async def test_get_returns_none_when_redis_raises(self, redis_mock: AsyncMock, scope_repo_mock: AsyncMock) -> None:
        redis_mock.get.side_effect = ConnectionError("redis down")
        cache = EligibleBrandsCache(redis_client=redis_mock, scope_repo=scope_repo_mock)
        out = await cache.get(publisher_uuid=UUID(int=1), lang="zh-tw")
        assert out is None  # Degrade to cache miss; caller hits DB
