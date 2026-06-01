"""Unit tests for `app/dependencies/auth.py::authenticated_user`.

Covers the two JWT shapes cortex-api sees:

- **Bootstrap token** — minted by cortex-web's NextAuth `jwt` callback
  BEFORE the AppUser UUID is known. `sub` is a UUIDv5 placeholder derived
  from the Google `oauth_subject`; the real Google id is carried in the
  `oauth_subject` claim and used by `/v1/auth/me` to upsert the AppUser.
- **Session token** — minted after `/v1/auth/me` returns. `sub` is the
  AppUser UUID and `oauth_subject` may be absent.

The dep MUST accept both shapes (parsing `sub` as a UUID) and reject
anything else. The owl-workflows review bot called out the original
implementation 401'd on bootstrap tokens because `UUID("104895824...")`
raises ValueError.
"""

from __future__ import annotations

from uuid import UUID, uuid4

import jwt
import pytest

from cortex_api.app.dependencies.auth import authenticated_user
from cortex_api.core.config.auth_config import AuthConfig
from cortex_api.core.exceptions import UnauthorizedError

_SECRET = "test-secret-do-not-use-in-prod-please-32+chars"


def _auth_config() -> AuthConfig:
    """Build an AuthConfig with a known secret for token signing/verification."""
    return AuthConfig(
        nextauth_secret=_SECRET,
        jwt_algorithm="HS256",
        jwt_audience="cortex-api",
        jwt_issuer="cortex-web",
    )


def _sign(payload: dict[str, object]) -> str:
    """Sign a JWT matching the auth config above. Caller supplies all claims."""
    full = {
        "iss": "cortex-web",
        "aud": "cortex-api",
        **payload,
    }
    return jwt.encode(full, _SECRET, algorithm="HS256")


# ---------------------------------------------------------------------------
# Bootstrap token shape — `sub` is a UUIDv5 placeholder, real Google id in
# `oauth_subject`. Pre-fix this 401'd because the dep parsed `sub` as a UUID
# and the cortex-web `signBootstrapToken` set `sub` to the raw Google id.
# ---------------------------------------------------------------------------


def test_authenticated_user_accepts_bootstrap_shape() -> None:
    """Bootstrap token (sub=UUIDv5 placeholder, oauth_subject=Google id) is accepted."""
    placeholder_sub = str(uuid4())  # UUIDv5 would also pass — only "is a UUID" matters
    google_sub = "104895824739274597"
    token = _sign(
        {
            "sub": placeholder_sub,
            "email": "x@mlytics.com",
            "oauth_subject": google_sub,
            "token_kind": "bootstrap",
        }
    )

    authed = authenticated_user(
        authorization=f"Bearer {token}",
        auth_config=_auth_config(),
    )

    assert authed.email == "x@mlytics.com"
    assert authed.user_id == UUID(placeholder_sub)
    # The real Google id is preserved in raw_claims for downstream upsert.
    assert authed.raw_claims["oauth_subject"] == google_sub


# ---------------------------------------------------------------------------
# Session token shape — `sub` is the AppUser UUID, no oauth_subject.
# ---------------------------------------------------------------------------


def test_authenticated_user_accepts_session_shape() -> None:
    """Session token (sub=AppUser UUID, no oauth_subject claim) is accepted."""
    app_user_id = uuid4()
    token = _sign(
        {
            "sub": str(app_user_id),
            "email": "y@mlytics.com",
            "display_name": "Yvonne",
        }
    )

    authed = authenticated_user(
        authorization=f"Bearer {token}",
        auth_config=_auth_config(),
    )

    assert authed.user_id == app_user_id
    assert authed.email == "y@mlytics.com"
    assert authed.display_name == "Yvonne"
    # No oauth_subject claim is expected on session tokens — downstream
    # current_app_user dispatches on `token_kind`, not on this field.
    assert "oauth_subject" not in authed.raw_claims


# ---------------------------------------------------------------------------
# Broken shape — non-UUID `sub`, no oauth_subject. This is the exact failure
# mode the bug report flagged.
# ---------------------------------------------------------------------------


def test_authenticated_user_rejects_non_uuid_sub() -> None:
    """Malformed `sub` (non-UUID, no fallback) → UnauthorizedError."""
    token = _sign(
        {
            "sub": "104895824739274597",  # Google id verbatim — not a UUID
            "email": "z@mlytics.com",
        }
    )

    with pytest.raises(UnauthorizedError, match="missing required claim"):
        authenticated_user(
            authorization=f"Bearer {token}",
            auth_config=_auth_config(),
        )


def test_authenticated_user_rejects_missing_header() -> None:
    """No Authorization header → UnauthorizedError (defense-in-depth)."""
    with pytest.raises(UnauthorizedError, match="missing or malformed"):
        authenticated_user(authorization="", auth_config=_auth_config())


def test_authenticated_user_rejects_bad_signature() -> None:
    """JWT signed with a different secret → UnauthorizedError."""
    token = jwt.encode(
        {
            "iss": "cortex-web",
            "aud": "cortex-api",
            "sub": str(uuid4()),
            "email": "x@mlytics.com",
        },
        "wrong-secret-also-long-enough-for-hs256-32chars",
        algorithm="HS256",
    )

    with pytest.raises(UnauthorizedError, match="JWT verification failed"):
        authenticated_user(
            authorization=f"Bearer {token}",
            auth_config=_auth_config(),
        )
