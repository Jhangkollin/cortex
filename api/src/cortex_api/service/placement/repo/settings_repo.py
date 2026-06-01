"""PlacementSettingsRepo — stateless CRUD for ``brand_placement_settings``.

Mirrors ``BrandProfileRepo``: every method takes the open ``AsyncSession``
so the composer (or any future writer) controls the transaction boundary.
Composer is the only authorised writer at MVP per AD7.

``upsert`` uses ``INSERT ... ON CONFLICT (brand_id) DO UPDATE`` with
``RETURNING`` so the saved row comes back in a single round-trip; the
composer's ``compose`` call therefore makes exactly two DB statements
(``SELECT existing``, then ``INSERT ... RETURNING``) plus the implicit
profile read.
"""

from __future__ import annotations

from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from cortex_api.service.brand.model.profile import BrandProfile
from cortex_api.service.placement.model.settings import BrandPlacementSettings

_PK_AND_TIMESTAMPS = {"brand_id", "created_at", "updated_at"}
_ALL_COLUMNS: tuple[str, ...] = tuple(sa.inspect(BrandPlacementSettings).columns.keys())
_REPLACEABLE_COLUMNS: tuple[str, ...] = tuple(name for name in _ALL_COLUMNS if name not in _PK_AND_TIMESTAMPS)


class PlacementSettingsRepo:
    """Repository for the ``brand_placement_settings`` table."""

    async def get_or_none(self, session: AsyncSession, brand_id: UUID) -> BrandPlacementSettings | None:
        result = await session.exec(select(BrandPlacementSettings).where(BrandPlacementSettings.brand_id == brand_id))
        return result.first()

    async def get_or_none_for_update(self, session: AsyncSession, brand_id: UUID) -> BrandPlacementSettings | None:
        """SELECT ... FOR UPDATE — acquire the row-level lock the composer
        needs before the read-derive-merge-write cycle.

        Per PR #52 Issue 2: ``compose`` reads ``overrides_mask`` from the
        existing row then upserts a merged result. Without a row lock,
        two concurrent composes on the same ``brand_id`` (Hook A from a
        PUT + Hook B from an in-flight analyze, or any future PATCH
        endpoint) can interleave between SELECT and UPSERT and the
        second writer overwrites the first's view. Postgres' row-level
        ``FOR UPDATE`` serialises the section: T1 acquires, T2 blocks,
        T1 UPSERTs + releases, T2 SELECTs the fresh row.

        Note: when the row does not exist yet, ``FOR UPDATE`` has
        nothing to lock — that race is benign because there's no
        existing mask to lose; the loser's ON CONFLICT DO UPDATE
        applies the same derived values.
        """
        result = await session.exec(
            select(BrandPlacementSettings).where(BrandPlacementSettings.brand_id == brand_id).with_for_update()
        )
        return result.first()

    async def find_stale_brand_ids(self, session: AsyncSession, *, limit: int) -> list[UUID]:
        """Find brands needing (re-)compose: profile exists but placement
        is missing OR profile changed after the last compose.

        Two stale cases covered (PR #52 Issue 3 — durability gap from a
        hard pod death between brand_profile commit and Hook A's
        composer task):

        1. ``brand_profile`` exists but no ``brand_placement_settings``
           row (Hook A never landed).
        2. ``brand_profile.updated_at > brand_placement_settings.updated_at``
           — the profile was rewritten and the composer hasn't replayed
           yet.

        Bounded by ``limit`` so a single sweep's blast radius stays
        small; the periodic loop catches the next batch. Composer is
        idempotent and the SELECT FOR UPDATE in its read path makes
        "sweep races a fresh Hook A" benign.
        """
        stmt = (
            select(BrandProfile.brand_id)
            .outerjoin(
                BrandPlacementSettings,
                BrandPlacementSettings.brand_id == BrandProfile.brand_id,  # type: ignore[arg-type]
            )
            .where(
                sa.or_(
                    BrandPlacementSettings.brand_id.is_(None),  # type: ignore[attr-defined]
                    BrandProfile.updated_at > BrandPlacementSettings.updated_at,  # type: ignore[arg-type]
                )
            )
            .limit(limit)
        )
        result = await session.execute(stmt)
        return [row[0] for row in result.all()]

    async def upsert(self, session: AsyncSession, settings: BrandPlacementSettings) -> BrandPlacementSettings:
        insert_values = {
            name: getattr(settings, name) for name in _ALL_COLUMNS if name not in {"created_at", "updated_at"}
        }
        replace_values: dict[str, object] = {name: getattr(settings, name) for name in _REPLACEABLE_COLUMNS}
        replace_values["updated_at"] = sa.func.now()

        stmt = (
            pg_insert(BrandPlacementSettings)
            .values(**insert_values)
            .on_conflict_do_update(index_elements=["brand_id"], set_=replace_values)
            .returning(BrandPlacementSettings)
        )
        result = await session.execute(stmt)
        saved: BrandPlacementSettings = result.scalars().one()
        await session.flush()
        return saved
