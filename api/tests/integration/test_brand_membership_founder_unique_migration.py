"""Round-trip migration test for dropping ``brand_membership_founder_uniq`` (7ab199ba95a2).

This migration DROPS the partial unique index on upgrade, so the round-trip is
inverted relative to an additive migration:

- at head                        → index ABSENT  (dropped by 7ab199ba95a2)
- downgrade a2b3c4d5e6f7          → index PRESENT (recreated by downgrade())
- upgrade head                   → index ABSENT  again

The ``finally`` block returns the shared session DB to head no matter what —
the autouse ``_migrations_applied`` fixture is session-scoped, so leaving the
DB downgraded would cascade misleading failures into later integration tests.
Upgrade-to-head when already at head is a no-op, so the guard is always safe.
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

_INDEX = "brand_membership_founder_uniq"
_PRIOR = "a2b3c4d5e6f7"  # down_revision of 7ab199ba95a2


def _alembic_cfg() -> Config:
    from alembic.config import Config

    api_root = Path(__file__).resolve().parents[2]  # api/
    cfg = Config(str(api_root / "alembic.ini"))
    cfg.set_main_option("script_location", str(api_root / "alembic"))
    return cfg


def _index_names(engine: sa.Engine, table: str) -> set[str]:
    with engine.connect() as conn:
        return {ix["name"] for ix in inspect(conn).get_indexes(table)}


def test_drop_founder_unique_round_trips(db_url: str) -> None:
    """upgrade head → downgrade a2b3c4d5e6f7 → upgrade head — all succeed.

    Asserts the founder-unique index is absent at head, present after downgrade
    (recreated), and absent again after re-upgrade.
    """
    from alembic import command

    cfg = _alembic_cfg()
    sync_url = db_url.replace("+asyncpg", "+psycopg")
    engine = sa.create_engine(sync_url)
    try:
        command.upgrade(cfg, "head")
        assert _INDEX not in _index_names(engine, "brand_membership"), (
            "founder-unique index must be ABSENT at head (dropped by 7ab199ba95a2)"
        )

        command.downgrade(cfg, _PRIOR)
        assert _INDEX in _index_names(engine, "brand_membership"), (
            "founder-unique index must be PRESENT after downgrade (recreated)"
        )

        command.upgrade(cfg, "head")
        assert _INDEX not in _index_names(engine, "brand_membership"), (
            "founder-unique index must be ABSENT again after re-upgrade"
        )
    finally:
        command.upgrade(cfg, "head")
        engine.dispose()
