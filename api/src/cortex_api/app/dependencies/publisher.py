"""Publisher tenant resolution Depends. Mirror of brand.py."""

from __future__ import annotations

from uuid import UUID

from fastapi import Depends

from cortex_api.app.dependencies.auth import authenticated_user
from cortex_api.core.exceptions import ContextMismatchError, WrongContextError
from cortex_api.service.identity.model.authed_user import AuthedUser
from cortex_api.service.publisher_identity.model.publisher_capability import PublisherCapability
from cortex_api.service.publisher_identity.model.publisher_role import PublisherRole
from cortex_api.service.publisher_identity.model.publisher_tenant_ctx import PublisherTenantCtx


def active_publisher(
    publisher_id: UUID,
    user: AuthedUser = Depends(authenticated_user),
) -> PublisherTenantCtx:
    """Build a PublisherTenantCtx from the URL `publisher_id` and JWT claims."""
    ctx = user.raw_claims.get("active_context")
    if not ctx or ctx.get("kind") != "publisher":
        raise WrongContextError("active JWT context is not a publisher")

    claim_id = ctx.get("id")
    try:
        claim_uuid = UUID(claim_id) if claim_id else None
    except (TypeError, ValueError) as e:
        raise WrongContextError(f"active_context.id is not a valid UUID: {claim_id!r}") from e
    if claim_uuid != publisher_id:
        raise ContextMismatchError(f"URL publisher_id {publisher_id} does not match active context id {claim_uuid}")

    try:
        role = PublisherRole(ctx["role"])
        capabilities = tuple(PublisherCapability(c) for c in ctx["capabilities"])
    except (KeyError, ValueError) as e:
        raise WrongContextError(f"active_context has invalid role/capabilities: {e}") from e

    return PublisherTenantCtx(
        user_id=user.user_id,
        publisher_id=publisher_id,
        role=role,
        capabilities=capabilities,
    )
