"""Brand identity endpoints — brand creation, metadata, membership management.

Two URL groups, both under `/v1/brand`:
- Collection (`/v1/brand`): self-serve creation
- Resource (`/v1/brand/{brand_id}`): read/update brand + manage members

The smoke test in `tests/unit/test_app_boots.py` expects
`/v1/brand/{brand_id}` and `/v1/brand/{brand_id}/users` to be registered;
this router uses explicit paths (no `prefix`) so both URL groups can share
one router.
"""

from __future__ import annotations

from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status

from cortex_api.app.api.brand_identity.dto import (
    BrandListItem,
    BrandListResponse,
    BrandMembersResponse,
    BrandResponse,
    CreateBrandRequest,
    CreateBrandResponse,
    GrantBrandMembershipRequest,
    OnboardingCompleteResponse,
    OnboardingStatusResponse,
    UpdateBrandRequest,
)
from cortex_api.app.dependencies.auth import current_app_user
from cortex_api.app.dependencies.brand import active_brand
from cortex_api.app.dependencies.capability import requires_brand_capability
from cortex_api.core.exceptions import CortexException, NotImplementedYetError
from cortex_api.service.brand_identity.container import Container as BrandIdentityContainer
from cortex_api.service.brand_identity.model.brand_capability import BrandCapability
from cortex_api.service.brand_identity.model.brand_role import BrandRole
from cortex_api.service.brand_identity.model.brand_tenant_ctx import BrandTenantCtx
from cortex_api.service.brand_identity.policy.brand_capability_policy import (
    BrandCapabilityPolicy,
)
from cortex_api.service.brand_identity.service import BrandIdentityService
from cortex_api.service.identity.model.app_user import AppUser

router = APIRouter(tags=["brand_identity"])


@router.post(
    "/v1/brand",
    response_model=CreateBrandResponse,
    summary="Self-serve: create a new brand workspace + ADMIN membership",
    status_code=status.HTTP_201_CREATED,
)
@inject
async def create_brand(
    body: CreateBrandRequest,
    app_user: AppUser = Depends(current_app_user),
    brand_identity_service: BrandIdentityService = Depends(Provide[BrandIdentityContainer.service]),
) -> CreateBrandResponse:
    """Auto-create a NEW brand workspace for the caller. The first member is
    ADMIN with `brand_membership.invited_by = NULL` (founder). Multi-brand:
    every call creates a fresh, independent brand (its own id + profile) — there
    is no one-brand-per-user limit and no override of existing brands (the
    founder-unique index was dropped in migration `7ab199ba95a2`).

    `display_name` defaults to `"{caller.display_name}'s brand"` when
    omitted, so the workspace has a sensible name from minute one. Wizard /
    settings page can rename via `PATCH /v1/brand/{id}`.
    """
    display_name = (
        body.display_name
        if body.display_name
        else (f"{app_user.display_name}'s brand" if app_user.display_name else "Untitled brand")
    )

    brand, _membership = await brand_identity_service.create_brand_with_admin(
        user_id=app_user.id,
        display_name=display_name,
    )

    # We just created the membership as ADMIN — build the capability list
    # locally rather than re-calling enter_brand (which would re-issue the
    # same membership lookup). Saves one DB roundtrip on the onboarding
    # path. The frontend gets role + capabilities in this response and
    # NextAuth can bake them straight into the next session token.
    capabilities = BrandCapabilityPolicy.resolve(BrandRole.ADMIN)

    return CreateBrandResponse(
        brand=BrandResponse(
            id=brand.id,
            display_name=brand.display_name,
            industry=brand.industry,
            domain=brand.domain,
            created_at=brand.created_at,
        ),
        role=BrandRole.ADMIN,
        capabilities=[c.value for c in capabilities],
    )


@router.get(
    "/v1/brands",
    response_model=BrandListResponse,
)
@inject
async def list_my_brands(
    app_user: AppUser = Depends(current_app_user),
    brand_identity_service: BrandIdentityService = Depends(Provide[BrandIdentityContainer.service]),
) -> BrandListResponse:
    """List the caller's own brands.

    No per-brand capability gate — the result set is intrinsically scoped to
    the caller's memberships. The sidebar switcher (chunk 1) and the
    onboarding-complete portfolio band (chunk 3) consume this.
    """
    rows = await brand_identity_service.list_my_brands(app_user.id)
    return BrandListResponse(
        brands=[
            BrandListItem(
                id=b.id,
                display_name=b.display_name,
                domain=b.domain,
                role=role,
                onboarded_at=b.onboarded_at,
                created_at=b.created_at,
                updated_at=b.updated_at,
            )
            for (b, role) in rows
        ]
    )


