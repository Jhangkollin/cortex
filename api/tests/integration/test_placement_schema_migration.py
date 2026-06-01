"""Round-trip alembic test for the placement schema migration.

AC-mandated by COR-55. Mirrors the structure of
``test_brand_onboarded_at_migration.py``:

* ``test_upgrade_downgrade_upgrade_round_trips`` — head → downgrade to
  ``b8c9d0e1f2a3`` (the revision just before placement) → head all succeed,
  and the placement tables are absent at the bottom of the round-trip.
* ``test_placement_tables_present_at_head`` — after head, all four tables
  exist and the key constraint columns are shaped correctly (notably
  ``overrides_mask`` is JSONB NOT NULL with default ``'{}'::jsonb``).

Both ``finally``-guard the shared session DB back to head no matter what,
so a downgrade left mid-run cannot cascade misleading failures into other
integration tests in the same pytest session.
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

PRE_PLACEMENT_REV = "b8c9d0e1f2a3"  # weekly_questions, head before placement


def _alembic_cfg() -> Config:
    from alembic.config import Config

    api_root = Path(__file__).resolve().parents[2]  # api/
    alembic_ini = api_root / "alembic.ini"
    cfg = Config(str(alembic_ini))
    cfg.set_main_option("script_location", str(api_root / "alembic"))
    return cfg


PLACEMENT_TABLES = (
    "brand_placement_settings",
    "brand_publisher_scope",
    "publisher_placement_config",
    "placement_audit",
)


def test_upgrade_downgrade_upgrade_round_trips(db_url: str) -> None:
    from alembic import command

    cfg = _alembic_cfg()
    sync_url = db_url.replace("+asyncpg", "+psycopg")
    engine = sa.create_engine(sync_url)
    try:
        command.upgrade(cfg, "head")

        # --- downgrade past placement ---
        command.downgrade(cfg, PRE_PLACEMENT_REV)
        with engine.connect() as conn:
            tables_after_down = set(inspect(conn).get_table_names())
        for tbl in PLACEMENT_TABLES:
            assert tbl not in tables_after_down, f"{tbl} should not exist after downgrade to {PRE_PLACEMENT_REV}"

        # --- upgrade back to head ---
        command.upgrade(cfg, "head")
        with engine.connect() as conn:
            tables_after_up = set(inspect(conn).get_table_names())
        for tbl in PLACEMENT_TABLES:
            assert tbl in tables_after_up, f"{tbl} must exist after upgrade head"
    finally:
        command.upgrade(cfg, "head")
        engine.dispose()


def test_placement_tables_present_at_head(db_url: str) -> None:
    """After head, the four placement tables exist and the schema-critical
    columns have the right shape (overrides_mask JSONB NOT NULL with
    '{}'::jsonb default — D1 design contract). Also covers the
    post-review additions: composed_at column, the four placement_audit
    indexes."""
    from alembic import command

    cfg = _alembic_cfg()
    sync_url = db_url.replace("+asyncpg", "+psycopg")
    engine = sa.create_engine(sync_url)
    try:
        command.upgrade(cfg, "head")

        with engine.connect() as conn:
            for tbl in PLACEMENT_TABLES:
                assert tbl in inspect(conn).get_table_names(), f"{tbl} missing after head"

            settings_cols = {c["name"]: c for c in inspect(conn).get_columns("brand_placement_settings")}
            assert "overrides_mask" in settings_cols, "overrides_mask column missing"
            ov = settings_cols["overrides_mask"]
            assert ov["nullable"] is False, "overrides_mask must be NOT NULL"
            # SQLAlchemy reflects server_default as a string like
            # "'{}'::jsonb" (postgres canonical form) — substring-check tolerates
            # quoting variation while proving the default is in place.
            assert "{}" in str(ov.get("default") or ""), (
                f"overrides_mask must default to '{{}}'::jsonb, got: {ov.get('default')!r}"
            )

            # status NOT NULL DEFAULT 'active'
            status = settings_cols["status"]
            assert status["nullable"] is False
            assert "active" in str(status.get("default") or "")

            # composed_at — nullable per design (the composer sets it
            # when a successful derivation finishes; NULL means
            # "not-yet-placement-ready").
            assert "composed_at" in settings_cols, "composed_at column missing"
            assert settings_cols["composed_at"]["nullable"] is True, "composed_at must be nullable"

            audit_indexes = {idx["name"] for idx in inspect(conn).get_indexes("placement_audit")}
            for expected in (
                "ix_placement_audit_brand_id_created_at",
                "ix_placement_audit_publisher_id_created_at",
                "ix_placement_audit_trace_id",
                "ix_placement_audit_article_url_hash",
            ):
                assert expected in audit_indexes, f"{expected} missing on placement_audit"
    finally:
        command.upgrade(cfg, "head")
        engine.dispose()
