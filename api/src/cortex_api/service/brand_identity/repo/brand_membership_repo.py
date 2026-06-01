"""BrandMembership persistence operations.

Stateless — every method takes an `AsyncSession` per call.
"""

from __future__ import annotations

from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from cortex_api.service.brand_identity.model.brand_membership import BrandMembership


class BrandMembershipRepo:
    """CRUD on the `brand_membership` table."""

    async def list_for_user(self, session: AsyncSession, user_id: UUID) -> list[BrandMembership]:
        """Every brand membership the user holds. Called at login."""
        result = await session.exec(select(BrandMembership).where(BrandMembership.user_id == user_id))
        return list(result.all())

    async def get(self, session: AsyncSession, user_id: UUID, brand_id: UUID) -> BrandMembership | None:
        """Single membership for (user, brand). Called at context switch."""
        result = await session.exec(
            select(BrandMembership).where(
                BrandMembership.user_id == user_id,
                BrandMembership.brand_id == brand_id,
            )
        )
        return result.first()

    async def create(self, session: AsyncSession, membership: BrandMembership) -> BrandMembership:
        session.add(membership)
        await session.flush()
        return membership

    async def delete(self, session: AsyncSession, membership_id: UUID) -> None:
        result = await session.exec(select(BrandMembership).where(BrandMembership.id == membership_id))
        existing = result.first()
        if existing is None:
            return
        await session.delete(existing)
        await session.flush()
