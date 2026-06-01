"""Unit tests for UserService — the OAuth-driven AppUser upsert."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from cortex_api.service.identity.config import Config
from cortex_api.service.identity.model.app_user import AppUser
from cortex_api.service.identity.service import UserService


def _make_service(user_repo: MagicMock) -> UserService:
    session = MagicMock()
    db_client = MagicMock()

    @asynccontextmanager
    async def _session() -> AsyncIterator[MagicMock]:
        yield session

    db_client.session = _session
    return UserService(database_client=db_client, user_repo=user_repo, config=Config())


@pytest.mark.asyncio
async def test_recognize_new_user_returns_created_appuser() -> None:
    """Repo upsert returns the new AppUser; service passes through."""
    expected = AppUser(
        id=uuid4(),
        oauth_subject="google-oauth2|new-sub",
        email="new@mlytics.com",
        display_name="New User",
    )
    user_repo = MagicMock()
    user_repo.upsert = AsyncMock(return_value=expected)

    service = _make_service(user_repo)
    user = await service.recognize_user(
        oauth_subject="google-oauth2|new-sub",
        email="new@mlytics.com",
        display_name="New User",
    )

    assert user is expected
    user_repo.upsert.assert_awaited_once()


@pytest.mark.asyncio
async def test_recognize_existing_user_passes_display_name_update() -> None:
    """Service forwards display_name=None correctly (repo decides what to do)."""
    expected = AppUser(
        id=uuid4(),
        oauth_subject="google-oauth2|existing",
        email="existing@mlytics.com",
        display_name="Old Name",  # repo would keep this when display_name=None
    )
    user_repo = MagicMock()
    user_repo.upsert = AsyncMock(return_value=expected)

    service = _make_service(user_repo)
    user = await service.recognize_user(
        oauth_subject="google-oauth2|existing",
        email="existing@mlytics.com",
        display_name=None,
    )

    assert user.display_name == "Old Name"
    upsert_call = user_repo.upsert.await_args
    assert upsert_call is not None
    assert upsert_call.kwargs.get("display_name") is None


@pytest.mark.asyncio
async def test_recognize_user_forwards_display_name_to_repo() -> None:
    """Service-layer forwarding only: a non-None display_name reaches the
    repo's `upsert` call kwargs unchanged.

    Scope honestly: this does NOT cover the repo-layer "refresh display_name
    on the existing row" behavior (that lives in `user_repo.upsert` and
    requires a real or in-memory DB to exercise). The wider "Untitled brand"
    bug class — bootstrap sends a name + repo writes it on conflict — is
    pinned end-to-end only when proper repo-layer test infrastructure lands.

    TODO(repo-tests): once a SQLite-or-Postgres-based UserRepo test harness
    exists, add a case that:
      1. Inserts an AppUser with display_name=NULL.
      2. Calls `user_repo.upsert(..., display_name="Vincent Yang")`.
      3. Asserts the row's display_name is now "Vincent Yang".
    """
    expected = AppUser(
        id=uuid4(),
        oauth_subject="google-oauth2|existing",
        email="existing@mlytics.com",
        display_name="Vincent Yang",
    )
    user_repo = MagicMock()
    user_repo.upsert = AsyncMock(return_value=expected)

    service = _make_service(user_repo)
    user = await service.recognize_user(
        oauth_subject="google-oauth2|existing",
        email="existing@mlytics.com",
        display_name="Vincent Yang",
    )

    assert user.display_name == "Vincent Yang"
    upsert_call = user_repo.upsert.await_args
    assert upsert_call is not None
    assert upsert_call.kwargs.get("display_name") == "Vincent Yang"
