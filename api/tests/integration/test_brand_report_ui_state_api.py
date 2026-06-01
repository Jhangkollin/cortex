"""Integration tests for brand_report ui-state endpoints (COR-82).

Tests the four endpoints:
  GET  /v1/brand/{brand_id}/report/ui-state
  POST /v1/brand/{brand_id}/report/ui-state/arm
  POST /v1/brand/{brand_id}/report/ui-state/celebrate-consume
  POST /v1/brand/{brand_id}/report/ui-state/hero-dismiss

Plus the migration round-trip test (upgrade → downgrade → upgrade) for the
`brand_report_ui_state` table.

Requires Postgres (docker-compose up -d) — skipped by ``pytest -m "not integration"``.
"""

from __future__ import annotations

import contextlib
import uuid
from collections.abc import Generator
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest
from alembic import command
from alembic.config import Config as AlembicConfig
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect

from cortex_api.app.dependencies.auth import authenticated_user
from cortex_api.core.identifiers import uuid7
from cortex_api.infra.container import Container as InfraContainer
from cortex_api.infra.database_client import DatabaseClient
from cortex_api.main import create_app
from cortex_api.service.brand_identity.model.brand import Brand
from cortex_api.service.brand_report.repo.report_repo import BrandReportRepo
from cortex_api.service.brand_report.repo.ui_state_repo import ReportUiStateRepo
from cortex_api.service.brand_report.ui_state_service import BrandReportUiStateService
from cortex_api.service.identity.model.authed_user import AuthedUser

pytestmark = pytest.mark.integration


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


async def _seed_brand(db: DatabaseClient, bid: UUID) -> None:
    async with db.session() as s:
        s.add(Brand(id=bid, display_name="UiStateTestCo"))
        await s.flush()
        await s.commit()


# ---------------------------------------------------------------------------
# make_client fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def make_client() -> Generator[Any, None, None]:
    """Yield a ``make_client(*, jwt_brand_id=None, caps=None)`` context manager."""
    from cortex_api import main as _main

    overridden = False

    @contextlib.contextmanager
    def _factory(
        *,
        jwt_brand_id: UUID | None = None,
        caps: list[str] | None = None,
    ) -> Generator[tuple[TestClient, UUID], None, None]:
        nonlocal overridden
        app = create_app()

        bid = uuid7()
        db = _main._brand_report_container.database_client()

        real_ui_state_service = BrandReportUiStateService(
            database_client=db,
            ui_state_repo=ReportUiStateRepo(),
            report_repo=BrandReportRepo(),
        )
        _main._brand_report_container.ui_state_service.override(real_ui_state_service)
        overridden = True

        token_brand = jwt_brand_id if jwt_brand_id is not None else bid
        token_caps = caps if caps is not None else ["view_brand_dashboard"]
        app.dependency_overrides[authenticated_user] = lambda: _authed(token_brand, token_caps)

        with TestClient(app) as c:
            from anyio.from_thread import BlockingPortal

            portal: BlockingPortal = c.portal  # type: ignore[assignment]
            portal.call(_seed_brand, db, bid)
            yield c, bid

    try:
        yield _factory
    finally:
        if overridden:
            _main._brand_report_container.ui_state_service.reset_override()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_get_ui_state_defaults(make_client: Any) -> None:
    """Fresh brand has celebrate_pending=false, hero_dismissed=false."""
    with make_client() as (client, brand_id):
        r = client.get(f"/v1/brand/{brand_id}/report/ui-state")
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["celebratePending"] is False
        assert body["heroDismissed"] is False


def test_ui_state_route_not_shadowed_by_report_id(make_client: Any) -> None:
    """REGRESSION LOCK (COR-82 review item 1): the static `.../report/ui-state`
    GET must resolve to the ui-state handler, NOT be captured by the
    parameterized `.../report/{report_id}` route as report_id='ui-state'.

    If the routes are ever reordered (parameterized before static), Starlette
    binds report_id='ui-state' → the report read path runs → 404 (no such
    report). A 200 with the ui-state body shape proves the static route wins.
    """
    with make_client() as (client, brand_id):
        r = client.get(f"/v1/brand/{brand_id}/report/ui-state")
        assert r.status_code == 200, r.text
        # Body shape is the ui-state DTO (celebratePending/heroDismissed),
        # NOT a ReportEnvelope (which would carry reportId/status/report).
        body = r.json()
        assert "celebratePending" in body
        assert "heroDismissed" in body
        assert "reportId" not in body


def test_arm_then_get(make_client: Any) -> None:
    """After arm, celebratePending becomes true."""
    with make_client() as (client, brand_id):
        r = client.post(f"/v1/brand/{brand_id}/report/ui-state/arm")
        assert r.status_code == 204, r.text

        r2 = client.get(f"/v1/brand/{brand_id}/report/ui-state")
        assert r2.json()["celebratePending"] is True


def test_arm_consume_resets(make_client: Any) -> None:
    """arm → consume results in celebratePending == false again."""
    with make_client() as (client, brand_id):
        client.post(f"/v1/brand/{brand_id}/report/ui-state/arm")
        r = client.post(f"/v1/brand/{brand_id}/report/ui-state/celebrate-consume")
        assert r.status_code == 204, r.text

        r2 = client.get(f"/v1/brand/{brand_id}/report/ui-state")
        assert r2.json()["celebratePending"] is False


