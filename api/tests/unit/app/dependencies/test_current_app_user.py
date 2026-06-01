"""Unit tests for `app/dependencies/auth.py::current_app_user`.

This dep owns the only place token-shape dispatch happens — bootstrap tokens
upsert via `recognize_user`, session tokens fetch via `get_user`, every other
shape 401s. The owl-workflows review on PR #13 flagged that the original
implementation dispatched on `oauth_subject` claim *presence* (a heuristic);
this test set pins the new contract: dispatch on the explicit `token_kind`
claim.

The dep is wired with `@inject` so its `user_service` Depends defaults are
container-resolved at request time. Calling it directly with kwargs (the
unit-test idiom) sidesteps the wiring layer entirely — we just hand it a
canned `AuthedUser` + a `MagicMock` user_service and assert on what it did.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from cortex_api.app.dependencies.auth import current_app_user
from cortex_api.core.exceptions import UnauthorizedError
from cortex_api.service.identity.model.app_user import AppUser
from cortex_api.service.identity.model.authed_user import AuthedUser


def _user_service_mock() -> MagicMock:
    svc = MagicMock()
    svc.recognize_user = AsyncMock()
    svc.get_user = AsyncMock()
    return svc


@pytest.mark.asyncio
async def test_bootstrap_token_calls_recognize_user_with_google_subject() -> None:
    """`token_kind="bootstrap"` + oauth_subject → recognize_user upsert path."""
    google_sub = "116973569897222226602"
    user = AuthedUser(
        user_id=uuid4(),  # UUIDv5 placeholder — not used on the bootstrap branch
        email="vincent@mlytics.com",
        display_name="Vincent Yang",
        raw_claims={
            "sub": "<placeholder>",
            "email": "vincent@mlytics.com",
            "display_name": "Vincent Yang",
            "oauth_subject": google_sub,
            "token_kind": "bootstrap",
        },
    )
    expected = AppUser(
        id=uuid4(),
        oauth_subject=google_sub,
        email="vincent@mlytics.com",
        display_name="Vincent Yang",
    )
    svc = _user_service_mock()
    svc.recognize_user.return_value = expected

    result = await current_app_user(user=user, user_service=svc)

    assert result is expected
    svc.recognize_user.assert_awaited_once_with(
        oauth_subject=google_sub,
        email="vincent@mlytics.com",
        display_name="Vincent Yang",
    )
    svc.get_user.assert_not_awaited()


@pytest.mark.asyncio
async def test_session_token_calls_get_user_with_user_id() -> None:
    """`token_kind="session"` → get_user(user_id) fetch path."""
    app_user_id = uuid4()
    user = AuthedUser(
        user_id=app_user_id,
        email="vincent@mlytics.com",
        raw_claims={
            "sub": str(app_user_id),
            "email": "vincent@mlytics.com",
            "token_kind": "session",
        },
    )
    expected = AppUser(
        id=app_user_id,
        oauth_subject="116973569897222226602",
        email="vincent@mlytics.com",
    )
    svc = _user_service_mock()
    svc.get_user.return_value = expected

    result = await current_app_user(user=user, user_service=svc)

    assert result is expected
    svc.get_user.assert_awaited_once_with(app_user_id)
    svc.recognize_user.assert_not_awaited()


@pytest.mark.asyncio
async def test_bootstrap_token_missing_oauth_subject_raises() -> None:
    """Bootstrap shape with no `oauth_subject` is a malformed contract → 401."""
    user = AuthedUser(
        user_id=uuid4(),
        email="vincent@mlytics.com",
        raw_claims={
            "sub": str(uuid4()),
            "email": "vincent@mlytics.com",
            "token_kind": "bootstrap",
            # No oauth_subject — would silently fall through to get_user in
            # the old contract.
        },
    )
    svc = _user_service_mock()

    with pytest.raises(UnauthorizedError, match="bootstrap token missing oauth_subject"):
        await current_app_user(user=user, user_service=svc)

    svc.recognize_user.assert_not_awaited()
    svc.get_user.assert_not_awaited()


@pytest.mark.asyncio
async def test_missing_token_kind_raises() -> None:
    """Absent `token_kind` claim → 401 at the boundary (no silent default)."""
    user = AuthedUser(
        user_id=uuid4(),
        email="vincent@mlytics.com",
        raw_claims={"sub": str(uuid4()), "email": "vincent@mlytics.com"},
    )
    svc = _user_service_mock()

    with pytest.raises(UnauthorizedError, match="missing or unknown token_kind"):
        await current_app_user(user=user, user_service=svc)


@pytest.mark.asyncio
async def test_unknown_token_kind_raises() -> None:
    """Unknown `token_kind` value (e.g. `"foo"`) → 401."""
    user = AuthedUser(
        user_id=uuid4(),
        email="vincent@mlytics.com",
        raw_claims={
            "sub": str(uuid4()),
            "email": "vincent@mlytics.com",
            "token_kind": "foo",
        },
    )
    svc = _user_service_mock()

    with pytest.raises(UnauthorizedError, match="missing or unknown token_kind"):
        await current_app_user(user=user, user_service=svc)
