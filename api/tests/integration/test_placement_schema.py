"""Integration tests for placement schema constraints.

These exercise behaviour that only a real Postgres can enforce: FK ON
DELETE, ENUM type bounds, JSONB server-defaults, composite PKs. They are
the AC-mandated "unit tests for table constraints" (ticket COR-55) — in
the cortex convention, constraint tests live under integration/ because
they need the actual constraint engine.

Note on ENUM assertions: asyncpg surfaces enum-bound violations as
``InvalidTextRepresentationError``, which the SQLAlchemy asyncpg dialect
wraps as ``DBAPIError`` (no specific ``DataError`` downcast). We pair the
class with ``match="invalid input value for enum"`` so the assertion
remains red against unrelated DBAPIErrors — including the
"relation does not exist" ProgrammingError that surfaces before the
migration has been applied.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError

from cortex_api.core.identifiers import uuid7
from cortex_api.infra.container import Container as InfraContainer
from cortex_api.service.brand_identity.model.brand import Brand
from cortex_api.service.placement.model.publisher_config import (
    PublisherPlacementConfig,
)
from cortex_api.service.placement.model.scope import BrandPublisherScope
from cortex_api.service.placement.model.settings import BrandPlacementSettings

pytestmark = pytest.mark.integration


@pytest.fixture
def database_client():
    return InfraContainer()._database_client_factory()


# --------------------------------------------------------------------------
# brand_placement_settings
# --------------------------------------------------------------------------


async def test_placement_settings_fk_rejects_orphan_brand(database_client) -> None:
    """Inserting a settings row for a non-existent brand must raise — this
    is the constraint that keeps brand_placement_settings 1:1 with brand."""
    async with database_client.session() as s:
        s.add(BrandPlacementSettings(brand_id=uuid4()))
        with pytest.raises(IntegrityError):
            await s.flush()
        await s.rollback()


async def test_placement_settings_pk_unique_per_brand(database_client) -> None:
    """brand_id is PK ⇒ a second settings row for the same brand_id raises."""
    bid = uuid7()
    async with database_client.session() as s:
        s.add(Brand(id=bid, display_name="OneRow"))
        await s.flush()
        s.add(BrandPlacementSettings(brand_id=bid))
        await s.flush()

    async with database_client.session() as s:
        s.add(BrandPlacementSettings(brand_id=bid))
        with pytest.raises(IntegrityError):
            await s.flush()
        await s.rollback()


async def test_overrides_mask_db_default_is_empty_dict(database_client) -> None:
    """A raw INSERT that omits overrides_mask reads back as {} per D1
    and status reads back as 'active'. composed_at reads back as NULL
    because the composer hasn't run yet — that's the canonical
    "not-yet-placement-ready" signal (Issue 2 from PR #51 review).

    Raw SQL deliberately bypasses SQLModel's Python-side default to prove
    the DB-level ``server_default '{}'::jsonb`` is in place — that's what
    seed scripts (COR-60) and ``psql`` fixups rely on.
    """
    bid = uuid7()
    async with database_client.session() as s:
        s.add(Brand(id=bid, display_name="DefaultMask"))
        await s.flush()
        await s.execute(text("INSERT INTO brand_placement_settings (brand_id) VALUES (:bid)").bindparams(bid=bid))
        result = await s.execute(
            text(
                "SELECT overrides_mask, status, composed_at FROM brand_placement_settings WHERE brand_id = :bid"
            ).bindparams(bid=bid)
        )
        overrides_mask, status, composed_at = result.one()
    assert overrides_mask == {}
    assert status == "active"
    assert composed_at is None


async def test_placement_mode_enum_rejects_invalid_value(database_client) -> None:
    bid = uuid7()
    async with database_client.session() as s:
        s.add(Brand(id=bid, display_name="ModeBad"))
        await s.flush()
        with pytest.raises(DBAPIError, match="invalid input value for enum"):
            await s.execute(
                text("INSERT INTO brand_placement_settings (brand_id, mode) VALUES (:bid, 'bogus')").bindparams(bid=bid)
            )
        await s.rollback()


async def test_placement_settings_status_enum_rejects_invalid_value(database_client) -> None:
    bid = uuid7()
    async with database_client.session() as s:
        s.add(Brand(id=bid, display_name="StatusBad"))
        await s.flush()
        with pytest.raises(DBAPIError, match="invalid input value for enum"):
            await s.execute(
                text("INSERT INTO brand_placement_settings (brand_id, status) VALUES (:bid, 'archived')").bindparams(
                    bid=bid
                )
            )
        await s.rollback()


# --------------------------------------------------------------------------
# brand_publisher_scope
# --------------------------------------------------------------------------


async def test_brand_publisher_scope_fk_rejects_orphan_brand(database_client) -> None:
    async with database_client.session() as s:
        s.add(BrandPublisherScope(brand_id=uuid4(), publisher_id=uuid4()))
        with pytest.raises(IntegrityError):
            await s.flush()
        await s.rollback()


async def test_brand_publisher_scope_composite_pk(database_client) -> None:
    """PK = (brand_id, publisher_id). Different publishers for the same
    brand are allowed; the same pair twice raises."""
    bid = uuid7()
    pub_a = uuid4()
    pub_b = uuid4()
    async with database_client.session() as s:
        s.add(Brand(id=bid, display_name="ScopePK"))
        await s.flush()
        s.add(BrandPublisherScope(brand_id=bid, publisher_id=pub_a))
        s.add(BrandPublisherScope(brand_id=bid, publisher_id=pub_b))
        await s.flush()

    async with database_client.session() as s:
        s.add(BrandPublisherScope(brand_id=bid, publisher_id=pub_a))
        with pytest.raises(IntegrityError):
            await s.flush()
        await s.rollback()


async def test_placement_scope_status_enum_rejects_invalid_value(database_client) -> None:
    bid = uuid7()
    async with database_client.session() as s:
        s.add(Brand(id=bid, display_name="ScopeEnumBad"))
        await s.flush()
        with pytest.raises(DBAPIError, match="invalid input value for enum"):
            await s.execute(
                text(
                    "INSERT INTO brand_publisher_scope (brand_id, publisher_id, status) VALUES (:bid, :pub, 'paused')"
                ).bindparams(bid=bid, pub=uuid4())
            )
        await s.rollback()


# --------------------------------------------------------------------------
# publisher_placement_config
# --------------------------------------------------------------------------


async def test_publisher_placement_config_pk_unique(database_client) -> None:
    pub = uuid4()
    async with database_client.session() as s:
        s.add(PublisherPlacementConfig(publisher_id=pub))
        await s.flush()

    async with database_client.session() as s:
        s.add(PublisherPlacementConfig(publisher_id=pub))
        with pytest.raises(IntegrityError):
            await s.flush()
        await s.rollback()


# --------------------------------------------------------------------------
# placement_audit
# --------------------------------------------------------------------------


async def test_placement_audit_losing_candidates_db_default_empty_list(database_client) -> None:
    """Raw INSERT without losing_candidates → server_default '[]'::jsonb."""
    aid = uuid7()
    brand_id = uuid4()
    pub = uuid4()
    async with database_client.session() as s:
        await s.execute(
            text(
                """
                INSERT INTO placement_audit
                    (id, brand_id, publisher_id, article_url, article_url_hash,
                     question_text, answer_text, placement_position, rationale,
                     selection_weight, trace_id, parent_trace_id)
                VALUES
                    (:id, :brand_id, :pub, 'https://e.test/article', :h,
                     'q', 'a', 0, 'r', 0.4200, 't', 'pt')
                """
            ).bindparams(id=aid, brand_id=brand_id, pub=pub, h="0" * 64)
        )
        result = await s.execute(
            text("SELECT losing_candidates FROM placement_audit WHERE id = :id").bindparams(id=aid)
        )
        (losing_candidates,) = result.one()
    assert losing_candidates == []
