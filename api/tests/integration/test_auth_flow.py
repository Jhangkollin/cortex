"""End-to-end regression tests for the auth + brand-creation flow.

Each test pins a contract that was broken by a real PR in the last few
weeks. The goal isn't unit-style behaviour coverage — these tests catch
the class of "looks right in unit tests, breaks in UAT" bugs that
motivated the integration suite in the first place.

Bug class                                                | PR(s)
---------------------------------------------------------|------------
Bootstrap JWT 401 from `UUID(google_sub)` parse failure  | #12 → #13
Phantom AppUser row from `or str(user.user_id)` fallback | #13 → #15
Founder UNIQUE only enforced in app code (TOCTOU race)   | #14, #16
`token_kind` claim dispatch (silent default branch)      | #15

Run with: ``pytest -m integration``.
"""

from __future__ import annotations

import datetime as _dt
from uuid import UUID

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from cortex_api.core.config.auth_config import AuthConfig
from cortex_api.core.identifiers import uuid7

pytestmark = pytest.mark.integration


async def test_bootstrap_jwt_returns_200_creates_app_user(
    client: TestClient,
    bootstrap_jwt,  # type: ignore[no-untyped-def]
    db_engine: AsyncEngine,
) -> None:
    """A valid bootstrap JWT (sub = UUIDv5 placeholder, oauth_subject = Google id)
    must reach /v1/auth/me, upsert exactly one app_user row, and return 200.

    Regression: the original bootstrap path 401'd because the api dep
    called ``UUID(claims["sub"])`` directly on Google's numeric `sub`
    (``"104895824..."``). Fixed by minting `sub` as a deterministic UUIDv5
    on the web side. This pins both sides of that contract.
    """
    token = bootstrap_jwt(
        oauth_subject="116000000000000000001",
        email="alice@mlytics.com",
        display_name="Alice",
    )

    r = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert r.status_code == 200, r.text
    body = r.json()
    assert body["email"] == "alice@mlytics.com"
    assert body["display_name"] == "Alice"
    assert body["memberships"] == []
    assert body["active_context"] is None

    async with db_engine.connect() as conn:
        rows = (await conn.execute(text("SELECT count(*)::int AS n FROM app_user"))).scalar()
        assert rows == 1


async def test_session_jwt_finds_existing_user_no_phantom(
    client: TestClient,
    bootstrap_jwt,  # type: ignore[no-untyped-def]
    session_jwt,  # type: ignore[no-untyped-def]
    db_engine: AsyncEngine,
) -> None:
    """A bootstrap call followed by a session call must converge on a single
    app_user row, not create a phantom.

    Regression: the original router fallback (``oauth_subject or
    str(user.user_id)``) created a phantom app_user row when a session
    token (no oauth_subject claim) hit /v1/auth/me — the upsert key
    silently became the placeholder UUID string. Fixed by current_app_user
    dispatching strictly on token_kind.
    """
    bt = bootstrap_jwt(
        oauth_subject="116000000000000000002",
        email="bob@mlytics.com",
    )
    r1 = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {bt}"})
    assert r1.status_code == 200, r1.text
    user_id = UUID(r1.json()["user_id"])

    st = session_jwt(user_id=user_id, email="bob@mlytics.com")
    r2 = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {st}"})
    assert r2.status_code == 200, r2.text
    assert UUID(r2.json()["user_id"]) == user_id

    async with db_engine.connect() as conn:
        n = (
            await conn.execute(
                text("SELECT count(*)::int FROM app_user WHERE email = :e"),
                {"e": "bob@mlytics.com"},
            )
        ).scalar()
        assert n == 1, "phantom app_user row created — session-token path leaked into bootstrap upsert"


async def test_post_brand_creates_membership_with_invited_by_null(
    client: TestClient,
    bootstrap_jwt,  # type: ignore[no-untyped-def]
    session_jwt,  # type: ignore[no-untyped-def]
    db_engine: AsyncEngine,
) -> None:
    """Self-serve brand creation produces an ADMIN founder membership with
    ``invited_by IS NULL`` (the founder semantic).
    """
    bt = bootstrap_jwt(
        oauth_subject="116000000000000000003",
        email="carol@mlytics.com",
    )
    me = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {bt}"})
    assert me.status_code == 200, me.text
    user_id = UUID(me.json()["user_id"])

    st = session_jwt(user_id=user_id, email="carol@mlytics.com")
    r = client.post("/v1/brand", headers={"Authorization": f"Bearer {st}"}, json={})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["role"] == "admin"
    assert "id" in body["brand"]
    brand_id = UUID(body["brand"]["id"])

    async with db_engine.connect() as conn:
        row = (
            await conn.execute(
                text("SELECT role, invited_by FROM brand_membership WHERE user_id = :u AND brand_id = :b"),
                {"u": user_id, "b": brand_id},
            )
        ).one()
        assert row.role == "admin"
        assert row.invited_by is None


