"""BrandService — brand profile read/write use cases.

Mirrors `BrandIdentityService`: opens a `DatabaseClient.session()` per use
case, delegates persistence to a stateless repo, raises errors from
`core/exceptions.py` chained with `from e`. Scope: brand profile only —
contract / kb_source / reference_answer are out of SP-1 scope.
"""

from __future__ import annotations

import asyncio
from uuid import UUID

import structlog

from cortex_api.core.background import BackgroundTaskTracker
from cortex_api.core.exceptions import NotFoundError
from cortex_api.infra.database_client import DatabaseClient
from cortex_api.service.brand.config import Config
from cortex_api.service.brand.model.profile import BrandProfile
from cortex_api.service.brand.repo.profile_repo import BrandProfileRepo
from cortex_api.service.placement.composer import BrandPlacementComposer


class BrandService:
    """Brand profile orchestration (write side)."""

    def __init__(
        self,
        database_client: DatabaseClient,
        profile_repo: BrandProfileRepo,
        config: Config,
        composer: BrandPlacementComposer,
        tracker: BackgroundTaskTracker,
    ) -> None:
        self._logger = structlog.get_logger(__name__)
        self._db = database_client
        self._profiles = profile_repo
        self._config = config
        self._composer = composer
        self._tracker = tracker

    async def get_profile(self, brand_id: UUID) -> BrandProfile:
        async with self._db.session() as session:
            profile = await self._profiles.get(session, brand_id)
            if profile is None:
                raise NotFoundError(f"brand profile for {brand_id} not found")
            return profile

    async def upsert_profile(self, brand_id: UUID, profile: BrandProfile) -> BrandProfile:
        """Insert or wholesale-replace the brand's single current profile.

        ``profile.brand_id`` is forced to the tenant-scoped ``brand_id`` so a
        client body can never write another brand's row.

        Hook A (AD7): after the upsert session commits, schedule the
        placement composer outside the brand transaction. R2 verdict —
        composer runs in its own session; brand_profile commit succeeds
        first; composer failure is logged by the tracker, never re-raised.
        """
        profile.brand_id = brand_id
        async with self._db.session() as session:
            saved = await self._profiles.upsert(session, profile)
        self._tracker.track(asyncio.create_task(self._composer.compose(brand_id)))
        self._logger.info("brand_profile_upserted", brand_id=str(brand_id))
        return saved
