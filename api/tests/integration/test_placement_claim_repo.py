"""M1-M7 tests for PlacementClaimRepo.claim() — the 4-branch UPSERT WHERE.

Each Mx maps 1:1 to a row in placement-runtime-design.md § AD8 Semantic
matrix and the COR-75 AC. Located under tests/integration/ so the
conftest ``_truncate_tables`` autouse fixture wipes between tests.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime, timedelta

import pytest

from cortex_api.service.placement.model.placement_compute_claim import (
    PlacementClaimStatus,
)
from cortex_api.service.placement.repo.placement_claim_repo import (
    PlacementClaimRepo,
)

pytestmark = pytest.mark.integration


_PUBLISHER = uuid.uuid4()
_ARTICLE_URL = "https://example.com/article-cor75"
_ARTICLE_HASH = hashlib.sha256(_ARTICLE_URL.encode("utf-8")).digest()
_BRAND_IDS = [uuid.uuid4(), uuid.uuid4()]


def _fresh_db():
    from cortex_api.infra.container import Container as InfraContainer

    return InfraContainer()._database_client_factory()


async def _existing_claim_row(
    *,
    status: PlacementClaimStatus,
    expires_in: timedelta,
    completed_age: timedelta | None = None,
    agent_ws_request_id: str = "seed-req",
) -> uuid.UUID:
    """Seed a single row and return its claim_id."""
    from sqlalchemy import text

    db = _fresh_db()
    claim_id = uuid.uuid4()
    async with db.session() as s:
        await s.execute(
            text(
                """
                INSERT INTO placement_compute_claim (
                  publisher_id, article_url_hash, claim_id, agent_ws_request_id,
                  brand_ids, expires_at, completed_at, status
                ) VALUES (
                  :pub, :hash, :cid, :req, CAST(:brands AS uuid[]),
                  NOW() + CAST(:ttl_sec AS integer) * interval '1 second',
                  CASE WHEN CAST(:done_age_sec AS integer) IS NULL THEN NULL
                       ELSE NOW() - CAST(:done_age_sec AS integer) * interval '1 second' END,
                  CAST(:status AS placement_claim_status)
                )
                """
            ),
            {
                "pub": _PUBLISHER,
                "hash": _ARTICLE_HASH,
                "cid": claim_id,
                "req": agent_ws_request_id,
                "brands": [str(b) for b in _BRAND_IDS],
                "ttl_sec": int(expires_in.total_seconds()),
                "done_age_sec": int(completed_age.total_seconds()) if completed_age else None,
                "status": status.value,
            },
        )
        await s.commit()
    return claim_id


@pytest.mark.asyncio
async def test_m1_no_row_winner() -> None:
    repo = PlacementClaimRepo()
    db = _fresh_db()
    async with db.session() as s:
        outcome = await repo.claim(
            s,
            publisher_id=_PUBLISHER,
            article_url_hash=_ARTICLE_HASH,
            agent_ws_request_id="caller-A",
            brand_ids=_BRAND_IDS,
        )
    assert outcome.winner is True
    assert (
        outcome.expires_at.replace(tzinfo=UTC) > datetime.now(tz=UTC)
        if outcome.expires_at.tzinfo is None
        else outcome.expires_at > datetime.now(tz=UTC)
    )


@pytest.mark.asyncio
async def test_m2_in_flight_same_caller_winner_l1() -> None:
    await _existing_claim_row(
        status=PlacementClaimStatus.IN_FLIGHT,
        expires_in=timedelta(seconds=45),
        agent_ws_request_id="caller-SAME",
    )
    repo = PlacementClaimRepo()
    db = _fresh_db()
    async with db.session() as s:
        outcome = await repo.claim(
            s,
            publisher_id=_PUBLISHER,
            article_url_hash=_ARTICLE_HASH,
            agent_ws_request_id="caller-SAME",  # same as seeded
            brand_ids=_BRAND_IDS,
        )
    assert outcome.winner is True  # L1


@pytest.mark.asyncio
async def test_m3_in_flight_different_caller_loser() -> None:
    seeded_claim = await _existing_claim_row(
        status=PlacementClaimStatus.IN_FLIGHT,
        expires_in=timedelta(seconds=45),
        agent_ws_request_id="caller-A",
    )
    repo = PlacementClaimRepo()
    db = _fresh_db()
    async with db.session() as s:
        outcome = await repo.claim(
            s,
            publisher_id=_PUBLISHER,
            article_url_hash=_ARTICLE_HASH,
            agent_ws_request_id="caller-B",  # different
            brand_ids=_BRAND_IDS,
        )
    assert outcome.winner is False
    assert outcome.claim_id == seeded_claim  # loser reads existing claim


@pytest.mark.asyncio
async def test_m4_in_flight_expired_takeover_winner() -> None:
    await _existing_claim_row(
        status=PlacementClaimStatus.IN_FLIGHT,
        expires_in=timedelta(seconds=-5),  # already past
        agent_ws_request_id="caller-A",
    )
    repo = PlacementClaimRepo()
    db = _fresh_db()
    async with db.session() as s:
        outcome = await repo.claim(
            s,
            publisher_id=_PUBLISHER,
            article_url_hash=_ARTICLE_HASH,
            agent_ws_request_id="caller-B",
            brand_ids=_BRAND_IDS,
        )
    assert outcome.winner is True


@pytest.mark.asyncio
async def test_m5_failed_retry_winner() -> None:
    await _existing_claim_row(
        status=PlacementClaimStatus.FAILED,
        expires_in=timedelta(seconds=45),
        agent_ws_request_id="caller-A",
    )
    repo = PlacementClaimRepo()
    db = _fresh_db()
    async with db.session() as s:
        outcome = await repo.claim(
            s,
            publisher_id=_PUBLISHER,
            article_url_hash=_ARTICLE_HASH,
            agent_ws_request_id="caller-B",
            brand_ids=_BRAND_IDS,
        )
    assert outcome.winner is True


@pytest.mark.asyncio
async def test_m6_done_fresh_loser_l3_freshness() -> None:
    await _existing_claim_row(
        status=PlacementClaimStatus.DONE,
        expires_in=timedelta(seconds=-30),  # past — but status='done' guards
        completed_age=timedelta(minutes=2),  # <5 min
        agent_ws_request_id="caller-A",
    )
    repo = PlacementClaimRepo()
    db = _fresh_db()
    async with db.session() as s:
        outcome = await repo.claim(
            s,
            publisher_id=_PUBLISHER,
            article_url_hash=_ARTICLE_HASH,
            agent_ws_request_id="caller-A",  # same caller — still loser
            brand_ids=_BRAND_IDS,
        )
    assert outcome.winner is False


@pytest.mark.asyncio
async def test_m7_done_stale_winner_l3_recompute() -> None:
    await _existing_claim_row(
        status=PlacementClaimStatus.DONE,
        expires_in=timedelta(seconds=-30),
        completed_age=timedelta(minutes=10),  # >5 min
        agent_ws_request_id="caller-A",
    )
    repo = PlacementClaimRepo()
    db = _fresh_db()
    async with db.session() as s:
        outcome = await repo.claim(
            s,
            publisher_id=_PUBLISHER,
            article_url_hash=_ARTICLE_HASH,
            agent_ws_request_id="caller-B",
            brand_ids=_BRAND_IDS,
        )
    assert outcome.winner is True


@pytest.mark.asyncio
async def test_complete_marks_done() -> None:
    """Successful complete sets status=done, completed_at, placement_audit_id."""
    from sqlalchemy import text

    claim_id_seeded = await _existing_claim_row(
        status=PlacementClaimStatus.IN_FLIGHT,
        expires_in=timedelta(seconds=45),
    )
    repo = PlacementClaimRepo()
    audit_id = uuid.uuid4()
    db = _fresh_db()
    async with db.session() as s:
        ok = await repo.complete(
            s,
            publisher_id=_PUBLISHER,
            claim_id=claim_id_seeded,
            status=PlacementClaimStatus.DONE,
            placement_audit_id=audit_id,
        )
        assert ok is True
        result = await s.execute(
            text("SELECT status, completed_at, placement_audit_id FROM placement_compute_claim WHERE claim_id = :cid"),
            {"cid": claim_id_seeded},
        )
        row = result.one()
    assert row[0] == "done"
    assert row[1] is not None
    assert row[2] == audit_id


@pytest.mark.asyncio
async def test_complete_wrong_claim_id_returns_false() -> None:
    """404 path: complete() on a non-existent claim_id returns False."""
    repo = PlacementClaimRepo()
    db = _fresh_db()
    async with db.session() as s:
        ok = await repo.complete(
            s,
            publisher_id=_PUBLISHER,
            claim_id=uuid.uuid4(),  # bogus
            status=PlacementClaimStatus.DONE,
            placement_audit_id=None,
        )
    assert ok is False


@pytest.mark.asyncio
async def test_m7_re_claim_clears_stale_completion_fields() -> None:
    """Regression guard: after a done→in_flight L3 takeover, completed_at /
    placement_audit_id must be cleared."""
    from sqlalchemy import text

    await _existing_claim_row(
        status=PlacementClaimStatus.DONE,
        expires_in=timedelta(seconds=-30),
        completed_age=timedelta(minutes=10),
        agent_ws_request_id="caller-A",
    )
    db = _fresh_db()
    audit_id = uuid.uuid4()
    async with db.session() as s:
        await s.execute(
            text(
                "UPDATE placement_compute_claim SET placement_audit_id = :aid "
                "WHERE publisher_id = :p AND article_url_hash = :h"
            ),
            {"aid": audit_id, "p": _PUBLISHER, "h": _ARTICLE_HASH},
        )
        await s.commit()

    repo = PlacementClaimRepo()
    async with db.session() as s:
        outcome = await repo.claim(
            s,
            publisher_id=_PUBLISHER,
            article_url_hash=_ARTICLE_HASH,
            agent_ws_request_id="caller-B",
            brand_ids=_BRAND_IDS,
        )
        assert outcome.winner is True
        result = await s.execute(
            text(
                "SELECT completed_at, placement_audit_id, status FROM placement_compute_claim "
                "WHERE publisher_id=:p AND article_url_hash=:h"
            ),
            {"p": _PUBLISHER, "h": _ARTICLE_HASH},
        )
        row = result.one()
    assert row[0] is None  # completed_at cleared
    assert row[1] is None  # placement_audit_id cleared
    assert row[2] == "in_flight"
