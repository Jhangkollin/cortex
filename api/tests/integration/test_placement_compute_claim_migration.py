"""Round-trip alembic test for placement_compute_claim (COR-75).

Mirrors test_placement_schema_migration.py's pattern: SYNC test bodies,
sync engine via +psycopg, finally-guard back to head.
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

PRE_CLAIM_REV = "e65e2383b6c5"  # COR-57 head, parent of placement_compute_claim


def _alembic_cfg() -> Config:
    from alembic.config import Config

    api_root = Path(__file__).resolve().parents[2]  # api/
    alembic_ini = api_root / "alembic.ini"
    cfg = Config(str(alembic_ini))
    cfg.set_main_option("script_location", str(api_root / "alembic"))
    return cfg


def test_round_trip_upgrade_downgrade_upgrade(db_url: str) -> None:
    from alembic import command

    cfg = _alembic_cfg()
    sync_url = db_url.replace("+asyncpg", "+psycopg")
    engine = sa.create_engine(sync_url)
    try:
        command.upgrade(cfg, "head")
        with engine.connect() as conn:
            assert "placement_compute_claim" in inspect(conn).get_table_names()

        # Downgrade one step (removes placement_compute_claim)
        command.downgrade(cfg, PRE_CLAIM_REV)
        with engine.connect() as conn:
            assert "placement_compute_claim" not in inspect(conn).get_table_names()

        # Re-upgrade back to head
        command.upgrade(cfg, "head")
        with engine.connect() as conn:
            assert "placement_compute_claim" in inspect(conn).get_table_names()
    finally:
        command.upgrade(cfg, "head")
        engine.dispose()


def test_placement_compute_claim_columns(db_url: str) -> None:
    """Schema-level assertions per the COR-75 AC."""
    from alembic import command

    cfg = _alembic_cfg()
    sync_url = db_url.replace("+asyncpg", "+psycopg")
    engine = sa.create_engine(sync_url)
    try:
        command.upgrade(cfg, "head")
        with engine.connect() as conn:
            cols = {c["name"]: c for c in inspect(conn).get_columns("placement_compute_claim")}

        # Required columns + nullability
        assert "publisher_id" in cols
        assert "article_url_hash" in cols
        assert "claim_id" in cols
        assert "agent_ws_request_id" in cols and cols["agent_ws_request_id"]["nullable"] is False
        assert "brand_ids" in cols
        assert "claimed_at" in cols
        assert "expires_at" in cols
        assert "completed_at" in cols and cols["completed_at"]["nullable"] is True
        assert "placement_audit_id" in cols and cols["placement_audit_id"]["nullable"] is True
        assert "status" in cols and cols["status"]["nullable"] is False
        assert "created_at" in cols
        assert "updated_at" in cols
    finally:
        engine.dispose()


def test_placement_compute_claim_primary_key(db_url: str) -> None:
    """PK is (publisher_id, article_url_hash)."""
    from alembic import command

    cfg = _alembic_cfg()
    sync_url = db_url.replace("+asyncpg", "+psycopg")
    engine = sa.create_engine(sync_url)
    try:
        command.upgrade(cfg, "head")
        with engine.connect() as conn:
            pk = inspect(conn).get_pk_constraint("placement_compute_claim")
        assert pk["constrained_columns"] == ["publisher_id", "article_url_hash"]
    finally:
        engine.dispose()
