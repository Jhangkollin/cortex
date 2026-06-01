from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from cortex_api.infra.container import Container as InfraContainer
from cortex_api.service.brand.model.analysis_job import (
    AnalyzeJobStatus,
    BrandProfileAnalysisJob,
)
from cortex_api.service.brand.repo.analysis_job_repo import AnalysisJobRepo
from cortex_api.service.brand_identity.model.brand import Brand

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
async def _schema():
    from sqlmodel import SQLModel

    db = InfraContainer()._database_client_factory()
    async with db.session() as s:
        conn = await s.connection()
        await conn.run_sync(SQLModel.metadata.create_all)


@pytest.fixture
def database_client():
    return InfraContainer()._database_client_factory()


async def _brand(session) -> object:
    b = Brand(display_name="AnalyzeRepoCo")
    session.add(b)
    await session.flush()
    return b.id


async def test_create_get_and_scope(database_client) -> None:
    repo = AnalysisJobRepo()
    async with database_client.session() as s:
        brand_id = await _brand(s)
        job = await repo.create(s, BrandProfileAnalysisJob(brand_id=brand_id, source_url="acme.test"))
        got = await repo.get(s, brand_id, job.id)
        assert got is not None and got.id == job.id
        assert await repo.get(s, uuid4(), job.id) is None  # cross-tenant


async def test_find_in_flight(database_client) -> None:
    repo = AnalysisJobRepo()
    async with database_client.session() as s:
        brand_id = await _brand(s)
        assert await repo.find_in_flight(s, brand_id) is None
        j = await repo.create(s, BrandProfileAnalysisJob(brand_id=brand_id, source_url="x"))
        found = await repo.find_in_flight(s, brand_id)
        assert found is not None and found.id == j.id
        await repo.mark_succeeded(s, j, cost_usd=0.5)
        assert await repo.find_in_flight(s, brand_id) is None


async def test_mark_transitions_and_sweep(database_client) -> None:
    repo = AnalysisJobRepo()
    async with database_client.session() as s:
        brand_id = await _brand(s)
        j = await repo.create(s, BrandProfileAnalysisJob(brand_id=brand_id, source_url="x"))
        await repo.mark_running(s, j)
        assert j.status == AnalyzeJobStatus.RUNNING
        j.created_at = datetime.utcnow() - timedelta(hours=1)
        await s.flush()
        swept = await repo.sweep_stale(s, older_than_seconds=60)
        assert swept >= 1
        refreshed = await repo.get(s, brand_id, j.id)
        assert refreshed is not None and refreshed.status == AnalyzeJobStatus.FAILED
