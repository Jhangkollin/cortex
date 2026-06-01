"""Brand IQ Report PDF API integration tests (COR-80).

Mirrors ``test_brand_report_api.py``: same ``_schema`` autouse, same
``_authed`` / ``make_client`` approach. The renderer is overridden at the DI
container level — tests never launch Chromium.

These tests are CI-pending: they require Postgres (``docker-compose up -d``)
and are skipped by ``pytest -m "not integration"``.
"""

from __future__ import annotations

import contextlib
import uuid
from collections.abc import Generator
from typing import Any
from uuid import UUID

import pytest
from anyio.from_thread import BlockingPortal
from fastapi.testclient import TestClient

from cortex_api.app.dependencies.auth import authenticated_user
from cortex_api.core.identifiers import uuid7
from cortex_api.infra.container import Container as InfraContainer
from cortex_api.infra.database_client import DatabaseClient
from cortex_api.main import create_app
from cortex_api.service.brand_identity.model.brand import Brand
from cortex_api.service.brand_report.config import Config
from cortex_api.service.brand_report.model.report import BrandReport, BrandReportStatus
from cortex_api.service.brand_report.pdf_service import BrandReportPdfService
from cortex_api.service.brand_report.repo.report_repo import BrandReportRepo
from cortex_api.service.brand_report.service import BrandReportService
from cortex_api.service.identity.model.authed_user import AuthedUser

pytestmark = pytest.mark.integration

# ---------------------------------------------------------------------------
# Fake renderer — returns stub PDF bytes; never launches Chromium
# ---------------------------------------------------------------------------

_FAKE_PDF = b"%PDF-1.4 test-stub-for-integration-tests"


async def _fake_renderer(html: str, *, timeout_ms: int, max_concurrent: int) -> bytes:
    return _FAKE_PDF


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
async def _schema() -> None:
    from sqlmodel import SQLModel

    db = InfraContainer()._database_client_factory()
    async with db.session() as s:
        conn = await s.connection()
        await conn.run_sync(SQLModel.metadata.create_all)


def _authed(brand_id: UUID, caps: list[str]) -> AuthedUser:
    return AuthedUser(
        user_id=uuid7(),
        email="t@example.com",
        display_name="T",
        raw_claims={
            "active_context": {
                "kind": "brand",
                "id": str(brand_id),
                "role": "admin",
                "capabilities": caps,
            }
        },
    )


async def _seed(
    db: DatabaseClient,
    bid: UUID,
    report_id: str,
    report_json: dict,  # type: ignore[type-arg]
    status: BrandReportStatus = BrandReportStatus.READY,
) -> None:
    """Seed a Brand row plus a BrandReport row in the given status."""
    async with db.session() as s:
        s.add(Brand(id=bid, display_name="PDFTestCo"))
        await s.flush()
        row = BrandReport(brand_id=bid, report_id=report_id, version="v1.0")
        row.status = status
        # GENERATING reports legitimately have no report_json yet.
        row.report_json = report_json if status == BrandReportStatus.READY else None
        s.add(row)
        await s.flush()


_MINIMAL_REPORT_JSON: dict = {
    "meta": {
        "subject": "PDFTestBrand",
        "enName": "PDFTestBrand",
        "monogram": "P",
        "primaryMarket": "台灣",
        "extendedMarkets": [],
        "reportDate": "2026-05-24",
        "windowFrom": "2025-05-24",
        "windowTo": "2026-05-24",
        "confidence": 90,
        "reportId": "BIQ-PDF-TEST",
        "pageCount": 8,
        "preparedFor": "Test User",
        "preparedBy": "Cortex · Brand Agent",
    },
    "core": [],
    "coreJudgement": "",
    "productLines": [],
    "productNote": "",
    "subBrands": [],
    "endorsements": {"status": "資料不足", "body": ""},
    "ipCollabs": {"status": "資料不足", "body": ""},
    "mediaNetwork": [],
    "competitors": [],
    "competitorNote": "",
    "insights": {"confirmed": [], "inferences": [], "hypotheses": []},
    "faq": [],
    "channels": [],
    "risks": [],
    "sources": {"A": [], "B": [], "C": []},
    "quality": {"high": "", "midLow": "", "gaps": "", "conflicts": "", "open": ""},
}