async def test_post_brand_twice_creates_two_independent_brands(
    client: TestClient,
    bootstrap_jwt,  # type: ignore[no-untyped-def]
    session_jwt,  # type: ignore[no-untyped-def]
    db_engine: AsyncEngine,
) -> None:
    """Multi-brand: a second POST /v1/brand by the same caller succeeds.

    The founder-unique partial index was dropped (migration 7ab199ba95a2), so a
    user can found more than one independent brand — each POST creates a new
    brand + its own ADMIN founder membership (invited_by IS NULL), never
    overriding the first.
    """
    bt = bootstrap_jwt(
        oauth_subject="116000000000000000004",
        email="dave@mlytics.com",
    )
    me = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {bt}"})
    assert me.status_code == 200, me.text
    user_id = UUID(me.json()["user_id"])

    st = session_jwt(user_id=user_id, email="dave@mlytics.com")
    r1 = client.post("/v1/brand", headers={"Authorization": f"Bearer {st}"}, json={})
    assert r1.status_code == 201, r1.text
    r2 = client.post("/v1/brand", headers={"Authorization": f"Bearer {st}"}, json={})
    assert r2.status_code == 201, r2.text

    brand1 = UUID(r1.json()["brand"]["id"])
    brand2 = UUID(r2.json()["brand"]["id"])
    assert brand1 != brand2, "second POST must create a distinct, independent brand"

    async with db_engine.connect() as conn:
        n = (
            await conn.execute(
                text("SELECT count(*)::int FROM brand_membership WHERE user_id = :u AND invited_by IS NULL"),
                {"u": user_id},
            )
        ).scalar()
        assert n == 2, "each onboarding should create its own founder membership (multi-brand)"


def _assert_token_kind_401(r) -> None:  # type: ignore[no-untyped-def]
    """Assert a 401 response that's specifically the token_kind dispatch
    rejection, not just any 401.

    Status alone is too loose: bad signature, expired exp, missing iss/aud
    all also produce 401s. The bug we're pinning (PR #15: silent default
    branch on unknown token_kind) only shows up if the rejection cites
    ``token_kind``. We assert on the error body shape produced by
    ``app/exception_handlers.py::_cortex_handler`` (``{"error",
    "message", "error_id"}``).
    """
    assert r.status_code == 401, r.text
    body = r.json()
    message = body.get("message") or body.get("detail") or ""
    assert "token_kind" in message.lower(), f"expected 'token_kind' in 401 message, got: {body!r}"


async def test_missing_token_kind_returns_401(client: TestClient) -> None:
    """JWT without `token_kind` must 401 *citing token_kind*, not silently
    take a default branch.

    Catches NextAuth misconfiguration (e.g., a legacy session cookie minted
    before the token_kind contract was tightened). Asserting on body, not
    just status, so a regression that 401s for some unrelated reason still
    fails this test loudly.
    """
    cfg = AuthConfig()
    now = int(_dt.datetime.now(tz=_dt.UTC).timestamp())
    payload = {
        "sub": str(uuid7()),  # arbitrary UUID — verifier won't even reach this if dispatch fires
        "email": "x@mlytics.com",
        "iss": cfg.jwt_issuer,
        "aud": cfg.jwt_audience,
        "iat": now,
        "exp": now + 60,
        # NB: no token_kind claim
    }
    token = jwt.encode(payload, cfg.nextauth_secret, algorithm=cfg.jwt_algorithm)

    r = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    _assert_token_kind_401(r)


async def test_unknown_token_kind_returns_401(client: TestClient) -> None:
    """Control case: token_kind set to a value not in the allowed set must
    also 401 citing token_kind.

    Confirms the dispatch is exhaustive on the allowed set
    (``"bootstrap"``/``"session"``), not a permissive default that fell
    through into some other 401 path. If a future PR adds a new kind, this
    test should fail loudly so the author either widens the test or
    updates the contract intentionally.
    """
    cfg = AuthConfig()
    now = int(_dt.datetime.now(tz=_dt.UTC).timestamp())
    payload = {
        "sub": str(uuid7()),
        "email": "x@mlytics.com",
        "iss": cfg.jwt_issuer,
        "aud": cfg.jwt_audience,
        "iat": now,
        "exp": now + 60,
        "token_kind": "unknown-future-kind",
    }
    token = jwt.encode(payload, cfg.nextauth_secret, algorithm=cfg.jwt_algorithm)

    r = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    _assert_token_kind_401(r)
