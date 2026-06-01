"""Brand profile persistence — stateless, session per call.

Mirrors `service/brand_identity/repo/brand_repo.py`: every method takes an
`AsyncSession` so the service owns the transaction. Always brand_id-scoped.
"""

from __future__ import annotations

from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from cortex_api.service.brand.model.profile import BrandProfile

# Single source of truth for "which columns exist": the SQLAlchemy mapper of
# the model itself. Anything that is neither the primary key nor a DB-managed
# timestamp participates in a wholesale-replace upsert. Adding a column to
# `BrandProfile` automatically joins this set — there is deliberately no
# hand-maintained second list to drift out of sync (DRY / SSOT).
_PK_AND_TIMESTAMPS = {"brand_id", "created_at", "updated_at"}
_ALL_COLUMNS: tuple[str, ...] = tuple(sa.inspect(BrandProfile).columns.keys())
_REPLACEABLE_COLUMNS: tuple[str, ...] = tuple(name for name in _ALL_COLUMNS if name not in _PK_AND_TIMESTAMPS)


class BrandProfileRepo:
    """CRUD on the `brand_profile` table."""

    async def get(self, session: AsyncSession, brand_id: UUID) -> BrandProfile | None:
        result = await session.exec(select(BrandProfile).where(BrandProfile.brand_id == brand_id))
        return result.first()

    async def upsert(self, session: AsyncSession, profile: BrandProfile) -> BrandProfile:
        """Insert or wholesale-replace the single profile for `profile.brand_id`.

        One atomic `INSERT ... ON CONFLICT (brand_id) DO UPDATE` statement —
        no read-then-write, so concurrent / duplicate PUTs cannot race into
        a unique-constraint violation and PUT stays idempotent. Every
        non-PK, non-timestamp column is replaced (wholesale-replace
        semantics); `updated_at` is bumped to `now()` on conflict so the DB
        stays the SSOT for row timestamps even on the update path.
        """
        insert_values = {
            name: getattr(profile, name) for name in _ALL_COLUMNS if name not in {"created_at", "updated_at"}
        }
        replace_values: dict[str, object] = {name: getattr(profile, name) for name in _REPLACEABLE_COLUMNS}
        replace_values["updated_at"] = sa.func.now()

        stmt = (
            pg_insert(BrandProfile)
            .values(**insert_values)
            .on_conflict_do_update(index_elements=["brand_id"], set_=replace_values)
            .returning(BrandProfile)
        )
        result = await session.execute(stmt)
        saved: BrandProfile = result.scalars().one()
        await session.flush()
        return saved
