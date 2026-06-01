"""Publisher Dashboard endpoints — placeholder projection over shared insights."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from cortex_api.app.dependencies.capability import requires_publisher_capability
from cortex_api.app.dependencies.publisher import active_publisher
from cortex_api.service.publisher_identity.model.publisher_capability import PublisherCapability
from cortex_api.service.publisher_identity.model.publisher_tenant_ctx import PublisherTenantCtx

router = APIRouter(prefix="/v1/publisher/{publisher_id}/analytics", tags=["publisher_dashboard"])


@router.get(
    "/metrics",
    summary="(Placeholder) Publisher dashboard metrics",
    dependencies=[Depends(requires_publisher_capability(PublisherCapability.VIEW_PUBLISHER_DASHBOARD))],
)
async def summarize_publisher_impact(
    publisher_id: UUID,
    tenant: PublisherTenantCtx = Depends(active_publisher),
) -> dict[str, str]:
    raise HTTPException(status_code=501, detail="publisher_dashboard is post-MVP")
