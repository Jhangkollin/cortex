"""Repo for placement_compute_claim — the 4-branch UPSERT WHERE.

See placement-runtime-design.md § AD8 Semantic matrix for the M1-M7
rules this encodes; see COR-75 description for the AC.

Stateless: caller passes ``AsyncSession`` per call. **Caller also owns
the transaction lifecycle** — this repo does NOT commit or rollback.
Wrap calls in a ``begin()`` block or commit explicitly in the service.
Caller also owns the sha256 hashing of ``article_url`` (kept out of the
repo so test fixtures can build hashes inline).

Lease TTL and L3 freshness window are per-call parameters (defaults
mirror ``PlacementClaimConfig``) — keeps the repo independent of config
construction order and lets unit tests pass explicit short windows.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from cortex_api.service.placement.model.placement_compute_claim import (
    PlacementClaimStatus,
)


@dataclass(frozen=True, slots=True)
class ClaimOutcome:
    """Result of a claim attempt.

    ``winner=True`` means the caller owns the compute slot (fresh INSERT
    OR one of the four take-over branches fired). When False, the caller
    is the loser; ``claim_id`` / ``expires_at`` / ``brand_ids`` describe
    the EXISTING winning claim so the loser can render the cached result.
    """

    winner: bool
    claim_id: uuid.UUID
    expires_at: datetime
    brand_ids: list[uuid.UUID]


# Lease TTL and freshness window are bound as parameters so a single
# config tunable propagates everywhere; ``updated_at = NOW()`` is set
# explicitly because raw ``text()`` UPDATEs bypass SQLAlchemy's
# ``onupdate`` hook (per CLAUDE.md hard-won rule #1).
_CLAIM_UPSERT_SQL = text(
    """
    INSERT INTO placement_compute_claim (
        publisher_id, article_url_hash, claim_id, agent_ws_request_id,
        brand_ids, expires_at, status
    ) VALUES (
        :publisher_id, :article_url_hash, :new_claim_id, :agent_ws_request_id,
        CAST(:brand_ids AS uuid[]),
        NOW() + CAST(:lease_ttl_seconds AS integer) * interval '1 second',
        'in_flight'
    )
    ON CONFLICT (publisher_id, article_url_hash) DO UPDATE
    SET claimed_at = NOW(),
        agent_ws_request_id = EXCLUDED.agent_ws_request_id,
        brand_ids = EXCLUDED.brand_ids,
        expires_at = NOW() + CAST(:lease_ttl_seconds AS integer) * interval '1 second',
        status = 'in_flight',
        completed_at = NULL,
        placement_audit_id = NULL,
        updated_at = NOW()
    WHERE
        -- Pod-crash takeover: prior in_flight claim's lease expired
        (placement_compute_claim.status = 'in_flight'
         AND placement_compute_claim.expires_at < NOW())
        -- Retry after a failed claim
        OR placement_compute_claim.status = 'failed'
        -- L1 — Caller-retry idempotency: same agent_ws_request_id on in_flight
        OR (placement_compute_claim.status = 'in_flight'
            AND placement_compute_claim.agent_ws_request_id = EXCLUDED.agent_ws_request_id)
        -- L3 — Completed-claim freshness: re-compute if 'done' is older than the window
        OR (placement_compute_claim.status = 'done'
            AND placement_compute_claim.completed_at
                < NOW() - CAST(:freshness_window_seconds AS integer) * interval '1 second')
    RETURNING claim_id, expires_at, brand_ids
    """
)


_CLAIM_READ_LOSER_SQL = text(
    """
    SELECT claim_id, expires_at, brand_ids
    FROM placement_compute_claim
    WHERE publisher_id = :publisher_id AND article_url_hash = :article_url_hash
    """
)


_COMPLETE_UPDATE_SQL = text(
    """
    UPDATE placement_compute_claim
    SET status = CAST(:status AS placement_claim_status),
        completed_at = NOW(),
        placement_audit_id = :placement_audit_id,
        updated_at = NOW()
    WHERE publisher_id = :publisher_id AND claim_id = :claim_id
    """
)


# Defaults mirror PlacementClaimConfig's values; service code reads config
# and passes through, but tests can call with short windows directly.
_DEFAULT_LEASE_TTL_SECONDS = 60
_DEFAULT_FRESHNESS_WINDOW_SECONDS = 300


class PlacementClaimRepo:
    """Stateless. Caller owns the AsyncSession lifecycle (no commit here)."""

    async def claim(
        self,
        session: AsyncSession,
        *,
        publisher_id: uuid.UUID,
        article_url_hash: bytes,
        agent_ws_request_id: str,
        brand_ids: list[uuid.UUID],
        lease_ttl_seconds: int = _DEFAULT_LEASE_TTL_SECONDS,
        freshness_window_seconds: int = _DEFAULT_FRESHNESS_WINDOW_SECONDS,
    ) -> ClaimOutcome:
        """Attempt to claim the (publisher, article) compute slot.

        Returns a ClaimOutcome with ``winner=True/False`` and the
        publisher's CURRENT claim row's identifiers (used by the caller
        for the /complete callback or for loser-path read-through).
        """
        new_claim_id = uuid.uuid4()
        result = await session.execute(
            _CLAIM_UPSERT_SQL,
            {
                "publisher_id": publisher_id,
                "article_url_hash": article_url_hash,
                "new_claim_id": new_claim_id,
                "agent_ws_request_id": agent_ws_request_id,
                "brand_ids": [str(b) for b in brand_ids],
                "lease_ttl_seconds": lease_ttl_seconds,
                "freshness_window_seconds": freshness_window_seconds,
            },
        )
        row = result.first()
        if row is not None:
            return ClaimOutcome(
                winner=True,
                claim_id=row[0],
                expires_at=row[1],
                brand_ids=[uuid.UUID(str(b)) for b in row[2]],
            )

        # Loser path: WHERE didn't permit the UPDATE. Read back the
        # existing row so the caller can render the cached result.
        result = await session.execute(
            _CLAIM_READ_LOSER_SQL,
            {
                "publisher_id": publisher_id,
                "article_url_hash": article_url_hash,
            },
        )
        existing = result.one()
        return ClaimOutcome(
            winner=False,
            claim_id=existing[0],
            expires_at=existing[1],
            brand_ids=[uuid.UUID(str(b)) for b in existing[2]],
        )

    async def delete(
        self,
        session: AsyncSession,
        *,
        publisher_id: uuid.UUID,
        article_url_hash: bytes,
    ) -> bool:
        """Unconditionally remove the claim row regardless of status.

        If an in-flight claim is deleted while agent-ws is processing it, the
        worker's eventual POST /complete will 404 (row gone). This is acceptable:
        一鍵刪除 is an admin action that should produce a full reset. The wasted
        compute is the trade-off for immediate invalidation.
        """
        result = await session.execute(
            text("""
                DELETE FROM placement_compute_claim
                WHERE publisher_id = :publisher_id
                  AND article_url_hash = :article_url_hash
            """),
            {"publisher_id": publisher_id, "article_url_hash": article_url_hash},
        )
        return result.rowcount > 0  # type: ignore[attr-defined]

    async def complete(
        self,
        session: AsyncSession,
        *,
        publisher_id: uuid.UUID,
        claim_id: uuid.UUID,
        status: PlacementClaimStatus,
        placement_audit_id: uuid.UUID | None,
    ) -> bool:
        """Mark a claim done/failed. Returns True iff the row was updated.

        Caller owns the commit; this method only issues the UPDATE.
        """
        result = await session.execute(
            _COMPLETE_UPDATE_SQL,
            {
                "status": status.value,
                "placement_audit_id": placement_audit_id,
                "publisher_id": publisher_id,
                "claim_id": claim_id,
            },
        )
        # rowcount is available on the underlying CursorResult for DML statements,
        # though Result[Any] doesn't expose it in the type stubs.
        return bool(result.rowcount == 1)  # type: ignore[attr-defined]
