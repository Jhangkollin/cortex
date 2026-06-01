"""Brand IQ Report API integration tests (COR-79, Task 10).

Mirrors ``test_media_network_api.py`` exactly: same ``_schema`` autouse
fixture, same ``_authed`` / ``make_client`` + DI-provider override approach,
same cross-tenant rejection probe.

``job_service`` is overridden with a ``BrandReportJobService`` whose
``provider`` is ``_AllFieldsProvider`` — a deterministic in-process fake that
satisfies both LLM calls (insights + risks) without any network I/O.
``service`` is overridden with a real ``BrandReportService`` backed by the
same real DB and ``BrandReportRepo`` (read path needs no provider).
Brand + brand_profile rows are seeded inside the TestClient portal loop so
the in-process worker's DB reads see them.

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
from cortex_brand_extract.llm.base import LLMResult
from fastapi.testclient import TestClient

from cortex_api.app.dependencies.auth import authenticated_user
from cortex_api.core.identifiers import uuid7
from cortex_api.infra.container import Container as InfraContainer
from cortex_api.infra.database_client import DatabaseClient
from cortex_api.main import create_app
from cortex_api.service.brand.model.profile import BrandProfile
from cortex_api.service.brand.repo.profile_repo import BrandProfileRepo
from cortex_api.service.brand_identity.model.brand import Brand
from cortex_api.service.brand_report.config import Config
from cortex_api.service.brand_report.job_service import BrandReportJobService
from cortex_api.service.brand_report.repo.report_repo import BrandReportRepo
from cortex_api.service.brand_report.service import BrandReportService
from cortex_api.service.identity.model.authed_user import AuthedUser
from cortex_api.service.media_network.repo.brand_media_repo import BrandMediaRepo
from cortex_api.service.questions.repo.brand_questions_repo import BrandQuestionsRepo

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Deterministic fake LLM provider — no network, no LLM, no mock.patch
# ---------------------------------------------------------------------------


class _AllFieldsProvider:
    """Returns a payload satisfying BOTH compose() calls (insights + risks) on every call,
    so it works for any number of generations / polls. No network."""

    model = "fake"

    async def complete_json(self, *, system: str, user: str, schema: object) -> LLMResult:
        return LLMResult(
            data={
                "coreJudgement": "j",
                "productNote": "p",
                "competitorNote": "c",
                "insights": {"confirmed": [], "inferences": [], "hypotheses": []},
                "faqAnswers": [],
                "risks": [],
            },
            cost_usd=0.001,
        )


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


async def _seed(db: DatabaseClient, bid: UUID, seed_profile: bool) -> None:
    """Seed brand row and optionally a brand_profile row."""
    async with db.session() as s:
        s.add(Brand(id=bid, display_name="ReportApiCo"))
        await s.flush()
        if seed_profile:
            await BrandProfileRepo().upsert(s, BrandProfile(brand_id=bid, name="Acme"))


# ---------------------------------------------------------------------------
# make_client factory fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def make_client() -> Generator[Any, None, None]:
    """Yield a ``make_client(*, jwt_brand_id=None, caps=None, seed_profile=True)``
    factory context manager.

    - Builds the real app via ``create_app()``.
    - Overrides ``authenticated_user`` with a brand-scoped ``AuthedUser``.
    - Overrides ``_brand_report_container.job_service`` with a
      ``BrandReportJobService`` whose LLM provider is the deterministic
      ``_AllFieldsProvider`` fake (lifecycle path).
    - Overrides ``_brand_report_container.service`` with a real
      ``BrandReportService(database_client=db, report_repo=BrandReportRepo())``
      (read path needs no provider).
    - Seeds brand (+ optionally brand_profile) via ``c.portal.call(_seed, ...)``
      so the in-process worker's DB reads see the rows.
    - Yields ``(client, brand_id)``.
    """
    from cortex_api import main as _main

    overridden = False

    @contextlib.contextmanager
    def _factory(
        *,
        jwt_brand_id: UUID | None = None,
        caps: list[str] | None = None,
        seed_profile: bool = True,
    ) -> Generator[tuple[TestClient, UUID], None, None]:
        nonlocal overridden
        app = create_app()

        bid = uuid7()
        db = _main._brand_report_container.database_client()

        fake_job_service = BrandReportJobService(
            database_client=db,
            report_repo=BrandReportRepo(),
            profile_repo=BrandProfileRepo(),
            media_repo=BrandMediaRepo(),
            questions_repo=BrandQuestionsRepo(),
            provider=_AllFieldsProvider(),
            config=Config(),
        )
        real_service = BrandReportService(
            database_client=db,
            report_repo=BrandReportRepo(),
        )
        _main._brand_report_container.job_service.override(fake_job_service)
        _main._brand_report_container.service.override(real_service)
        overridden = True

        token_brand = jwt_brand_id if jwt_brand_id is not None else bid
        token_caps = caps if caps is not None else ["view_brand_dashboard"]
        app.dependency_overrides[authenticated_user] = lambda: _authed(token_brand, token_caps)

        with TestClient(app) as c:
            # Seed inside the portal loop so the worker's reads see the rows.
            portal: BlockingPortal = c.portal  # type: ignore[assignment]
            portal.call(_seed, db, bid, seed_profile)
            yield c, bid

    try:
        yield _factory
    finally:
        if overridden:
            _main._brand_report_container.job_service.reset_override()
            _main._brand_report_container.service.reset_override()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_generate_then_poll_ready(make_client: Any) -> None:
    """POST /report → 202; polling GET eventually returns status == 'ready'
    with report.meta.subject matching the seeded profile name."""
    with make_client() as (client, brand_id):
        r = client.post(f"/v1/brand/{brand_id}/report")
        assert r.status_code == 202, r.text
        report_id = r.json()["reportId"]

        body: dict[str, Any] = {}
        for _ in range(50):
            g = client.get(f"/v1/brand/{brand_id}/report/{report_id}")
            assert g.status_code == 200, g.text
            body = g.json()
            if body["status"] in ("ready", "failed"):
                break

        assert body["status"] == "ready", body
        assert body["report"]["meta"]["subject"] == "Acme"


def test_get_unknown_report_404(make_client: Any) -> None:
    """GET /report/NOPE for a brand that has no such report → 404."""
    with make_client() as (client, brand_id):
        g = client.get(f"/v1/brand/{brand_id}/report/NOPE")
        assert g.status_code == 404, g.text


def test_generate_without_profile_404(make_client: Any) -> None:
    """POST /report when brand has no profile → 404 (service raises NotFoundError)."""
    with make_client(seed_profile=False) as (client, brand_id):
        r = client.post(f"/v1/brand/{brand_id}/report")
        assert r.status_code == 404, r.text


def test_generate_without_capability_403(make_client: Any) -> None:
    """A token missing VIEW_BRAND_DASHBOARD must be refused on POST with 403."""
    with make_client(caps=["edit_brand_settings"]) as (client, brand_id):
        r = client.post(f"/v1/brand/{brand_id}/report")
        assert r.status_code == 403, r.text


def test_cross_tenant_rejected(make_client: Any) -> None:
    """JWT scoped to a different brand hitting seeded brand's reports URL → 4xx.

    ``active_brand`` sees JWT brand ≠ URL brand and raises ContextMismatchError
    → mapped to 400 by the exception handler.
    """
    other = uuid.uuid4()
    with make_client(jwt_brand_id=other) as (client, seeded_bid):
        g = client.get(f"/v1/brand/{seeded_bid}/reports")
        assert 400 <= g.status_code < 500, g.text


def test_reports_version_list(make_client: Any) -> None:
    """Generate two reports, poll each to ready; GET /reports returns 2 items,
    exactly one marked current == True."""
    with make_client() as (client, brand_id):

        def _generate_and_wait() -> None:
            r = client.post(f"/v1/brand/{brand_id}/report")
            assert r.status_code == 202, r.text
            report_id = r.json()["reportId"]
            for _ in range(50):
                g = client.get(f"/v1/brand/{brand_id}/report/{report_id}")
                body = g.json()
                if body["status"] in ("ready", "failed"):
                    break
            assert body.get("status") == "ready", body

        _generate_and_wait()
        _generate_and_wait()

        g = client.get(f"/v1/brand/{brand_id}/reports")
        assert g.status_code == 200, g.text
        items = g.json()
        assert len(items) == 2, items
        current_flags = [item["current"] for item in items]
        assert current_flags.count(True) == 1, items


def test_ui_state_celebrate_ready_lifecycle(make_client: Any) -> None:
    """Arm + a READY report → celebrateReady True; consume → celebrateReady False."""
    with make_client() as (client, brand_id):
        a = client.post(f"/v1/brand/{brand_id}/report/ui-state/arm")
        assert a.status_code == 204, a.text

        r = client.post(f"/v1/brand/{brand_id}/report")
        assert r.status_code == 202, r.text
        report_id = r.json()["reportId"]
        body: dict[str, Any] = {}
        for _ in range(50):
            g = client.get(f"/v1/brand/{brand_id}/report/{report_id}")
            body = g.json()
            if body["status"] in ("ready", "failed"):
                break
        assert body.get("status") == "ready", body

        s = client.get(f"/v1/brand/{brand_id}/report/ui-state")
        assert s.status_code == 200, s.text
        state = s.json()
        assert state["celebrateReady"] is True, state
        assert state["celebratePending"] is True, state

        c = client.post(f"/v1/brand/{brand_id}/report/ui-state/celebrate-consume")
        assert c.status_code == 204, c.text

        s2 = client.get(f"/v1/brand/{brand_id}/report/ui-state")
        assert s2.status_code == 200, s2.text
        assert s2.json()["celebrateReady"] is False, s2.json()
