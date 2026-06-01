"""Brand persistence operations.

Stateless — every method takes an `AsyncSession` per call so the caller can
coordinate multi-repo transactions (e.g. create brand + create admin
membership atomically).
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from cortex_api.service.brand_identity.model.brand import Brand
from cortex_api.service.brand_identity.model.brand_role import BrandRole


class BrandRepo:
    """CRUD on the `brand` table."""

    async def get_by_id(self, session: AsyncSession, brand_id: UUID) -> Brand | None:
        result = await session.exec(select(Brand).where(Brand.id == brand_id))
        return result.first()

    async def list_for_user_id(
        self,
        session: AsyncSession,
        user_id: UUID,
    ) -> list[tuple[Brand, BrandRole]]:
        """All brands the caller has membership in, with the caller's role per brand.

        Joins brand → brand_membership filtered to the calling user. Ordered by
        `brand.updated_at DESC` so "most recently touched" surfaces first.
        """
        from cortex_api.service.brand_identity.model.brand_membership import (
            BrandMembership,  # noqa: PLC0415 — local to avoid circular
        )

        stmt = (
            select(Brand, BrandMembership.role)
            .join(BrandMembership, BrandMembership.brand_id == Brand.id)  # type: ignore[arg-type]
            .where(BrandMembership.user_id == user_id)
            .order_by(Brand.updated_at.desc())  # type: ignore[attr-defined]
        )
        result = await session.execute(stmt)
        return [(b, r) for b, r in result.all()]

    async def create(self, session: AsyncSession, brand: Brand) -> Brand:
        session.add(brand)
        await session.flush()
        return brand

    async def update_fields(
        self,
        session: AsyncSession,
        brand: Brand,
        **fields: object,
    ) -> Brand:
        """Apply `fields` to the brand object in-place, flush.

        Caller owns field-level validation (which fields are allowed for the
        current role). This is a thin persistence helper.
        """
        for key, value in fields.items():
            setattr(brand, key, value)
        session.add(brand)
        await session.flush()
        return brand

    async def archive(self, session: AsyncSession, brand_id: UUID) -> None:
        brand = await self.get_by_id(session, brand_id)
        if brand is None:
            return
        brand.archived_at = datetime.utcnow()
        session.add(brand)
        await session.flush()
