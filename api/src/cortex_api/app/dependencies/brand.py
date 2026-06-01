"""Brand tenant resolution Depends.

`active_brand` is the keystone — constructing the BrandTenantCtx is the act
of authorizing the caller for this brand-side route. Zero DB on hot path:
all data comes from JWT claims baked at login.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import Depends

from cortex_api.app.dependencies.auth import authenticated_user
from cortex_api.core.exceptions import ContextMismatchError, WrongContextError
from cortex_api.service.brand_identity.model.brand_capability import BrandCapability
from cortex_api.service.brand_identity.model.brand_role import BrandRole
from cortex_api.service.brand_identity.model.brand_tenant_ctx import BrandTenantCtx
from cortex_api.service.identity.model.authed_user import AuthedUser


def active_brand(
    brand_id: UUID,
    user: AuthedUser = Depends(authenticated_user),
) -> BrandTenantCtx:
    """Build a BrandTenantCtx from the URL `brand_id` and JWT claims.

    Verifies:
    - JWT's active_context.kind is "brand"
    - JWT's active_context.id matches the URL `brand_id`

    Reads role + capabilities pre-resolved in claims; no DB.
    """
    ctx = user.raw_claims.get("active_context")
    if not ctx or ctx.get("kind") != "brand":
        raise WrongContextError("active JWT context is not a brand")

    claim_id = ctx.get("id")
    try:
        claim_uuid = UUID(claim_id) if claim_id else None
    except (TypeError, ValueError) as e:
        raise WrongContextError(f"active_context.id is not a valid UUID: {claim_id!r}") from e
    if claim_uuid != brand_id:
        raise ContextMismatchError(f"URL brand_id {brand_id} does not match active context id {claim_uuid}")

    try:
        role = BrandRole(ctx["role"])
        capabilities = tuple(BrandCapability(c) for c in ctx["capabilities"])
    except (KeyError, ValueError) as e:
        raise WrongContextError(f"active_context has invalid role/capabilities: {e}") from e

    return BrandTenantCtx(
        user_id=user.user_id,
        brand_id=brand_id,
        role=role,
        capabilities=capabilities,
    )
