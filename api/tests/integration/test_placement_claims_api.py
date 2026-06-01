"""HTTP integration tests for F2b placement-claims (COR-75) — M1-M7
matrix end-to-end, plus auth + 404 + cross-publisher + full claim-complete cycle.

Pattern mirrors ``test_eligible_brands_api.py``: each async test creates
its own ``app = _create_app_with_service_token()`` + inline ``TestClient``
to bind the brand-container singletons to one loop per test (cross-event-loop
hazard from the session-scoped ``client`` fixture).
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import os
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

VALID_TOKEN = "test-token-for-integration"
INVALID_TOKEN = "wrong-token"

pytestmark = pytest.mark.integration


def _create_app_with_service_token():
    """Build a fresh app whose ServiceBearerMiddleware uses VALID_TOKEN."""
    from cortex_api import main as _main
    from cortex_api.main import create_app

    os.environ["CORE_SERVICE_TOKEN_AGENT_WS"] = VALID_TOKEN
    _main._core_container.service_token_config.reset()
    return create_app()


def _fresh_db():
    from cortex_api.infra.container import Container as InfraContainer

    return InfraContainer()._database_client_factory()


async def _seed_one_eligible_brand(publisher_uuid: UUID, lang: str = "zh-tw") -> UUID:
    """Insert Brand + Profile + Scope + placement-settings as one composed row.

    Returns the brand UUID so callers can assert on it if needed.
    """
    from cortex_api.core.identifiers import uuid7
    from cortex_api.service.brand.model.profile import BrandProfile
    from cortex_api.service.brand_identity.model.brand import Brand
    from cortex_api.service.placement.model.scope import BrandPublisherScope
    from cortex_api.service.placement.model.settings import (
        BrandPlacementSettings,
        PlacementMode,
    )
    from cortex_api.service.placement.model.status import PlacementRowStatus

    brand_uuid = uuid7()
    db = _fresh_db()
    async with db.session() as s:
        s.add(Brand(id=brand_uuid, display_name="TestBrand"))
        await s.flush()
        s.add(BrandProfile(brand_id=brand_uuid, name="TestBrand", about="x", topics=[]))
        s.add(
            BrandPublisherScope(
                brand_id=brand_uuid,
                publisher_id=publisher_uuid,
                lang=lang,
                status=PlacementRowStatus.ACTIVE,
            )
        )
        s.add(
            BrandPlacementSettings(
                brand_id=brand_uuid,
                matching_rules=None,
                matching_keywords=[],
                matching_categories=[],
                ad_ratio=Decimal("1.00"),
                question_position=1,
                mode=PlacementMode.QUESTION_REPLACEMENT,
                status=PlacementRowStatus.ACTIVE,
                composed_at=_dt.datetime.now(tz=_dt.UTC).replace(tzinfo=None),
            )
        )
        await s.flush()
    return brand_uuid


def _hash(url: str) -> bytes:
    return hashlib.sha256(url.encode("utf-8")).digest()


# ---------------------------------------------------------------------------
# Auth tests — sync, no DB
# ---------------------------------------------------------------------------


class TestPlacementClaimsAuth:
    def test_no_auth_returns_401(self) -> None:
        from fastapi.testclient import TestClient

        app = _create_app_with_service_token()
        publisher = uuid4()
        with TestClient(app) as c:
            r = c.post(
                f"/v1/publishers/{publisher}/placement-claims?lang=zh-tw",
                json={"article_url": "https://x", "agent_ws_request_id": "r"},
            )
        assert r.status_code == 401

    def test_wrong_token_returns_401(self) -> None:
        from fastapi.testclient import TestClient

        app = _create_app_with_service_token()
        publisher = uuid4()
        with TestClient(app) as c:
            r = c.post(
                f"/v1/publishers/{publisher}/placement-claims?lang=zh-tw",
                json={"article_url": "https://x", "agent_ws_request_id": "r"},
                headers={"Authorization": f"Bearer {INVALID_TOKEN}"},
            )
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# M1-M7 matrix — HTTP roundtrip per row
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_m1_http_no_row_winner() -> None:
    from fastapi.testclient import TestClient

    publisher = uuid4()
    await _seed_one_eligible_brand(publisher)
    app = _create_app_with_service_token()
    with TestClient(app) as c:
        r = c.post(
            f"/v1/publishers/{publisher}/placement-claims?lang=zh-tw",
            json={"article_url": "https://example.com/m1", "agent_ws_request_id": "req-A"},
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        )
    assert r.status_code == 200
    body = r.json()
    assert body["winner"] is True
    assert len(body["eligible_brands"]) == 1


@pytest.mark.asyncio
async def test_m2_http_in_flight_same_caller_l1() -> None:
    """Same caller hitting twice → both winners (L1 idempotency)."""
    from fastapi.testclient import TestClient

    publisher = uuid4()
    await _seed_one_eligible_brand(publisher)
    app = _create_app_with_service_token()
    with TestClient(app) as c:
        body1 = c.post(
            f"/v1/publishers/{publisher}/placement-claims?lang=zh-tw",
            json={"article_url": "https://example.com/m2", "agent_ws_request_id": "req-SAME"},
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        ).json()
        body2 = c.post(
            f"/v1/publishers/{publisher}/placement-claims?lang=zh-tw",
            json={"article_url": "https://example.com/m2", "agent_ws_request_id": "req-SAME"},
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        ).json()
    assert body1["winner"] is True
    assert body2["winner"] is True


@pytest.mark.asyncio
async def test_m3_http_in_flight_different_caller_loser() -> None:
    from fastapi.testclient import TestClient

    publisher = uuid4()
    await _seed_one_eligible_brand(publisher)
    app = _create_app_with_service_token()
    with TestClient(app) as c:
        a = c.post(
            f"/v1/publishers/{publisher}/placement-claims?lang=zh-tw",
            json={"article_url": "https://example.com/m3", "agent_ws_request_id": "req-A"},
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        ).json()
        b = c.post(
            f"/v1/publishers/{publisher}/placement-claims?lang=zh-tw",
            json={"article_url": "https://example.com/m3", "agent_ws_request_id": "req-B"},
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        ).json()
    assert a["winner"] is True
    assert b["winner"] is False
    assert b["claim_id"] == a["claim_id"]  # loser reads existing claim


@pytest.mark.asyncio
async def test_m4_http_expired_takeover() -> None:
    """Seed an in_flight row with past expires_at, then POST and expect winner."""
    from fastapi.testclient import TestClient
    from sqlalchemy import text

    publisher = uuid4()
    article = "https://example.com/m4"
    await _seed_one_eligible_brand(publisher)
    db = _fresh_db()
    async with db.session() as s:
        await s.execute(
            text(
                """
                INSERT INTO placement_compute_claim
                    (publisher_id, article_url_hash, claim_id, agent_ws_request_id,
                     brand_ids, expires_at, status)
                VALUES (:p, :h, :c, 'old', ARRAY[]::uuid[],
                        NOW() - interval '5 seconds',
                        CAST('in_flight' AS placement_claim_status))
                """
            ),
            {"p": publisher, "h": _hash(article), "c": uuid4()},
        )
        await s.commit()

    app = _create_app_with_service_token()
    with TestClient(app) as c:
        r = c.post(
            f"/v1/publishers/{publisher}/placement-claims?lang=zh-tw",
            json={"article_url": article, "agent_ws_request_id": "req-NEW"},
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        )
    assert r.json()["winner"] is True


@pytest.mark.asyncio
async def test_m5_http_failed_retry() -> None:
    from fastapi.testclient import TestClient
    from sqlalchemy import text

    publisher = uuid4()
    article = "https://example.com/m5"
    await _seed_one_eligible_brand(publisher)
    db = _fresh_db()
    async with db.session() as s:
        await s.execute(
            text(
                """
                INSERT INTO placement_compute_claim
                    (publisher_id, article_url_hash, claim_id, agent_ws_request_id,
                     brand_ids, expires_at, status)
                VALUES (:p, :h, :c, 'old', ARRAY[]::uuid[],
                        NOW() + interval '45 seconds',
                        CAST('failed' AS placement_claim_status))
                """
            ),
            {"p": publisher, "h": _hash(article), "c": uuid4()},
        )
        await s.commit()

    app = _create_app_with_service_token()
    with TestClient(app) as c:
        r = c.post(
            f"/v1/publishers/{publisher}/placement-claims?lang=zh-tw",
            json={"article_url": article, "agent_ws_request_id": "req-RETRY"},
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        )
    assert r.json()["winner"] is True


@pytest.mark.asyncio
async def test_m6_http_done_fresh_loser() -> None:
    from fastapi.testclient import TestClient
    from sqlalchemy import text

    publisher = uuid4()
    article = "https://example.com/m6"
    await _seed_one_eligible_brand(publisher)
    db = _fresh_db()
    async with db.session() as s:
        await s.execute(
            text(
                """
                INSERT INTO placement_compute_claim
                    (publisher_id, article_url_hash, claim_id, agent_ws_request_id,
                     brand_ids, expires_at, completed_at, status)
                VALUES (:p, :h, :c, 'old', ARRAY[]::uuid[],
                        NOW() - interval '30 seconds',
                        NOW() - interval '2 minutes',
                        CAST('done' AS placement_claim_status))
                """
            ),
            {"p": publisher, "h": _hash(article), "c": uuid4()},
        )
        await s.commit()

    app = _create_app_with_service_token()
    with TestClient(app) as c:
        r = c.post(
            f"/v1/publishers/{publisher}/placement-claims?lang=zh-tw",
            json={"article_url": article, "agent_ws_request_id": "req-X"},
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        )
    assert r.json()["winner"] is False


@pytest.mark.asyncio
async def test_m7_http_done_stale_winner() -> None:
    from fastapi.testclient import TestClient
    from sqlalchemy import text

    publisher = uuid4()
    article = "https://example.com/m7"
    await _seed_one_eligible_brand(publisher)
    db = _fresh_db()
    async with db.session() as s:
        await s.execute(
            text(
                """
                INSERT INTO placement_compute_claim
                    (publisher_id, article_url_hash, claim_id, agent_ws_request_id,
                     brand_ids, expires_at, completed_at, status)
                VALUES (:p, :h, :c, 'old', ARRAY[]::uuid[],
                        NOW() - interval '30 seconds',
                        NOW() - interval '10 minutes',
                        CAST('done' AS placement_claim_status))
                """
            ),
            {"p": publisher, "h": _hash(article), "c": uuid4()},
        )
        await s.commit()

    app = _create_app_with_service_token()
    with TestClient(app) as c:
        r = c.post(
            f"/v1/publishers/{publisher}/placement-claims?lang=zh-tw",
            json={"article_url": article, "agent_ws_request_id": "req-NEW"},
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        )
    assert r.json()["winner"] is True


# ---------------------------------------------------------------------------
# Cross-publisher + 404 + full cycle
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cross_publisher_isolation() -> None:
    """Same article URL, two publishers — independent claims (PK includes publisher)."""
    from fastapi.testclient import TestClient

    p1, p2 = uuid4(), uuid4()
    await _seed_one_eligible_brand(p1)
    await _seed_one_eligible_brand(p2)
    app = _create_app_with_service_token()
    with TestClient(app) as c:
        r1 = c.post(
            f"/v1/publishers/{p1}/placement-claims?lang=zh-tw",
            json={"article_url": "https://example.com/shared", "agent_ws_request_id": "rA"},
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        ).json()
        r2 = c.post(
            f"/v1/publishers/{p2}/placement-claims?lang=zh-tw",
            json={"article_url": "https://example.com/shared", "agent_ws_request_id": "rB"},
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        ).json()
    assert r1["winner"] is True
    assert r2["winner"] is True
    assert r1["claim_id"] != r2["claim_id"]


def test_complete_garbage_status_returns_422() -> None:
    """Pydantic ``Literal`` validates at the boundary so unknown ``status``
    returns 422 (not a deferred ValueError → 500)."""
    from fastapi.testclient import TestClient

    app = _create_app_with_service_token()
    publisher = uuid4()
    bogus = uuid4()
    with TestClient(app) as c:
        r = c.post(
            f"/v1/publishers/{publisher}/placement-claims/{bogus}/complete",
            json={"status": "banana"},
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_complete_unknown_claim_returns_404() -> None:
    from fastapi.testclient import TestClient

    publisher = uuid4()
    bogus = uuid4()
    app = _create_app_with_service_token()
    with TestClient(app) as c:
        r = c.post(
            f"/v1/publishers/{publisher}/placement-claims/{bogus}/complete",
            json={"status": "done"},
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_delete_claim_removes_existing() -> None:
    """DELETE on an existing claim removes the row; subsequent POST is a fresh winner."""
    from fastapi.testclient import TestClient

    publisher = uuid4()
    article = "https://example.com/delete-existing"
    await _seed_one_eligible_brand(publisher)
    app = _create_app_with_service_token()
    with TestClient(app) as c:
        # First: claim so a row exists
        r1 = c.post(
            f"/v1/publishers/{publisher}/placement-claims?lang=zh-tw",
            json={"article_url": article, "agent_ws_request_id": "req-pre-delete"},
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        ).json()
        assert r1["winner"] is True

        # Delete the claim
        rd = c.delete(
            f"/v1/publishers/{publisher}/placement-claims",
            params={"article_url": article},
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        )
        assert rd.status_code == 200
        assert rd.json() == {"deleted": True}

        # After deletion: a new POST should be a fresh winner (no blocking row)
        r2 = c.post(
            f"/v1/publishers/{publisher}/placement-claims?lang=zh-tw",
            json={"article_url": article, "agent_ws_request_id": "req-post-delete"},
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        ).json()
    assert r2["winner"] is True


@pytest.mark.asyncio
async def test_delete_claim_nonexistent_returns_false() -> None:
    """DELETE on a non-existent (publisher, article_url) pair returns deleted=false."""
    from fastapi.testclient import TestClient

    publisher = uuid4()
    app = _create_app_with_service_token()
    with TestClient(app) as c:
        rd = c.delete(
            f"/v1/publishers/{publisher}/placement-claims",
            params={"article_url": "https://example.com/no-such-row"},
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        )
    assert rd.status_code == 200
    assert rd.json() == {"deleted": False}


@pytest.mark.asyncio
async def test_full_claim_then_complete_then_m6_loser() -> None:
    """End-to-end: claim → complete → second claim within freshness window → loser (L3)."""
    from fastapi.testclient import TestClient

    publisher = uuid4()
    await _seed_one_eligible_brand(publisher)
    app = _create_app_with_service_token()
    with TestClient(app) as c:
        r1 = c.post(
            f"/v1/publishers/{publisher}/placement-claims?lang=zh-tw",
            json={"article_url": "https://example.com/full", "agent_ws_request_id": "rA"},
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        ).json()
        assert r1["winner"] is True
        claim_id = r1["claim_id"]

        complete = c.post(
            f"/v1/publishers/{publisher}/placement-claims/{claim_id}/complete",
            json={"status": "done"},
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        )
        assert complete.status_code == 200

        # Within 5-min freshness window → loser (L3)
        r2 = c.post(
            f"/v1/publishers/{publisher}/placement-claims?lang=zh-tw",
            json={"article_url": "https://example.com/full", "agent_ws_request_id": "rB"},
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        ).json()
    assert r2["winner"] is False


@pytest.mark.asyncio
async def test_delete_within_freshness_window_unblocks_winner() -> None:
    """Claim → complete(done) → delete within L3 window → reclaim → winner.

    Step 3 proves the freshness window blocks a normal re-claim (L3 loser).
    Step 5 proves the DELETE bypasses the freshness window (fresh M1 insert).
    """
    from fastapi.testclient import TestClient

    publisher = uuid4()
    article = "https://example.com/delete-unblocks"
    await _seed_one_eligible_brand(publisher)
    app = _create_app_with_service_token()
    with TestClient(app) as c:
        # Step 1: initial POST → winner
        r1 = c.post(
            f"/v1/publishers/{publisher}/placement-claims?lang=zh-tw",
            json={"article_url": article, "agent_ws_request_id": "rA"},
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        ).json()
        assert r1["winner"] is True, "step 1: initial claim must be winner"
        claim_id = r1["claim_id"]

        # Step 2: complete(done) — mark it finished within the freshness window
        rc = c.post(
            f"/v1/publishers/{publisher}/placement-claims/{claim_id}/complete",
            json={"status": "done"},
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        )
        assert rc.status_code == 200, "step 2: complete must succeed"

        # Step 3: POST again — still within 5-min freshness window → LOSER (L3)
        r2 = c.post(
            f"/v1/publishers/{publisher}/placement-claims?lang=zh-tw",
            json={"article_url": article, "agent_ws_request_id": "rB"},
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        ).json()
        assert r2["winner"] is False, "step 3: within freshness window must be loser (L3)"

        # Step 4: DELETE the claim — 一鍵刪除 bypasses L3
        rd = c.delete(
            f"/v1/publishers/{publisher}/placement-claims",
            params={"article_url": article},
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        )
        assert rd.status_code == 200
        assert rd.json()["deleted"] is True, "step 4: row must have been deleted"

        # Step 5: POST again — no row in DB → fresh M1 INSERT → WINNER
        r3 = c.post(
            f"/v1/publishers/{publisher}/placement-claims?lang=zh-tw",
            json={"article_url": article, "agent_ws_request_id": "rC"},
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        ).json()
    assert r3["winner"] is True, "step 5: after delete, claim must be winner again"