def test_consume_idempotent(make_client: Any) -> None:
    """Calling celebrate-consume twice is safe."""
    with make_client() as (client, brand_id):
        r1 = client.post(f"/v1/brand/{brand_id}/report/ui-state/celebrate-consume")
        r2 = client.post(f"/v1/brand/{brand_id}/report/ui-state/celebrate-consume")
        assert r1.status_code == 204
        assert r2.status_code == 204


def test_arm_after_consume_is_noop(make_client: Any) -> None:
    """ "arm once" semantic: re-arming after a consume must NOT resurrect the
    celebration (so re-running onboarding can't show a dismissed modal again)."""
    with make_client() as (client, brand_id):
        client.post(f"/v1/brand/{brand_id}/report/ui-state/arm")
        client.post(f"/v1/brand/{brand_id}/report/ui-state/celebrate-consume")
        # Re-run onboarding → arm again, but it's been consumed → stays false.
        client.post(f"/v1/brand/{brand_id}/report/ui-state/arm")

        r = client.get(f"/v1/brand/{brand_id}/report/ui-state")
        assert r.json()["celebratePending"] is False


def test_hero_dismiss(make_client: Any) -> None:
    """After hero-dismiss, heroDismissed becomes true."""
    with make_client() as (client, brand_id):
        r = client.post(f"/v1/brand/{brand_id}/report/ui-state/hero-dismiss")
        assert r.status_code == 204, r.text

        r2 = client.get(f"/v1/brand/{brand_id}/report/ui-state")
        assert r2.json()["heroDismissed"] is True


def test_ui_state_requires_capability(make_client: Any) -> None:
    """Missing VIEW_BRAND_DASHBOARD → 403 on ui-state GET."""
    with make_client(caps=["edit_brand_settings"]) as (client, brand_id):
        r = client.get(f"/v1/brand/{brand_id}/report/ui-state")
        assert r.status_code == 403, r.text


def test_cross_tenant_rejected(make_client: Any) -> None:
    """JWT scoped to different brand → 4xx from active_brand dep."""
    other = uuid.uuid4()
    with make_client(jwt_brand_id=other) as (client, seeded_bid):
        r = client.get(f"/v1/brand/{seeded_bid}/report/ui-state")
        assert 400 <= r.status_code < 500, r.text


# ---------------------------------------------------------------------------
# Migration round-trip test
# ---------------------------------------------------------------------------


def _alembic_cfg(db_url: str) -> AlembicConfig:
    """Build an Alembic Config rooted at the api/ dir via __file__ resolution.

    Mirrors ``tests/integration/test_brand_report_migration.py::_cfg`` so the
    test is machine-independent (no hardcoded cwd — works on CI / any clone).
    ``parents[2]`` from ``tests/integration/<file>.py`` is the api/ root.
    """
    api_root = Path(__file__).resolve().parents[2]
    cfg = AlembicConfig(str(api_root / "alembic.ini"))
    cfg.set_main_option("script_location", str(api_root / "alembic"))
    cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg


def test_migration_round_trip(db_url: str) -> None:
    """Alembic upgrade → downgrade → upgrade does not error.

    Validates that a2b3c4d5e6f7 (brand_report_ui_state table) is round-trip
    safe per CLAUDE.md migration rules. ``downgrade('-1')`` drops the table;
    the second ``upgrade('head')`` would fail if the downgrade left the schema
    in a bad state. Also asserts the new table exists with a CASCADE FK and
    that the old `report_*` columns are NOT on `brand`. Requires a live DB.
    """
    cfg = _alembic_cfg(db_url)
    try:
        command.upgrade(cfg, "head")
        command.downgrade(cfg, "-1")  # drops brand_report_ui_state
        command.upgrade(cfg, "head")  # re-creates; fails here if downgrade was wrong
        sync_url = db_url.replace("+asyncpg", "+psycopg")
        eng = create_engine(sync_url)
        try:
            inspector = inspect(eng)
            # The owned table exists with the expected columns.
            assert "brand_report_ui_state" in inspector.get_table_names()
            cols = {col["name"] for col in inspector.get_columns("brand_report_ui_state")}
            assert {"brand_id", "celebrate_pending", "hero_dismissed", "celebrate_consumed"} <= cols
            # FK → brand.id with ON DELETE CASCADE.
            fks = inspector.get_foreign_keys("brand_report_ui_state")
            assert any(
                fk["referred_table"] == "brand"
                and fk["constrained_columns"] == ["brand_id"]
                and (fk.get("options") or {}).get("ondelete", "").upper() == "CASCADE"
                for fk in fks
            ), fks
            # The old per-brand columns must be gone from `brand`.
            brand_cols = {col["name"] for col in inspector.get_columns("brand")}
            assert "report_celebrate_pending" not in brand_cols
            assert "report_hero_dismissed" not in brand_cols
        finally:
            eng.dispose()
    finally:
        # Leave the shared session DB at head even if a mid-test step failed.
        command.upgrade(cfg, "head")
