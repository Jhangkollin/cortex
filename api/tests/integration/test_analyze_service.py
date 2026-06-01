from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

import pytest
from cortex_brand_extract.errors import UpstreamTimeoutError as SP2Timeout
from cortex_brand_extract.types import BrandProfile, Category, ExtractionMeta

from cortex_api.core.background import BackgroundTaskTracker
from cortex_api.infra.container import Container as InfraContainer
from cortex_api.service.brand.analyze_config import AnalyzeConfig
from cortex_api.service.brand.analyze_service import AnalyzeJobService
from cortex_api.service.brand.model.analysis_job import (
    AnalyzeJobStatus,
    BrandProfileAnalysisJob,
)
from cortex_api.service.brand.repo.analysis_job_repo import AnalysisJobRepo
from cortex_api.service.brand.repo.profile_repo import BrandProfileRepo


class _NoopComposer:
    """No-op composer for analyze-service tests that don't exercise Hook B side effects.

    Hook B integration is verified in tests/integration/test_placement_composer.py
    (via the BrandService path); these tests focus on the analyze-job lifecycle.
    """

    async def compose(self, _brand_id):
        return None


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


def _cfg() -> AnalyzeConfig:
    return AnalyzeConfig(
        provider_kind="claude",
        api_key="x",
        model="m",
        base_url=None,
        tier="lite",
        stale_job_seconds=900,
    )


async def _brand(session):
    from cortex_api.service.brand_identity.model.brand import Brand

    b = Brand(display_name="AnalyzeSvcCo")
    session.add(b)
    await session.flush()
    return b.id


def _svc(db, extract_impl) -> AnalyzeJobService:
    return AnalyzeJobService(
        database_client=db,
        analysis_job_repo=AnalysisJobRepo(),
        profile_repo=BrandProfileRepo(),
        config=_cfg(),
        composer=_NoopComposer(),  # type: ignore[arg-type]
        tracker=BackgroundTaskTracker(),
        _extract=extract_impl,
    )


def _ok(name: str = "Acme", cost: float = 0.42):
    async def _fn(url, *, provider, tier):  # noqa: ANN001, ARG001
        return BrandProfile(
            url=url,
            name=name,
            category=Category(value="Bank", confidence=80),
            extraction_meta=ExtractionMeta(tier="lite", model="m", cost_usd=cost),
        )

    return _fn


async def test_success_persists_profile_and_marks_succeeded(database_client) -> None:
    async with database_client.session() as s:
        brand_id = await _brand(s)
    svc = _svc(database_client, _ok(cost=0.42))
    job = await svc.start_analyze(brand_id, "acme.test")
    await svc.drain()
    done = await svc.get_job(brand_id, job.id)
    assert done.status == AnalyzeJobStatus.SUCCEEDED
    assert done.cost_usd == 0.42
    async with database_client.session() as s:
        saved = await BrandProfileRepo().get(s, brand_id)
    assert saved is not None and saved.name == "Acme"


async def test_dedupes_in_flight(database_client) -> None:
    async with database_client.session() as s:
        brand_id = await _brand(s)
    started = asyncio.Event()
    release = asyncio.Event()

    async def slow(url, *, provider, tier):  # noqa: ANN001, ARG001
        started.set()
        await release.wait()
        return BrandProfile(
            url=url,
            name="A",
            category=Category(value="B", confidence=1),
            extraction_meta=ExtractionMeta(tier="lite", model="m", cost_usd=0.0),
        )

    svc = _svc(database_client, slow)
    j1 = await svc.start_analyze(brand_id, "a")
    await started.wait()
    j2 = await svc.start_analyze(brand_id, "a")
    assert j2.id == j1.id
    release.set()
    await svc.drain()


async def test_failure_translates_and_marks_failed(database_client) -> None:
    async with database_client.session() as s:
        brand_id = await _brand(s)

    async def boom(url, *, provider, tier):  # noqa: ANN001, ARG001
        raise SP2Timeout("llm timed out", stage="synthesize")

    svc = _svc(database_client, boom)
    job = await svc.start_analyze(brand_id, "a")
    await svc.drain()
    failed = await svc.get_job(brand_id, job.id)
    assert failed.status == AnalyzeJobStatus.FAILED
    assert "llm timed out" in (failed.error or "")


