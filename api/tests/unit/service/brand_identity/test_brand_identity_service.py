"""Unit tests for BrandIdentityService.

Mocks the DB session + repos so the business logic is exercised in
isolation. The DB-level invariants (FK constraints, UNIQUE on
(user_id, brand_id)) are covered by the alembic migration + the
end-to-end UAT verification — not these tests.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from cortex_api.core.exceptions import ForbiddenError, MembershipError
from cortex_api.service.brand_identity.config import Config
from cortex_api.service.brand_identity.model.brand import Brand
from cortex_api.service.brand_identity.model.brand_capability import BrandCapability
from cortex_api.service.brand_identity.model.brand_membership import BrandMembership
from cortex_api.service.brand_identity.model.brand_role import BrandRole
from cortex_api.service.brand_identity.model.brand_tenant_ctx import BrandTenantCtx
from cortex_api.service.brand_identity.policy.brand_capability_policy import (
    BrandCapabilityPolicy,
)
from cortex_api.service.brand_identity.service import BrandIdentityService


def _make_service(
    membership_repo: MagicMock,
    brand_repo: MagicMock,
) -> BrandIdentityService:
    """Build a BrandIdentityService with mocked deps + an async-context-yielding session."""
    session = MagicMock()
    db_client = MagicMock()

    @asynccontextmanager
    async def _session() -> AsyncIterator[MagicMock]:
        yield session

    db_client.session = _session
    return BrandIdentityService(
        database_client=db_client,
        brand_repo=brand_repo,
        membership_repo=membership_repo,
        config=Config(),
    )


def _admin_ctx(user_id: UUID, brand_id: UUID) -> BrandTenantCtx:
    return BrandTenantCtx(
        user_id=user_id,
        brand_id=brand_id,
        role=BrandRole.ADMIN,
        capabilities=BrandCapabilityPolicy.resolve(BrandRole.ADMIN),
    )


def _viewer_ctx(user_id: UUID, brand_id: UUID) -> BrandTenantCtx:
    return BrandTenantCtx(
        user_id=user_id,
        brand_id=brand_id,
        role=BrandRole.VIEWER,
        capabilities=BrandCapabilityPolicy.resolve(BrandRole.VIEWER),
    )


# ---------------------------------------------------------------------------
# create_brand_with_admin
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_brand_with_admin_success() -> None:
    """First-time founder: creates brand + ADMIN membership."""
    user_id = uuid4()

    membership_repo = MagicMock()
    membership_repo.create = AsyncMock(side_effect=lambda _s, m: m)

    brand_repo = MagicMock()
    brand_repo.create = AsyncMock(side_effect=lambda _s, b: b)

    service = _make_service(membership_repo, brand_repo)
    brand, membership = await service.create_brand_with_admin(
        user_id=user_id,
        display_name="Acme Brands",
    )

    assert brand.display_name == "Acme Brands"
    assert isinstance(brand, Brand)
    assert isinstance(membership, BrandMembership)
    assert membership.user_id == user_id
    assert membership.brand_id == brand.id
    assert membership.role == BrandRole.ADMIN
    assert membership.invited_by is None  # founder semantic


@pytest.mark.asyncio
async def test_create_brand_with_admin_allows_multiple_brands_per_user() -> None:
    """Multi-brand: a user can found more than one independent brand.

    The old one-founder-per-user partial UNIQUE index was dropped (migration
    7ab199ba95a2), so two `create_brand_with_admin` calls for the same user
    both succeed — each yields a distinct brand + its own ADMIN founder
    membership, with no override.
    """
    user_id = uuid4()

    membership_repo = MagicMock()
    membership_repo.create = AsyncMock(side_effect=lambda _s, m: m)

    brand_repo = MagicMock()
    brand_repo.create = AsyncMock(side_effect=lambda _s, b: b)

    service = _make_service(membership_repo, brand_repo)

    brand1, m1 = await service.create_brand_with_admin(user_id=user_id, display_name="Brand One")
    brand2, m2 = await service.create_brand_with_admin(user_id=user_id, display_name="Brand Two")

    assert brand1.id != brand2.id  # independent brands, no override
    assert m1.brand_id == brand1.id and m2.brand_id == brand2.id
    assert m1.user_id == user_id and m2.user_id == user_id
    assert m1.role == BrandRole.ADMIN and m2.role == BrandRole.ADMIN
    assert m1.invited_by is None and m2.invited_by is None  # both founders
    assert membership_repo.create.await_count == 2


# ---------------------------------------------------------------------------
# update_brand — capability gate
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_brand_admin_succeeds() -> None:
    """ADMIN has EDIT_BRAND_SETTINGS → update applied."""
    user_id = uuid4()
    brand_id = uuid4()
    existing_brand = Brand(id=brand_id, display_name="Old name")

    membership_repo = MagicMock()
    brand_repo = MagicMock()
    brand_repo.get_by_id = AsyncMock(return_value=existing_brand)

    async def _update_fields(_session: object, brand: Brand, **fields: object) -> Brand:
        for k, v in fields.items():
            setattr(brand, k, v)
        return brand

    brand_repo.update_fields = AsyncMock(side_effect=_update_fields)

    service = _make_service(membership_repo, brand_repo)
    updated = await service.update_brand(
        actor=_admin_ctx(user_id, brand_id),
        display_name="New name",
        industry="fintech",
    )

    assert updated.display_name == "New name"
    assert updated.industry == "fintech"
    brand_repo.update_fields.assert_called_once()


@pytest.mark.asyncio
async def test_update_brand_viewer_forbidden() -> None:
    """VIEWER lacks EDIT_BRAND_SETTINGS → ForbiddenError (HTTP 403)."""
    user_id = uuid4()
    brand_id = uuid4()

    membership_repo = MagicMock()
    brand_repo = MagicMock()
    brand_repo.get_by_id = AsyncMock()
    brand_repo.update_fields = AsyncMock()

    service = _make_service(membership_repo, brand_repo)
    with pytest.raises(ForbiddenError, match="edit_brand_settings"):
        await service.update_brand(
            actor=_viewer_ctx(user_id, brand_id),
            display_name="New",
        )

    # Forbidden should fail BEFORE any DB hit.
    brand_repo.get_by_id.assert_not_called()
    brand_repo.update_fields.assert_not_called()


# ---------------------------------------------------------------------------
# enter_brand — capability resolution + non-member rejection
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_enter_brand_resolves_capabilities_by_role() -> None:
    """Successful enter → BrandTenantCtx with capabilities from the role.

    The brand row is not fetched — FK on brand_membership.brand_id
    guarantees the brand exists whenever a membership row exists. So
    `brand_repo.get_by_id` is NOT expected to be called.
    """
    user_id = uuid4()
    brand_id = uuid4()
    membership = BrandMembership(user_id=user_id, brand_id=brand_id, role=BrandRole.EDITOR)

    membership_repo = MagicMock()
    membership_repo.get = AsyncMock(return_value=membership)
    brand_repo = MagicMock()
    brand_repo.get_by_id = AsyncMock()  # should NOT be called

    service = _make_service(membership_repo, brand_repo)
    ctx = await service.enter_brand(user_id, brand_id)

    assert ctx.user_id == user_id
    assert ctx.brand_id == brand_id
    assert ctx.role == BrandRole.EDITOR
    # EDITOR has EDIT_BRAND_SETTINGS but not MANAGE_BRAND_USERS
    assert BrandCapability.EDIT_BRAND_SETTINGS in ctx.capabilities
    assert BrandCapability.MANAGE_BRAND_USERS not in ctx.capabilities
    # No defensive brand fetch — FK is the source of truth.
    brand_repo.get_by_id.assert_not_called()


@pytest.mark.asyncio
async def test_enter_brand_non_member_raises() -> None:
    """No membership row → MembershipError (HTTP 403)."""
    user_id = uuid4()
    brand_id = uuid4()

    membership_repo = MagicMock()
    membership_repo.get = AsyncMock(return_value=None)
    brand_repo = MagicMock()
    brand_repo.get_by_id = AsyncMock()  # should NOT be called

    service = _make_service(membership_repo, brand_repo)
    with pytest.raises(MembershipError, match="no membership"):
        await service.enter_brand(user_id, brand_id)

    brand_repo.get_by_id.assert_not_called()


# ---------------------------------------------------------------------------
# BrandCapabilityPolicy — sanity that role → capabilities is stable
# ---------------------------------------------------------------------------


def test_capability_policy_admin_has_all() -> None:
    caps = BrandCapabilityPolicy.resolve(BrandRole.ADMIN)
    assert set(caps) == set(BrandCapability)


def test_capability_policy_viewer_has_view_only() -> None:
    caps = BrandCapabilityPolicy.resolve(BrandRole.VIEWER)
    cap_set = set(caps)
    assert BrandCapability.VIEW_BRAND_DASHBOARD in cap_set
    assert BrandCapability.EDIT_BRAND_SETTINGS not in cap_set
    assert BrandCapability.MANAGE_BRAND_USERS not in cap_set


# ---------------------------------------------------------------------------
# mark_onboarded — idempotent onboarding stamp
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mark_onboarded_stamps_when_null() -> None:
    """First call: onboarded_at is None → stamps with a datetime."""
    user_id = uuid4()
    brand_id = uuid4()
    existing_brand = Brand(id=brand_id, display_name="Acme", onboarded_at=None)

    membership_repo = MagicMock()
    brand_repo = MagicMock()
    brand_repo.get_by_id = AsyncMock(return_value=existing_brand)

    async def _update_fields(_session: object, brand: Brand, **fields: object) -> Brand:
        for k, v in fields.items():
            setattr(brand, k, v)
        return brand

    brand_repo.update_fields = AsyncMock(side_effect=_update_fields)

    service = _make_service(membership_repo, brand_repo)
    brand = await service.mark_onboarded(_admin_ctx(user_id, brand_id))

    assert brand.onboarded_at is not None
    brand_repo.update_fields.assert_called_once()


@pytest.mark.asyncio
async def test_mark_onboarded_is_idempotent() -> None:
    """Second call: onboarded_at already set → no update_fields call, same timestamp returned."""
    user_id = uuid4()
    brand_id = uuid4()
    stamp = datetime(2024, 1, 1, 12, 0, 0)
    existing_brand = Brand(id=brand_id, display_name="Acme", onboarded_at=stamp)

    membership_repo = MagicMock()
    brand_repo = MagicMock()
    brand_repo.get_by_id = AsyncMock(return_value=existing_brand)
    brand_repo.update_fields = AsyncMock()

    service = _make_service(membership_repo, brand_repo)
    result = await service.mark_onboarded(_admin_ctx(user_id, brand_id))

    assert result.onboarded_at == stamp
    brand_repo.update_fields.assert_not_called()


@pytest.mark.asyncio
async def test_mark_onboarded_requires_edit_capability() -> None:
    """VIEWER lacks EDIT_BRAND_SETTINGS → ForbiddenError before any DB hit."""
    user_id = uuid4()
    brand_id = uuid4()

    membership_repo = MagicMock()
    brand_repo = MagicMock()
    brand_repo.get_by_id = AsyncMock()
    brand_repo.update_fields = AsyncMock()

    service = _make_service(membership_repo, brand_repo)
    with pytest.raises(ForbiddenError, match="edit_brand_settings"):
        await service.mark_onboarded(_viewer_ctx(user_id, brand_id))

    brand_repo.get_by_id.assert_not_called()
    brand_repo.update_fields.assert_not_called()
