from __future__ import annotations

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

pytestmark = pytest.mark.integration


def _cfg(db_url: str) -> Config:
    api_root = Path(__file__).resolve().parents[2]
    cfg = Config(str(api_root / "alembic.ini"))
    cfg.set_main_option("script_location", str(api_root / "alembic"))
    cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg


def test_brand_report_migration_round_trips(db_url: str) -> None:
    cfg = _cfg(db_url)
    try:
        command.upgrade(cfg, "head")
        command.downgrade(cfg, "-1")  # exercises the ENUM drop
        command.upgrade(cfg, "head")  # fails here if the enum wasn't dropped
        sync_url = db_url.replace("+asyncpg", "+psycopg")
        eng = create_engine(sync_url)
        try:
            inspector = inspect(eng)
            assert "brand_report" in inspector.get_table_names()
            index_names = {idx["name"] for idx in inspector.get_indexes("brand_report")}
            assert "ix_brand_report_brand_id" in index_names
            assert "ix_brand_report_report_id" in index_names
            assert "ix_brand_report_brand_id_status" in index_names
            assert "uq_brand_report_one_current" in index_names
            uc_names = {uc["name"] for uc in inspector.get_unique_constraints("brand_report")}
            assert "uq_brand_report_brand_id_version" in uc_names
            # get_enums is a PostgreSQL-dialect Inspector method (not on the
            # generic Inspector type stub).
            enum_names = {enum["name"] for enum in inspector.get_enums()}  # type: ignore[attr-defined]
            assert "brandreportstatus" in enum_names
        finally:
            eng.dispose()
    finally:
        # Leave the shared session DB at head even if a mid-test step failed.
        command.upgrade(cfg, "head")