async def test_generic_exception_marks_failed(database_client) -> None:
    async with database_client.session() as s:
        brand_id = await _brand(s)

    async def kaboom(url, *, provider, tier):  # noqa: ANN001, ARG001
        raise ValueError("totally unexpected")

    svc = _svc(database_client, kaboom)
    job = await svc.start_analyze(brand_id, "a")
    await svc.drain()
    failed = await svc.get_job(brand_id, job.id)
    assert failed.status == AnalyzeJobStatus.FAILED
    assert (failed.error or "").startswith("unexpected: ValueError")


async def _age_created_at(database_client, brand_id, job_id, *, seconds: int) -> None:  # noqa: ANN001
    """Push a job's created_at into the past so the stale-sweep sees it."""
    async with database_client.session() as s:
        job = await AnalysisJobRepo().get(s, brand_id, job_id)
        assert job is not None
        job.created_at = datetime.utcnow() - timedelta(seconds=seconds)
        s.add(job)
        await s.flush()


async def test_sweep_stale_flips_aged_running_to_failed(database_client) -> None:
    async with database_client.session() as s:
        brand_id = await _brand(s)
    svc = _svc(database_client, _ok())
    async with database_client.session() as s:
        job = await AnalysisJobRepo().create(s, BrandProfileAnalysisJob(brand_id=brand_id, source_url="a"))
        await AnalysisJobRepo().mark_running(s, job)
    job_id = job.id
    # younger than the TTL: sweep must NOT touch it
    swept = await svc.sweep_stale()
    assert swept == 0
    still = await svc.get_job(brand_id, job_id)
    assert still.status == AnalyzeJobStatus.RUNNING
    # age it past stale_job_seconds (900) → sweep flips it to FAILED
    await _age_created_at(database_client, brand_id, job_id, seconds=1000)
    swept = await svc.sweep_stale()
    assert swept == 1
    reclaimed = await svc.get_job(brand_id, job_id)
    assert reclaimed.status == AnalyzeJobStatus.FAILED
    assert "stale" in (reclaimed.error or "")


async def test_cancel_all_marks_in_flight_job_failed(database_client) -> None:
    async with database_client.session() as s:
        brand_id = await _brand(s)
    running = asyncio.Event()
    release = asyncio.Event()

    async def blocked(url, *, provider, tier):  # noqa: ANN001, ARG001
        running.set()
        await release.wait()  # never released; cancel_all cancels the task
        return BrandProfile(
            url=url,
            name="A",
            category=Category(value="B", confidence=1),
            extraction_meta=ExtractionMeta(tier="lite", model="m", cost_usd=0.0),
        )

    svc = _svc(database_client, blocked)
    job = await svc.start_analyze(brand_id, "a")
    await running.wait()  # job row is RUNNING, task parked in _extract
    [task] = list(svc._tasks)
    await svc.cancel_all()
    failed = await svc.get_job(brand_id, job.id)
    assert failed.status == AnalyzeJobStatus.FAILED
    assert "cancelled at shutdown" in (failed.error or "")
    assert task.cancelled()
    assert svc._tasks == {}


async def test_orphan_deadlock_broken_by_sweep_then_fresh_start(database_client) -> None:
    """An aged RUNNING orphan would make find_in_flight dedupe forever;
    sweep_stale must clear it so a fresh start_analyze creates a NEW job."""
    async with database_client.session() as s:
        brand_id = await _brand(s)
    # Simulate a pod that died between mark_running and mark_succeeded.
    async with database_client.session() as s:
        orphan = await AnalysisJobRepo().create(s, BrandProfileAnalysisJob(brand_id=brand_id, source_url="a"))
        await AnalysisJobRepo().mark_running(s, orphan)
    orphan_id = orphan.id
    await _age_created_at(database_client, brand_id, orphan_id, seconds=1000)

    svc = _svc(database_client, _ok())
    # Pre-sweep: start_analyze would return the orphan (deadlock).
    deadlocked = await svc.start_analyze(brand_id, "a")
    assert deadlocked.id == orphan_id
    await svc.drain()

    # Re-orphan (drain may have advanced nothing since orphan has no task),
    # then sweep and prove a brand-new job is created instead of the orphan.
    async with database_client.session() as s:
        again = await AnalysisJobRepo().get(s, brand_id, orphan_id)
        assert again is not None
        again.status = AnalyzeJobStatus.RUNNING
        again.created_at = datetime.utcnow() - timedelta(seconds=1000)
        s.add(again)
        await s.flush()

    reclaimed = await svc.sweep_stale()
    assert reclaimed == 1
    fresh = await svc.start_analyze(brand_id, "a")
    assert fresh.id != orphan_id
    await svc.drain()
    done = await svc.get_job(brand_id, fresh.id)
    assert done.status == AnalyzeJobStatus.SUCCEEDED
