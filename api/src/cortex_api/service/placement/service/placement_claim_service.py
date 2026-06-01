"""Orchestrates the F2b claim endpoint pair.

``claim()``   — resolve eligible brands → repo.claim() → return outcome + DTO list
``complete()`` — repo.complete()

Status validation lives at the DTO boundary (Pydantic ``Literal``), so
this layer trusts the input is already one of the valid strings.
Transaction lifecycle is owned by the ``async with self._db.session()``
context manager + explicit ``session.commit()`` after the write.

This is the only place ``article_url`` → ``sha256`` conversion lives.
"""

from __future__ import annotations

import hashlib
import uuid
from typing import Any

import structlog

from cortex_api.infra.database_client import DatabaseClient
from cortex_api.service.placement.model.placement_compute_claim import (
    PlacementClaimStatus,
)
from cortex_api.service.placement.placement_claim_config import PlacementClaimConfig
from cortex_api.service.placement.repo.placement_claim_repo import (
    ClaimOutcome,
    PlacementClaimRepo,
)
from cortex_api.service.placement.service.eligible_brands_service import (
    EligibleBrandsService,
)

_LOG = structlog.get_logger(__name__)


class PlacementClaimService:
    """F2b orchestration: claim acquisition + completion callback."""

    def __init__(
        self,
        database_client: DatabaseClient,
        repo: PlacementClaimRepo,
        eligible_brands_service: EligibleBrandsService,
        config: PlacementClaimConfig,
    ) -> None:
        self._db = database_client
        self._repo = repo
        self._ebs = eligible_brands_service
        self._config = config

    async def claim(
        self,
        *,
        publisher_uuid: uuid.UUID,
        article_url: str,
        agent_ws_request_id: str,
        lang: str,
    ) -> tuple[ClaimOutcome, list[dict[str, Any]]]:
        """Pre-resolve eligible brands (for the response payload AND the
        claim row's ``brand_ids`` snapshot), then attempt to claim."""
        eligible = await self._ebs.list_eligible(publisher_uuid=publisher_uuid, lang=lang)
        brand_ids = [uuid.UUID(item["brand_uuid"]) for item in eligible]

        article_hash = hashlib.sha256(article_url.encode("utf-8")).digest()
        async with self._db.session() as session:
            outcome = await self._repo.claim(
                session,
                publisher_id=publisher_uuid,
                article_url_hash=article_hash,
                agent_ws_request_id=agent_ws_request_id,
                brand_ids=brand_ids,
                lease_ttl_seconds=self._config.lease_ttl_seconds,
                freshness_window_seconds=self._config.freshness_window_seconds,
            )
            await session.commit()

        _LOG.info(
            "placement_claim",
            publisher_uuid=str(publisher_uuid),
            winner=outcome.winner,
            claim_id=str(outcome.claim_id),
            brand_count=len(brand_ids),
        )
        return outcome, eligible

    async def delete_claim(
        self,
        *,
        publisher_uuid: uuid.UUID,
        article_url: str,
    ) -> bool:
        """Reset the placement claim for an article — immediate invalidation.

        Called by aigc-mvp's 一鍵刪除 to bypass the L3 freshness window.
        Unconditional delete: works on in_flight, done, or failed claims.
        Next visitor's POST /placement-claims will see no row (M1) and win.
        """
        article_url_hash = hashlib.sha256(article_url.encode("utf-8")).digest()
        async with self._db.session() as session:
            deleted = await self._repo.delete(
                session,
                publisher_id=publisher_uuid,
                article_url_hash=article_url_hash,
            )
            await session.commit()
        _LOG.info(
            "placement_claim_delete",
            publisher_uuid=str(publisher_uuid),
            article_url=article_url,
            deleted=deleted,
        )
        return deleted

    async def complete(
        self,
        *,
        publisher_uuid: uuid.UUID,
        claim_id: uuid.UUID,
        status: PlacementClaimStatus,
        placement_audit_id: uuid.UUID | None,
    ) -> bool:
        """Mark a claim done/failed. Returns False if ``(publisher_uuid,
        claim_id)`` doesn't match any row (router translates to 404).

        ``status`` is already validated by the DTO ``Literal``; we accept
        the enum here so the type system flows through.
        """
        async with self._db.session() as session:
            ok = await self._repo.complete(
                session,
                publisher_id=publisher_uuid,
                claim_id=claim_id,
                status=status,
                placement_audit_id=placement_audit_id,
            )
            await session.commit()
        _LOG.info(
            "placement_claim_complete",
            publisher_uuid=str(publisher_uuid),
            claim_id=str(claim_id),
            status=status.value,
            ok=ok,
        )
        return ok
