"""Analyze-pipeline API integration tests.

Harness is copied VERBATIM from ``test_brand_profile_api.py`` (SP-1):
the same ``_schema`` autouse fixture, the same ``_authed`` JWT helper,
the same ``brand_id`` seed fixture, and crucially the same
context-managed ``with TestClient(app) as c:`` client — a bare
``TestClient(app)`` spins a separate BlockingPortal event loop and the
DI Singleton asyncpg engine then binds to a closed loop, so PUT-then-GET
(and here POST-then-poll) breaks. The only addition is overriding the
app's ``BrandContainer.analyze_service`` with an ``AnalyzeJobService``
whose ``_extract`` is a deterministic in-process fake returning a real
``cortex_brand_extract.types.BrandProfile`` (no network, no mock.patch),
mirroring how SP-1 overrides the brand ``service`` provider.
"""

from __future__ import annotations

import contextlib
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from cortex_brand_extract.types import BrandProfile as SP2Profile
from cortex_brand_extract.types import Category, ExtractionMeta
from fastapi.testclient import TestClient

from cortex_api.app.dependencies.auth import authenticated_user
from cortex_api.core.identifiers import uuid7
from cortex_api.infra.container import Container as InfraContainer
from cortex_api.main import create_app
from cortex_api.service.brand.analyze_config import AnalyzeConfig
from cortex_api.service.brand.analyze_service import AnalyzeJobService
from cortex_api.service.brand.repo.analysis_job_repo import AnalysisJobRepo
from cortex_api.service.brand.repo.profile_repo import BrandProfileRepo
from cortex_api.service.brand_identity.model.brand import Brand
from cortex_api.service.identity.model.authed_user import AuthedUser

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
async def _schema():
    from sqlmodel import SQLModel

    db = InfraContainer()._database_client_factory()
    async with db.session() as s:
        conn = await s.connection()
        await conn.run_sync(SQLModel.metadata.create_all)


def _authed(brand_id, caps):
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


async def _fake_extract(url: str, **_: object) -> SP2Profile:
    """Deterministic in-process SP-2 extractor — no network, no mock.patch.

    Returns a real ``cortex_brand_extract.types.BrandProfile`` so the
    SP-2 -> SP-1 mapper and ``mark_succeeded(cost_usd=...)`` run exactly
    as they do in production.
    """
    return SP2Profile(
        url=url,
        name="Acme Test Co",
        category=Category(value="SaaS", confidence=90, alternatives=["Software"]),
        region=["TW"],
        extraction_meta=ExtractionMeta(
            tier="lite",
            model="fake-test-model",
            cost_usd=0.0,
            extracted_at=datetime.now(tz=UTC),
            warnings=[],
        ),
    )


async def _seed_brand(db, bid) -> None:
    async with db.session() as s:
        s.add(Brand(id=bid, display_name="ApiCo"))
        await s.flush()


@pytest.fixture
def make_client():
    """Yield a ``make_client(*, jwt_brand_id=None)`` factory cm.

    Each invocation mirrors ``test_brand_profile_api.py``'s ``_client``
    cm: build the real app via ``create_app()``, override
    ``authenticated_user`` with a brand-scoped ``AuthedUser``, and yield
    inside ``with TestClient(app) as c:`` (NOT a bare ``TestClient(app)``).

    Additionally overrides the app's ``BrandContainer.analyze_service``
    with an ``AnalyzeJobService`` bound to the SAME ``DatabaseClient``
    the routes use (resolved after the app is built, post
    singleton-reset) so the in-process worker's writes are visible to
    the GET poll. ``jwt_brand_id`` splits the JWT's brand from the URL's
    brand to drive the cross-tenant rejection path, exactly as SP-1 does.
    """
    from cortex_api import main as _main

    overridden = False

    @contextlib.contextmanager
    def _factory(*, jwt_brand_id=None, caps=None):
        nonlocal overridden
        app = create_app()

        bid = uuid7()
        db = _main._brand_container.database_client()
        fake_service = AnalyzeJobService(
            database_client=db,
            analysis_job_repo=AnalysisJobRepo(),
            profile_repo=BrandProfileRepo(),
            config=AnalyzeConfig(),
            # tracker + composer come from BrandContainer's wired graph —
            # main.py supplies the placement-owned singletons via
            # ``BrandContainer(tracker=..., settings_repo=...)`` so we don't
            # need to reach into ``_placement_container`` here.
            composer=_main._brand_container.composer(),
            tracker=_main._brand_container.tracker(),
            _extract=_fake_extract,
        )
        _main._brand_container.analyze_service.override(fake_service)
        overridden = True

        token_brand = jwt_brand_id if jwt_brand_id is not None else bid
        token_caps = caps if caps is not None else ["view_brand_dashboard", "edit_brand_settings"]
        app.dependency_overrides[authenticated_user] = lambda: _authed(
            token_brand,
            token_caps,
        )

        with TestClient(app) as c:
            # Seed the brand row through the same DB client the app uses,
            # inside the TestClient portal loop (the cm has started it).
            c.portal.call(_seed_brand, db, bid)
            yield c, bid

    try:
        yield _factory
    finally:
        if overridden:
            _main._brand_container.analyze_service.reset_override()


def test_post_analyze_202_then_get_succeeds(make_client) -> None:
    with make_client() as (client, brand_id):
        r = client.post(f"/v1/brand/{brand_id}/profile/analyze", json={"url": "acme.test"})
        assert r.status_code == 202, r.text
        job_id = r.json()["job_id"]
        body = {}
        for _ in range(50):
            g = client.get(f"/v1/brand/{brand_id}/profile/analyze/{job_id}")
            assert g.status_code == 200, g.text
            body = g.json()
            if body["status"] in ("succeeded", "failed"):
                break
        assert body["status"] == "succeeded", body
        assert body["profile"]["name"]


def test_post_analyze_without_capability_403(make_client) -> None:
    """Authed-but-under-privileged JWT may not start an analyze job.

    The POST is gated by `requires_brand_capability(EDIT_BRAND_SETTINGS)`.
    A token correctly scoped to the brand but missing `edit_brand_settings`
    must be refused: `requires_brand_capability` raises `ForbiddenError`,
    mapped to HTTP 403 by `app/exception_handlers.py`. Mirrors SP-1's
    `test_put_without_capability_403`.
    """
    with make_client(caps=["view_brand_dashboard"]) as (client, brand_id):
        r = client.post(f"/v1/brand/{brand_id}/profile/analyze", json={"url": "acme.test"})
        assert r.status_code == 403, r.text


def test_get_cross_tenant_job_not_leaked(make_client) -> None:
    with make_client() as (client, brand_id):
        r = client.post(f"/v1/brand/{brand_id}/profile/analyze", json={"url": "a"})
        job_id = r.json()["job_id"]
    with make_client(jwt_brand_id=uuid4()) as (client2, other_brand):
        g = client2.get(f"/v1/brand/{other_brand}/profile/analyze/{job_id}")
        assert 400 <= g.status_code < 500, g.text
        assert g.json().get("profile") is None