# ---------------------------------------------------------------------------
# make_client factory fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def make_client() -> Generator[Any, None, None]:
    """Yield a factory that creates a TestClient with the fake PDF renderer wired in."""
    from cortex_api import main as _main

    overridden = False

    @contextlib.contextmanager
    def _factory(
        *,
        jwt_brand_id: UUID | None = None,
        caps: list[str] | None = None,
        report_id: str = "BIQ-PDF-TEST",
        seed_report: bool = True,
        status: BrandReportStatus = BrandReportStatus.READY,
    ) -> Generator[tuple[TestClient, UUID], None, None]:
        nonlocal overridden
        app = create_app()

        bid = uuid7()
        db = _main._brand_report_container.database_client()

        # Build a real BrandReportPdfService wired to the fake renderer
        real_service = BrandReportService(
            database_client=db,
            report_repo=BrandReportRepo(),
        )
        fake_pdf_service = BrandReportPdfService(
            service=real_service,
            renderer=_fake_renderer,
            config=Config(),
        )

        _main._brand_report_container.service.override(real_service)
        _main._brand_report_container.pdf_service.override(fake_pdf_service)
        overridden = True

        token_brand = jwt_brand_id if jwt_brand_id is not None else bid
        token_caps = caps if caps is not None else ["view_brand_dashboard"]
        app.dependency_overrides[authenticated_user] = lambda: _authed(token_brand, token_caps)

        with TestClient(app) as c:
            portal: BlockingPortal = c.portal  # type: ignore[assignment]
            if seed_report:
                portal.call(_seed, db, bid, report_id, _MINIMAL_REPORT_JSON, status)
            yield c, bid

    try:
        yield _factory
    finally:
        if overridden:
            _main._brand_report_container.service.reset_override()
            _main._brand_report_container.pdf_service.reset_override()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_download_pdf_200_application_pdf(make_client: Any) -> None:
    """GET /report/{id}/pdf with a READY report → 200 application/pdf."""
    report_id = "BIQ-PDF-TEST"
    with make_client(report_id=report_id) as (client, brand_id):
        r = client.get(f"/v1/brand/{brand_id}/report/{report_id}/pdf")
        assert r.status_code == 200, r.text
        assert r.headers["content-type"] == "application/pdf"


def test_download_pdf_content_disposition_attachment(make_client: Any) -> None:
    """PDF response must have Content-Disposition: attachment."""
    report_id = "BIQ-PDF-TEST"
    with make_client(report_id=report_id) as (client, brand_id):
        r = client.get(f"/v1/brand/{brand_id}/report/{report_id}/pdf")
        assert r.status_code == 200, r.text
        cd = r.headers.get("content-disposition", "")
        assert "attachment" in cd


def test_download_pdf_content_disposition_has_filename(make_client: Any) -> None:
    """Content-Disposition must include a filename."""
    report_id = "BIQ-PDF-TEST"
    with make_client(report_id=report_id) as (client, brand_id):
        r = client.get(f"/v1/brand/{brand_id}/report/{report_id}/pdf")
        cd = r.headers.get("content-disposition", "")
        assert "filename" in cd
        assert ".pdf" in cd


def test_download_pdf_body_is_fake_pdf(make_client: Any) -> None:
    """Response body is exactly the fake renderer's output."""
    report_id = "BIQ-PDF-TEST"
    with make_client(report_id=report_id) as (client, brand_id):
        r = client.get(f"/v1/brand/{brand_id}/report/{report_id}/pdf")
        assert r.content == _FAKE_PDF


def test_download_pdf_404_unknown_report(make_client: Any) -> None:
    """GET /report/NOPE/pdf with no such report → 404."""
    with make_client() as (client, brand_id):
        r = client.get(f"/v1/brand/{brand_id}/report/BIQ-DOES-NOT-EXIST/pdf")
        assert r.status_code == 404, r.text


def test_download_pdf_409_not_ready(make_client: Any) -> None:
    """GET /report/{id}/pdf for a GENERATING (not-yet-READY) report → 409."""
    report_id = "BIQ-GENERATING"
    with make_client(report_id=report_id, status=BrandReportStatus.GENERATING) as (client, brand_id):
        r = client.get(f"/v1/brand/{brand_id}/report/{report_id}/pdf")
        assert r.status_code == 409, r.text


def test_download_pdf_403_missing_capability(make_client: Any) -> None:
    """JWT missing view_brand_dashboard → 403."""
    report_id = "BIQ-PDF-TEST"
    with make_client(report_id=report_id, caps=["edit_brand_settings"]) as (client, brand_id):
        r = client.get(f"/v1/brand/{brand_id}/report/{report_id}/pdf")
        assert r.status_code == 403, r.text


def test_download_pdf_cross_tenant_rejected(make_client: Any) -> None:
    """JWT scoped to different brand → 4xx (ContextMismatchError)."""
    other = uuid.uuid4()
    report_id = "BIQ-PDF-TEST"
    with make_client(jwt_brand_id=other, report_id=report_id) as (client, seeded_bid):
        r = client.get(f"/v1/brand/{seeded_bid}/report/{report_id}/pdf")
        assert 400 <= r.status_code < 500, r.text
