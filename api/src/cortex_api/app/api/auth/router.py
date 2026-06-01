"""Auth endpoints — whoami + capability resolution.

Pattern B JWT — OAuth happens in cortex-web (NextAuth), which signs all
session JWTs. cortex-api **enriches** those JWTs via callback (does NOT mint
its own). Two endpoints:

- `GET /v1/auth/me` — upserts AppUser, returns user + memberships.
- `POST /v1/auth/resolve-context` — verifies membership, returns role +
  capabilities so NextAuth's `jwt` callback can bake them into the next
  signed session.

NextAuth's `jwt` callback in cortex-web calls both on first sign-in /
context switch. The frontend never calls `resolve-context` directly.
"""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from cortex_api.app.api.auth.dto import (
    ActiveContextResponse,
    MembershipSummary,
    MeResponse,
    ResolveContextRequest,
)
from cortex_api.app.dependencies.auth import authenticated_user, current_app_user
from cortex_api.core.exceptions import BadRequestError, MembershipError
from cortex_api.service.brand_identity.container import Container as BrandIdentityContainer
from cortex_api.service.brand_identity.service import BrandIdentityService
from cortex_api.service.identity.model.app_user import AppUser
from cortex_api.service.identity.model.authed_user import AuthedUser

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.get("/me", response_model=MeResponse, summary="Whoami + memberships")
@inject
async def me(
    user: AuthedUser = Depends(authenticated_user),
    app_user: AppUser = Depends(current_app_user),
    brand_identity_service: BrandIdentityService = Depends(Provide[BrandIdentityContainer.service]),
) -> MeResponse:
    """Return the calling user + their memberships.

    Does NOT auto-create brands; that's `POST /v1/brand` (explicit, on
    persona picker). Active context is read from JWT claims if present
    (set by NextAuth's jwt callback after a prior `resolve-context`
    round-trip).
    """
    # Memberships across both bounded contexts.
    brand_memberships = await brand_identity_service.list_user_brands(app_user.id)
    memberships: list[MembershipSummary] = [
        MembershipSummary(
            kind="brand",
            id=brand.id,
            display_name=brand.display_name,
            role=ctx.role.value,
        )
        for (brand, ctx) in brand_memberships
    ]
    # (publisher memberships will be added by the publisher_identity slice when it lands)

    # Active context from JWT (already verified upstream by `authenticated_user`).
    active_ctx: ActiveContextResponse | None = None
    claim_ctx = user.raw_claims.get("active_context")
    if isinstance(claim_ctx, dict) and claim_ctx.get("kind") and claim_ctx.get("id"):
        try:
            active_ctx = ActiveContextResponse(
                kind=claim_ctx["kind"],
                id=UUID(str(claim_ctx["id"])),
                role=str(claim_ctx.get("role", "")),
                capabilities=list(claim_ctx.get("capabilities", [])),
            )
        except (ValueError, TypeError):
            # Malformed claim — log via the regular pipeline and just omit.
            active_ctx = None

    return MeResponse(
        user_id=app_user.id,
        email=app_user.email,
        display_name=app_user.display_name,
        active_context=active_ctx,
        memberships=memberships,
    )


@router.post(
    "/resolve-context",
    response_model=ActiveContextResponse,
    summary="Resolve role + capabilities for a chosen membership",
)
@inject
async def resolve_context(
    body: ResolveContextRequest,
    app_user: AppUser = Depends(current_app_user),
    brand_identity_service: BrandIdentityService = Depends(Provide[BrandIdentityContainer.service]),
) -> ActiveContextResponse:
    """Verify the user has a membership for `(kind, id)` and return its
    resolved role + capability set.

    Called by NextAuth's `jwt` callback at sign-in / context switch — the
    callback writes the response straight into the NextAuth token's
    `active_context` claim. cortex-api never sees the resulting JWT
    (NextAuth signs it locally); cortex-api only verifies signatures on
    subsequent requests.
    """
    kind: Literal["brand", "publisher"] = body.kind
    if kind == "brand":
        ctx = await brand_identity_service.enter_brand(app_user.id, body.id)
        return ActiveContextResponse(
            kind="brand",
            id=ctx.brand_id,
            role=ctx.role.value,
            capabilities=[c.value for c in ctx.capabilities],
        )
    if kind == "publisher":
        # Publisher resolution will be implemented when publisher_identity
        # ships. For now, return a 400 so the frontend can de-grade.
        raise MembershipError("publisher contexts are not yet implemented in cortex-api")
    raise BadRequestError(f"unknown context kind: {kind!r}")
