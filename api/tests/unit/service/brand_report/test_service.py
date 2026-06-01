from __future__ import annotations

import pytest
from cortex_brand_extract.llm.base import FakeProvider
from sqlalchemy.exc import IntegrityError

from cortex_api.core.exceptions import ConflictError, NotFoundError
from cortex_api.core.identifiers import uuid7
from cortex_api.service.brand.model.profile import BrandProfile
from cortex_api.service.brand_report.config import Config
from cortex_api.service.brand_report.job_service import BrandReportJobService
from cortex_api.service.brand_report.model.report import BrandReport, BrandReportStatus
from cortex_api.service.brand_report.service import BrandReportService


class _SessCtx:
    async def __aenter__(self):
        return object()

    async def __aexit__(self, *a):
        return False


class _DB:
    def session(self):
        return _SessCtx()


class _ProfileRepo:
    def __init__(self, profile):
        self._p = profile

    async def get(self, _s, _bid):
        return self._p


class _NullRepo:
    async def get(self, _s, _bid):
        return None


class _ReportRepo:
    def __init__(self):
        self.rows: dict[str, BrandReport] = {}
        self._in_flight: BrandReport | None = None

    async def find_in_flight(self, _s, _bid):
        return self._in_flight

    async def next_version(self, _s, _bid):
        return "v1.0"

    async def create(self, _s, row):
        self.rows[row.report_id] = row
        return row

    async def get(self, _s, _bid, rid):
        return self.rows.get(rid)

    async def list_for_brand(self, _s, _bid):
        return list(self.rows.values())

    async def mark_ready(self, _s, row, *, report_json, cost_usd):
        row.status = BrandReportStatus.READY
        row.report_json = report_json
        row.cost_usd = cost_usd

    async def mark_failed(self, _s, row, *, error):
        row.status = BrandReportStatus.FAILED
        row.error = error


def _provider():
    return FakeProvider(
        [
            {
                "coreJudgement": "J",
                "productNote": "P",
                "competitorNote": "C",
                "insights": {"confirmed": [], "inferences": [], "hypotheses": []},
                "faqAnswers": [],
            },
            {"risks": []},
        ]
    )


def _report_repo_with_rows(*rows: BrandReport) -> _ReportRepo:
    repo = _ReportRepo()
    for r in rows:
        repo.rows[r.report_id] = r
    return repo


def _job_svc(profile) -> BrandReportJobService:
    return BrandReportJobService(
        database_client=_DB(),
        report_repo=_ReportRepo(),
        profile_repo=_ProfileRepo(profile),
        media_repo=_NullRepo(),
        questions_repo=_NullRepo(),
        provider=_provider(),
        config=Config(),
    )


# ---------------------------------------------------------------------------
# BrandReportJobService tests
# ---------------------------------------------------------------------------


async def test_generate_without_profile_raises_not_found() -> None:
    svc = _job_svc(profile=None)
    with pytest.raises(NotFoundError):
        await svc.generate(uuid7())


async def test_generate_then_run_produces_ready_report() -> None:
    bid = uuid7()
    svc = _job_svc(profile=BrandProfile(brand_id=bid, name="Acme"))
    row = await svc.generate(bid)
    await svc.drain()
    # Fetch from the same report_repo via get
    done = svc._report_repo.rows[row.report_id]
    assert done.status == BrandReportStatus.READY
    assert done.report_json["meta"]["subject"] == "Acme"
    assert row.report_id.startswith("BIQ-")
    assert row.version == "v1.0"
    assert done.report_json["meta"]["reportId"] == done.report_id


# ---------------------------------------------------------------------------
# BrandReportService (read-only) tests
# ---------------------------------------------------------------------------


async def test_get_report_returns_row() -> None:
    bid = uuid7()
    existing = BrandReport(brand_id=bid, report_id="BIQ-x", version="v1.0")
    repo = _report_repo_with_rows(existing)
    svc = BrandReportService(database_client=_DB(), report_repo=repo)
    result = await svc.get_report(bid, "BIQ-x")
    assert result.report_id == "BIQ-x"


async def test_get_report_missing_raises_not_found() -> None:
    bid = uuid7()
    svc = BrandReportService(database_client=_DB(), report_repo=_ReportRepo())
    with pytest.raises(NotFoundError):
        await svc.get_report(bid, "BIQ-nope")


async def test_list_reports_returns_all_rows() -> None:
    bid = uuid7()
    r1 = BrandReport(brand_id=bid, report_id="BIQ-a", version="v1.0")
    r2 = BrandReport(brand_id=bid, report_id="BIQ-b", version="v2.0")
    repo = _report_repo_with_rows(r1, r2)
    svc = BrandReportService(database_client=_DB(), report_repo=repo)
    rows = await svc.list_reports(bid)
    assert {r.report_id for r in rows} == {"BIQ-a", "BIQ-b"}


async def test_generate_dedupes_in_flight() -> None:
    """If find_in_flight returns an existing GENERATING row, generate() returns
    it immediately without calling create()."""
    bid = uuid7()
    existing = BrandReport(brand_id=bid, report_id="BIQ-existing", version="v1.0")
    existing.status = BrandReportStatus.GENERATING

    report_repo = _ReportRepo()
    report_repo._in_flight = existing

    svc = BrandReportJobService(
        database_client=_DB(),
        report_repo=report_repo,
        profile_repo=_ProfileRepo(BrandProfile(brand_id=bid, name="Acme")),
        media_repo=_NullRepo(),
        questions_repo=_NullRepo(),
        provider=_provider(),
        config=Config(),
    )

    result = await svc.generate(bid)

    # Must return the existing row, not create a new one
    assert result.report_id == "BIQ-existing"
    assert result.status == BrandReportStatus.GENERATING
    # create() was never called — rows dict is still empty
    assert report_repo.rows == {}


async def test_generate_maps_integrity_error_to_conflict() -> None:
    """If create() raises IntegrityError (concurrent insert race), generate()
    maps it to ConflictError (HTTP 409)."""
    bid = uuid7()

    class _RaisingRepo(_ReportRepo):
        async def create(self, _s, row):  # noqa: ANN001, ANN201
            raise IntegrityError("stmt", {}, Exception("dup"))

    report_repo = _RaisingRepo()

    svc = BrandReportJobService(
        database_client=_DB(),
        report_repo=report_repo,
        profile_repo=_ProfileRepo(BrandProfile(brand_id=bid, name="Acme")),
        media_repo=_NullRepo(),
        questions_repo=_NullRepo(),
        provider=_provider(),
        config=Config(),
    )

    with pytest.raises(ConflictError):
        await svc.generate(bid)
