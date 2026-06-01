"""Cache-aside read service for F2 eligible-brands API."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any
from uuid import UUID

import structlog

from cortex_api.infra.database_client import DatabaseClient
from cortex_api.service.placement.cache.eligible_brands_cache import EligibleBrandsCache
from cortex_api.service.placement.repo.eligible_brands_repo import (
    EligibleBrandRow,
    EligibleBrandsRepo,
)

_LOG = structlog.get_logger(__name__)


class EligibleBrandsService:
    """Orchestrates cache + repo for the F2 read path."""

    def __init__(
        self,
        database_client: DatabaseClient,
        repo: EligibleBrandsRepo,
        cache: EligibleBrandsCache,
    ) -> None:
        self._db = database_client
        self._repo = repo
        self._cache = cache

    async def list_eligible(self, publisher_uuid: UUID, lang: str) -> list[dict[str, Any]]:
        cached = await self._cache.get(publisher_uuid=publisher_uuid, lang=lang)
        if cached is not None:
            _LOG.info("eligible_brands_cache_hit", publisher_uuid=str(publisher_uuid), lang=lang)
            return cached

        async with self._db.session() as session:
            rows = await self._repo.find_for_publisher(session=session, publisher_uuid=publisher_uuid, lang=lang)

        payload = [_row_to_dict(r) for r in rows]
        await self._cache.set(publisher_uuid=publisher_uuid, lang=lang, value=payload)
        _LOG.info(
            "eligible_brands_cache_miss_repo_filled",
            publisher_uuid=str(publisher_uuid),
            lang=lang,
            count=len(payload),
        )
        return payload


def _row_to_dict(row: EligibleBrandRow) -> dict[str, Any]:
    """EligibleBrandRow → JSON-serializable dict (UUIDs → str)."""
    d = asdict(row)
    d["brand_uuid"] = str(row.brand_uuid)
    return d
