"""Read repo for brand_publisher_scope.

Stateless: caller passes ``AsyncSession`` per call. Mirrors the style of
PlacementSettingsRepo (which is also stateless and takes session per call).
"""

from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from cortex_api.service.placement.model.scope import BrandPublisherScope
from cortex_api.service.placement.model.status import PlacementRowStatus

SessionFactory = Callable[[], AbstractAsyncContextManager[AsyncSession]]


class BrandPublisherScopeRepo:
    """Read-side queries for brand_publisher_scope."""

    async def find_publishers_for_brand(self, session: AsyncSession, brand_id: UUID) -> list[tuple[UUID, str]]:
        """Return ``(publisher_uuid, lang)`` pairs for active scope rows.

        Used by EligibleBrandsCache.invalidate_for_brand to know which cache
        keys to DEL after a successful compose.
        """
        stmt = (
            select(BrandPublisherScope.publisher_id, BrandPublisherScope.lang)
            .where(BrandPublisherScope.brand_id == brand_id)
            .where(BrandPublisherScope.status == PlacementRowStatus.ACTIVE)
        )
        result = await session.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]


class ScopedBrandPublisherScopeRepo:
    """Adapter that supplies an AsyncSession from a session factory each call.

    Matches the ``_ScopeRepo`` protocol EligibleBrandsCache expects.
    """

    def __init__(self, repo: BrandPublisherScopeRepo, session_factory: SessionFactory) -> None:
        self._repo = repo
        self._session_factory = session_factory

    async def find_publishers_for_brand(self, brand_id: UUID) -> list[tuple[UUID, str]]:
        async with self._session_factory() as session:
            return await self._repo.find_publishers_for_brand(session, brand_id)
