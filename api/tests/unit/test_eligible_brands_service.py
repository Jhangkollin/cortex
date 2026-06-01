"""Unit tests for EligibleBrandsService."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from cortex_api.service.placement.repo.eligible_brands_repo import EligibleBrandRow
from cortex_api.service.placement.service.eligible_brands_service import EligibleBrandsService


def _row(name: str = "Acme") -> EligibleBrandRow:
    return EligibleBrandRow(
        brand_uuid=UUID(int=1),
        brand_name=name,
        brand_description="desc",
        brand_topics=["t"],
        matching_keywords=["k"],
        matching_categories=["c"],
        matching_rules="rules",
        ad_ratio=0.5,
        question_position=2,
        mode="question_replacement",
        brand_answer_prompt="a",
        brand_question_prompt="q",
        brand_cta_text="cta",
        brand_cta_url="https://x",
    )


@pytest.fixture
def cache_mock() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def repo_mock() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def db_client_mock() -> MagicMock:
    """db client with .session() context manager returning a MagicMock session."""
    m = MagicMock()
    session = AsyncMock()
    m.session.return_value.__aenter__.return_value = session
    m.session.return_value.__aexit__.return_value = None
    return m


class TestEligibleBrandsService:
    @pytest.mark.asyncio
    async def test_cache_hit_skips_repo(
        self, cache_mock: AsyncMock, repo_mock: AsyncMock, db_client_mock: MagicMock
    ) -> None:
        cached_payload = [{"brand_uuid": "abc", "brand_name": "X"}]
        cache_mock.get.return_value = cached_payload
        svc = EligibleBrandsService(database_client=db_client_mock, repo=repo_mock, cache=cache_mock)
        out = await svc.list_eligible(publisher_uuid=UUID(int=5), lang="zh-tw")
        assert out == cached_payload
        repo_mock.find_for_publisher.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_cache_miss_hits_repo_then_sets_cache(
        self, cache_mock: AsyncMock, repo_mock: AsyncMock, db_client_mock: MagicMock
    ) -> None:
        cache_mock.get.return_value = None
        repo_mock.find_for_publisher.return_value = [_row("Acme")]
        svc = EligibleBrandsService(database_client=db_client_mock, repo=repo_mock, cache=cache_mock)
        out = await svc.list_eligible(publisher_uuid=UUID(int=5), lang="zh-tw")
        assert len(out) == 1
        assert out[0]["brand_name"] == "Acme"
        cache_mock.set.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_empty_result_returns_empty_list_and_sets_empty_cache(
        self, cache_mock: AsyncMock, repo_mock: AsyncMock, db_client_mock: MagicMock
    ) -> None:
        cache_mock.get.return_value = None
        repo_mock.find_for_publisher.return_value = []
        svc = EligibleBrandsService(database_client=db_client_mock, repo=repo_mock, cache=cache_mock)
        out = await svc.list_eligible(publisher_uuid=UUID(int=5), lang="zh-tw")
        assert out == []
        cache_mock.set.assert_awaited_once_with(publisher_uuid=UUID(int=5), lang="zh-tw", value=[])