@router.get(
    "/v1/brand/{brand_id}",
    response_model=BrandResponse,
    summary="Brand profile for the active brand",
)
@inject
async def get_brand(
    brand_id: UUID,
    tenant: BrandTenantCtx = Depends(active_brand),
    brand_identity_service: BrandIdentityService = Depends(Provide[BrandIdentityContainer.service]),
) -> BrandResponse:
    """Return brand profile data. Any role with membership can read."""
    brand = await brand_identity_service.get_brand(tenant.brand_id)
    return BrandResponse(
        id=brand.id,
        display_name=brand.display_name,
        industry=brand.industry,
        domain=brand.domain,
        created_at=brand.created_at,
    )


@router.patch(
    "/v1/brand/{brand_id}",
    response_model=BrandResponse,
    summary="Update brand profile fields",
    dependencies=[Depends(requires_brand_capability(BrandCapability.EDIT_BRAND_SETTINGS))],
)
@inject
async def update_brand(
    brand_id: UUID,
    body: UpdateBrandRequest,
    tenant: BrandTenantCtx = Depends(active_brand),
    brand_identity_service: BrandIdentityService = Depends(Provide[BrandIdentityContainer.service]),
) -> BrandResponse:
    """Partial update — only fields explicitly provided in the body are
    written. Requires `EDIT_BRAND_SETTINGS` capability (EDITOR or ADMIN).
    """
    brand = await brand_identity_service.update_brand(
        actor=tenant,
        display_name=body.display_name,
        industry=body.industry,
        domain=body.domain,
    )
    return BrandResponse(
        id=brand.id,
        display_name=brand.display_name,
        industry=brand.industry,
        domain=brand.domain,
        created_at=brand.created_at,
    )


@router.get(
    "/v1/brand/{brand_id}/onboarding/status",
    response_model=OnboardingStatusResponse,
    summary="Whether this brand has finished onboarding",
    dependencies=[Depends(requires_brand_capability(BrandCapability.VIEW_BRAND_DASHBOARD))],
)
@inject
async def get_onboarding_status(
    brand_id: UUID,
    tenant: BrandTenantCtx = Depends(active_brand),
    brand_identity_service: BrandIdentityService = Depends(Provide[BrandIdentityContainer.service]),
) -> OnboardingStatusResponse:
    brand = await brand_identity_service.get_brand(tenant.brand_id)
    return OnboardingStatusResponse(onboarded=brand.onboarded_at is not None)


@router.post(
    "/v1/brand/{brand_id}/onboarding/complete",
    response_model=OnboardingCompleteResponse,
    summary="Mark this brand's onboarding complete (idempotent)",
    dependencies=[Depends(requires_brand_capability(BrandCapability.EDIT_BRAND_SETTINGS))],
)
@inject
async def complete_onboarding(
    brand_id: UUID,
    tenant: BrandTenantCtx = Depends(active_brand),
    brand_identity_service: BrandIdentityService = Depends(Provide[BrandIdentityContainer.service]),
) -> OnboardingCompleteResponse:
    brand = await brand_identity_service.mark_onboarded(tenant)
    if brand.onboarded_at is None:
        raise CortexException("mark_onboarded returned brand with onboarded_at=None; service contract violated")
    return OnboardingCompleteResponse(onboarded_at=brand.onboarded_at)


@router.get(
    "/v1/brand/{brand_id}/users",
    response_model=BrandMembersResponse,
    summary="List members of this brand",
    dependencies=[Depends(requires_brand_capability(BrandCapability.MANAGE_BRAND_USERS))],
)
async def list_brand_users(
    brand_id: UUID,
    tenant: BrandTenantCtx = Depends(active_brand),
) -> BrandMembersResponse:
    """List members — admin-only. Future slice will join with app_user
    to surface email + display_name; today returns 501 until that lands."""
    raise NotImplementedYetError("brand member listing not yet implemented")


@router.post(
    "/v1/brand/{brand_id}/users",
    summary="Grant a user a membership in this brand",
    status_code=201,
    dependencies=[Depends(requires_brand_capability(BrandCapability.MANAGE_BRAND_USERS))],
)
async def grant_brand_membership(
    brand_id: UUID,
    body: GrantBrandMembershipRequest,
    tenant: BrandTenantCtx = Depends(active_brand),
) -> dict[str, str]:
    """Stub for the future invitation flow — see project memory
    `project_cortex_mvp.md` § Onboarding flow design. Returns 501 today.
    """
    raise NotImplementedYetError("brand invitation flow not yet implemented")
