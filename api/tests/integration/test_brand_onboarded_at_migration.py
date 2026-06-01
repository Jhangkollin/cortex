"""Round-trip migration tests for brand.onboarded_at.

Two tests, deliberately split for clearer CI failure attribution:

- ``test_upgrade_downgrade_upgrade_round_trips`` — the migration chain
  upgrade head → downgrade e5f6a7b8c9d0 → upgrade head all succeed, and the
  column is absent at the bottom of the round-trip.
- ``test_onboarded_at_column_present_and_nullable`` — after head, the
  ``brand.onboarded_at`` column exists and is nullable.

Both ``finally``-guard the shared session DB back to head no matter what.
The ``_migrations_applied`` fixture is session-scoped autouse, so a test
that left the DB at ``e5f6a7b8c9d0`` would cascade misleading failures into
every later integration test in the same pytest session. Upgrade-to-head
when already at head is a no-op, so the guard is safe on every path.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
import sqlalchemy as sa
from sqlalchemy import inspect

if TYPE_CHECKING:  # pragma: no cover - typing only
    from alembic.config import Config

pytestmark = pytest.mark.integration


def _alembic_cfg() -> Config:
    """Return an Alembic Config pointed at the repo's alembic.ini.

    Mirrors the ``_alembic_upgrade`` helper in conftest.py — same root
    discovery logic so the same env.py / CORE_DB_* path is exercised.
    """
    from alembic.config import Config

    api_root = Path(__file__).resolve().parents[2]  # api/
    alembic_ini = api_root / "alembic.ini"
    cfg = Config(str(alembic_ini))
    cfg.set_main_option("script_location", str(api_root / "alembic"))
    return cfg


def test_upgrade_downgrade_upgrade_round_trips(db_url: str) -> None:
    """upgrade head → downgrade e5f6a7b8c9d0 → upgrade head — all succeed.

    Asserts the column is absent at the bottom of the round-trip. The
    ``finally`` block guarantees the shared session DB is returned to head
    even if an assertion fails, so a failure here cannot cascade into other
    integration tests in the same session.
    """
    from alembic import command

    cfg = _alembic_cfg()
    sync_url = db_url.replace("+asyncpg", "+psycopg")
    engine = sa.create_engine(sync_url)
    try:
        # Ensure DB is at head before starting the round-trip (self-contained
        # even when this test runs in isolation; no-op under conftest).
        command.upgrade(cfg, "head")

        # --- downgrade to the revision just before our migration ---
        command.downgrade(cfg, "e5f6a7b8c9d0")
        with engine.connect() as conn:
            col_names_after_down = {c["name"] for c in inspect(conn).get_columns("brand")}
        assert "onboarded_at" not in col_names_after_down, (
            "onboarded_at column should not exist after downgrade to e5f6a7b8c9d0"
        )

        # --- upgrade back to head ---
        command.upgrade(cfg, "head")
        with engine.connect() as conn:
            col_names_after_up = {c["name"] for c in inspect(conn).get_columns("brand")}
        assert "onboarded_at" in col_names_after_up, "onboarded_at column must exist after upgrade head"
    finally:
        # Guarantee the shared session DB is back at head no matter what —
        # idempotent no-op if already there, repair if an assertion above
        # left it downgraded.
        command.upgrade(cfg, "head")
        engine.dispose()


def test_onboarded_at_column_present_and_nullable(db_url: str) -> None:
    """After head, brand.onboarded_at exists and is nullable.

    NULL legitimately means "not onboarded", so the column must permit NULL.
    Uses a sync (psycopg3 ``+psycopg``) engine for inspect calls — no asyncpg
    or event-loop wrangling needed for a schema assertion.
    """
    from alembic import command

    cfg = _alembic_cfg()
    sync_url = db_url.replace("+asyncpg", "+psycopg")
    engine = sa.create_engine(sync_url)
    try:
        command.upgrade(cfg, "head")
        with engine.connect() as conn:
            cols = {c["name"]: c for c in inspect(conn).get_columns("brand")}

        assert "onboarded_at" in cols, "onboarded_at column must exist after upgrade head"
        col = cols["onboarded_at"]
        assert col["nullable"] is True, "onboarded_at must be nullable (NULL = not onboarded)"
    finally:
        # Symmetric finally-guard: never leave the shared session DB off head.
        command.upgrade(cfg, "head")
        engine.dispose()
