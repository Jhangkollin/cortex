from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from cortex_api.core.identifiers import uuid7
from cortex_api.infra.container import Container as InfraContainer
from cortex_api.service.brand_identity.model.brand import Brand
from cortex_api.service.brand_report.model.report import BrandReport, BrandReportStatus
from cortex_api.service.brand_report.repo.report_repo import BrandReportRepo

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
async def _schema():
    from sqlmodel import SQLModel

    db = InfraContainer()._database_client_factory()
    async with db.session() as s:
        conn = await s.connection()
        await conn.run_sync(SQLModel.metadata.create_all)


async def test_second_ready_archives_first_and_bumps_version() -> None:
    db = InfraContainer()._database_client_factory()
    repo = BrandReportRepo()
    bid = uuid7()
    async with db.session() as s:
        s.add(Brand(id=bid, display_name="RepoCo"))
        await s.flush()
        v1 = await repo.create(s, BrandReport(brand_id=bid, report_id="BIQ-1", version="v1.0"))
        await repo.mark_ready(s, v1, report_json={"meta": {}}, cost_usd=0.01)

    async with db.session() as s:
        assert await repo.next_version(s, bid) == "v1.1"
        v2 = await repo.create(s, BrandReport(brand_id=bid, report_id="BIQ-2", version="v1.1"))
        await repo.mark_ready(s, v2, report_json={"meta": {}}, cost_usd=0.02)

    async with db.session() as s:
        current = await repo.get_current(s, bid)
        assert current is not None and current.report_id == "BIQ-2"
        history = await repo.list_for_brand(s, bid)
        assert [r.report_id for r in history] == ["BIQ-2", "BIQ-1"]
        assert sum(1 for r in history if r.archived_at is None and r.status == BrandReportStatus.READY) == 1


async def test_get_is_brand_scoped() -> None:
    db = InfraContainer()._database_client_factory()
    repo = BrandReportRepo()
    bid = uuid7()
    async with db.session() as s:
        s.add(Brand(id=bid, display_name="ScopeCo"))
        await s.flush()
        await repo.create(s, BrandReport(brand_id=bid, report_id="BIQ-SCOPE", version="v1.0"))

    async with db.session() as s:
        got = await repo.get(s, bid, "BIQ-SCOPE")
        assert got is not None and got.report_id == "BIQ-SCOPE"
        assert await repo.get(s, uuid4(), "BIQ-SCOPE") is None  # cross-tenant


async def test_mark_failed() -> None:
    db = InfraContainer()._database_client_factory()
    repo = BrandReportRepo()
    bid = uuid7()
    async with db.session() as s:
        s.add(Brand(id=bid, display_name="FailCo"))
        await s.flush()
        row = await repo.create(s, BrandReport(brand_id=bid, report_id="BIQ-FAIL", version="v1.0"))
        await repo.mark_failed(s, row, error="boom")

    async with db.session() as s:
        got = await repo.get(s, bid, "BIQ-FAIL")
        assert got is not None
        assert got.status == BrandReportStatus.FAILED
        assert got.error == "boom"


async def test_sweep_stale() -> None:
    db = InfraContainer()._database_client_factory()
    repo = BrandReportRepo()
    bid = uuid7()
    async with db.session() as s:
        s.add(Brand(id=bid, display_name="SweepCo"))
        await s.flush()
        row = await repo.create(s, BrandReport(brand_id=bid, report_id="BIQ-STALE", version="v1.0"))
        assert row.status == BrandReportStatus.GENERATING
        row.created_at = datetime.utcnow() - timedelta(hours=1)
        s.add(row)
        await s.flush()
        swept = await repo.sweep_stale(s, older_than_seconds=60)
        assert swept == 1

    async with db.session() as s:
        got = await repo.get(s, bid, "BIQ-STALE")
        assert got is not None and got.status == BrandReportStatus.FAILED


async def test_next_version_is_monotonic_across_failures() -> None:
    """next_version must count across ALL statuses, not just READY.

    After a v1.0 row is FAILED, next_version must return v1.1 (not v1.0)
    so that retries never collide on UNIQUE(brand_id, version).
    """
    db = InfraContainer()._database_client_factory()
    repo = BrandReportRepo()
    bid = uuid7()
    async with db.session() as s:
        s.add(Brand(id=bid, display_name="MonotoneCo"))
        await s.flush()
        row = await repo.create(s, BrandReport(brand_id=bid, report_id="BIQ-MONO", version="v1.0"))
        await repo.mark_failed(s, row, error="first attempt failed")

    async with db.session() as s:
        version = await repo.next_version(s, bid)
        assert version == "v1.1"
