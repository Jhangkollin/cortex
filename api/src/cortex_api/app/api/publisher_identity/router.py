"""Publisher identity endpoints — mirror of brand_identity router."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from cortex_api.app.api.publisher_identity.dto import (
    GrantPublisherMembershipRequest,
    PublisherMembersResponse,
    PublisherResponse,
)
from cortex_api.app.dependencies.capability import requires_publisher_capability
from cortex_api.app.dependencies.publisher import active_publisher
from cortex_api.service.publisher_identity.model.publisher_capability import PublisherCapability
from cortex_api.service.publisher_identity.model.publisher_tenant_ctx import PublisherTenantCtx

router = APIRouter(prefix="/v1/publisher/{publisher_id}", tags=["publisher_identity"])


@router.get(
    "",
    response_model=PublisherResponse,
    summary="Publisher profile for the active publisher",
)
async def get_publisher(
    publisher_id: UUID,
    tenant: PublisherTenantCtx = Depends(active_publisher),
) -> PublisherResponse:
    raise HTTPException(status_code=501, detail="publisher_identity GET not yet implemented")


@router.get(
    "/users",
    response_model=PublisherMembersResponse,
    summary="List members of this publisher",
    dependencies=[Depends(requires_publisher_capability(PublisherCapability.MANAGE_PUBLISHER_USERS))],
)
async def list_publisher_users(
    publisher_id: UUID,
    tenant: PublisherTenantCtx = Depends(active_publisher),
) -> PublisherMembersResponse:
    raise HTTPException(status_code=501, detail="publisher_identity list users not yet implemented")


@router.post(
    "/users",
    summary="Grant a user a membership in this publisher",
    status_code=201,
    dependencies=[Depends(requires_publisher_capability(PublisherCapability.MANAGE_PUBLISHER_USERS))],
)
async def grant_publisher_membership(
    publisher_id: UUID,
    body: GrantPublisherMembershipRequest,
    tenant: PublisherTenantCtx = Depends(active_publisher),
) -> dict[str, str]:
    raise HTTPException(status_code=501, detail="publisher_identity grant not yet implemented")
