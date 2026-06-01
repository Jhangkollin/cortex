"""Router-level tests for the three endpoints that resolve an AppUser:

- `GET  /v1/auth/me`
- `POST /v1/auth/resolve-context`
- `POST /v1/brand`

Token-shape dispatch (bootstrap upsert vs session fetch) lives in the
`current_app_user` dep and is covered by
`tests/unit/app/dependencies/test_current_app_user.py`. Here we only verify
the routers wire the dep result into the service call and return a sensible
shape — overriding both `authenticated_user` (the `me` endpoint reads
`raw_claims["active_context"]` for the response) and `current_app_user`
(everything else) via FastAPI's standard `app.dependency_overrides`.

Per CLAUDE.md, prefer `app.dependency_overrides` over reaching into private
container instances or `mock.patch`. The container-level overrides live in
the dispatch-dep test, not here.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from cortex_api import main as cortex_main
from cortex_api.app.api.auth.router import me as me_endpoint
from cortex_api.app.api.auth.router import resolve_context as resolve_context_endpoint
from cortex_api.app.api.brand_identity.router import create_brand as create_brand_endpoint
from cortex_api.app.dependencies.auth import authenticated_user, current_app_user
from cortex_api.service.brand_identity.model.brand import Brand
from cortex_api.service.brand_identity.model.brand_capability import BrandCapability
from cortex_api.service.brand_identity.model.brand_membership import BrandMembership
from cortex_api.service.brand_identity.model.brand_role import BrandRole
from cortex_api.service.brand_identity.model.brand_tenant_ctx import BrandTenantCtx
from cortex_api.service.identity.model.app_user import AppUser
from cortex_api.service.identity.model.authed_user import AuthedUser


def _make_app_user() -> AppUser:
    return AppUser(
        id=uuid4(),
        oauth_subject="116973569897222226602",
        email="vincent@mlytics.com",
        display_name="Vincent Yang",
    )


def _make_authed_user(app_user: AppUser, active_context: dict[str, object] | None = None) -> AuthedUser:
    raw_claims: dict[str, object] = {"sub": str(app_user.id), "email": app_user.email}
    if active_context is not None:
        raw_claims["active_context"] = active_context
    return AuthedUser(
        user_id=app_user.id,
        email=app_user.email,
        display_name=app_user.display_name,
        raw_claims=raw_claims,
    )


@pytest.fixture
def mock_brand_identity_service() -> MagicMock:
    svc = MagicMock()
    svc.list_user_brands = AsyncMock(return_value=[])
    svc.enter_brand = AsyncMock()
    svc.create_brand_with_admin = AsyncMock()
    return svc


@pytest.fixture
def app_user() -> AppUser:
    return _make_app_user()


@pytest.fixture
def client(
    mock_brand_identity_service: MagicMock,
    app_user: AppUser,
) -> Iterator[TestClient]:
    """TestClient with `current_app_user` + `authenticated_user` overridden.

    Brand-side service is still container-overridden because each endpoint
    pulls it via `Depends(Provide[...])`. That's a single seam — the
    multi-seam JWT-shape dispatch the bot flagged is gone (lives in the
    dep now), so test wiring stays small.
    """
    cortex_main.app.dependency_overrides[current_app_user] = lambda: app_user
    cortex_main.app.dependency_overrides[authenticated_user] = lambda: _make_authed_user(app_user)
    cortex_main._brand_identity_container.service.override(mock_brand_identity_service)
    try:
        with TestClient(cortex_main.app) as test_client:
            yield test_client
    finally:
        cortex_main._brand_identity_container.service.reset_override()
        cortex_main.app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# GET /v1/auth/me
# ---------------------------------------------------------------------------


def test_me_returns_resolved_app_user(
    client: TestClient,
    app_user: AppUser,
    mock_brand_identity_service: MagicMock,
) -> None:
    """`me` returns the AppUser resolved by `current_app_user` + memberships."""
    resp = client.get("/v1/auth/me", headers={"Authorization": "Bearer fake"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["user_id"] == str(app_user.id)
    assert body["email"] == app_user.email
    assert body["memberships"] == []
    mock_brand_identity_service.list_user_brands.assert_awaited_once_with(app_user.id)


def test_me_surfaces_active_context_claim(
    mock_brand_identity_service: MagicMock,
    app_user: AppUser,
) -> None:
    """`me` parses `active_context` from raw_claims when present."""
    brand_id = uuid4()
    authed = _make_authed_user(
        app_user,
        active_context={
            "kind": "brand",
            "id": str(brand_id),
            "role": "admin",
            "capabilities": [BrandCapability.VIEW_BRAND_DASHBOARD.value],
        },
    )
    cortex_main.app.dependency_overrides[current_app_user] = lambda: app_user
    cortex_main.app.dependency_overrides[authenticated_user] = lambda: authed
    cortex_main._brand_identity_container.service.override(mock_brand_identity_service)
    try:
        with TestClient(cortex_main.app) as test_client:
            resp = test_client.get("/v1/auth/me", headers={"Authorization": "Bearer fake"})
    finally:
        cortex_main._brand_identity_container.service.reset_override()
        cortex_main.app.dependency_overrides.clear()

    assert resp.status_code == 200, resp.text
    ctx = resp.json()["active_context"]
    assert ctx["kind"] == "brand"
    assert ctx["id"] == str(brand_id)


# ---------------------------------------------------------------------------
# POST /v1/auth/resolve-context
# ---------------------------------------------------------------------------


def test_resolve_context_brand_returns_role_and_capabilities(
    client: TestClient,
    app_user: AppUser,
    mock_brand_identity_service: MagicMock,
) -> None:
    """`resolve-context` for brand kind returns the enter_brand tenant ctx."""
    brand_id = uuid4()
    mock_brand_identity_service.enter_brand.return_value = BrandTenantCtx(
        user_id=app_user.id,
        brand_id=brand_id,
        role=BrandRole.ADMIN,
        capabilities=(BrandCapability.VIEW_BRAND_DASHBOARD,),
    )

    resp = client.post(
        "/v1/auth/resolve-context",
        headers={"Authorization": "Bearer fake"},
        json={"kind": "brand", "id": str(brand_id)},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["kind"] == "brand"
    assert body["id"] == str(brand_id)
    assert body["role"] == "admin"
    assert body["capabilities"] == [BrandCapability.VIEW_BRAND_DASHBOARD.value]
    mock_brand_identity_service.enter_brand.assert_awaited_once_with(app_user.id, brand_id)


def test_resolve_context_publisher_returns_membership_error(
    client: TestClient,
) -> None:
    """Publisher path is stubbed out — surfaces MembershipError (403)."""
    resp = client.post(
        "/v1/auth/resolve-context",
        headers={"Authorization": "Bearer fake"},
        json={"kind": "publisher", "id": str(uuid4())},
    )
    # MembershipError maps to 403 in the exception handler.
    assert resp.status_code == 403, resp.text


# ---------------------------------------------------------------------------
# POST /v1/brand
# ---------------------------------------------------------------------------


def test_create_brand_uses_resolved_app_user(
    client: TestClient,
    app_user: AppUser,
    mock_brand_identity_service: MagicMock,
) -> None:
    """`create_brand` passes the resolved app_user.id to the service."""
    brand_id = uuid4()
    brand = Brand(id=brand_id, display_name="Vincent Yang's brand", created_at=datetime.utcnow())
    membership = BrandMembership(
        user_id=app_user.id,
        brand_id=brand_id,
        role=BrandRole.ADMIN,
        invited_by=None,
    )
    mock_brand_identity_service.create_brand_with_admin.return_value = (brand, membership)

    resp = client.post(
        "/v1/brand",
        headers={"Authorization": "Bearer fake"},
        json={},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["brand"]["id"] == str(brand_id)
    assert body["role"] == BrandRole.ADMIN.value
    mock_brand_identity_service.create_brand_with_admin.assert_awaited_once_with(
        user_id=app_user.id,
        display_name="Vincent Yang's brand",
    )


def test_create_brand_uses_custom_display_name(
    client: TestClient,
    app_user: AppUser,
    mock_brand_identity_service: MagicMock,
) -> None:
    """A body-provided display_name overrides the `{name}'s brand` default."""
    brand_id = uuid4()
    brand = Brand(id=brand_id, display_name="Acme Co", created_at=datetime.utcnow())
    membership = BrandMembership(
        user_id=app_user.id,
        brand_id=brand_id,
        role=BrandRole.ADMIN,
        invited_by=None,
    )
    mock_brand_identity_service.create_brand_with_admin.return_value = (brand, membership)

    resp = client.post(
        "/v1/brand",
        headers={"Authorization": "Bearer fake"},
        json={"display_name": "Acme Co"},
    )
    assert resp.status_code == 201, resp.text
    mock_brand_identity_service.create_brand_with_admin.assert_awaited_once_with(
        user_id=app_user.id,
        display_name="Acme Co",
    )


# ---------------------------------------------------------------------------
# Endpoint references — silence "imported but unused" lints. These imports
# make it explicit which router handlers this file is exercising; tools like
# IDEs and pyright use them for jump-to-definition.
# ---------------------------------------------------------------------------

_ = (me_endpoint, resolve_context_endpoint, create_brand_endpoint)
