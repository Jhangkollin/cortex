"""Media-network endpoints — tenant-scoped start/poll for brand media-network jobs.

Pattern mirrors ``app/api/brand/router.py``: explicit ``/v1/brand`` paths,
``@inject`` + ``Provide[MediaContainer.job_service]``, ``active_brand`` builds
the BrandTenantCtx from JWT claims, capability gate via
``requires_brand_capability``. Service raises ``NotFoundError``; the app's
registered exception handlers map it to HTTP 404.
"""

from __future__ import annotations

from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from cortex_api.app.api.media_network.dto import MediaNetworkResponse
from cortex_api.app.dependencies.brand import active_brand
from cortex_api.app.dependencies.capability import requires_brand_capability
from cortex_api.service.brand_identity.model.brand_capability import BrandCapability
from cortex_api.service.brand_identity.model.brand_tenant_ctx import BrandTenantCtx
from cortex_api.service.media_network.container import Container as MediaContainer
from cortex_api.service.media_network.job_service import MediaNetworkJobService

router = APIRouter(tags=["media-network"])


@router.post(
    "/v1/brand/{brand_id}/media-network",
    response_model=MediaNetworkResponse,
    status_code=202,
    summary="Start (or return) an async brand media-network job",
    dependencies=[Depends(requires_brand_capability(BrandCapability.EDIT_BRAND_SETTINGS))],
)
@inject
async def start_media_network(
    brand_id: UUID,
    regenerate: bool = False,
    tenant: BrandTenantCtx = Depends(active_brand),
    svc: MediaNetworkJobService = Depends(Provide[MediaContainer.job_service]),
) -> MediaNetworkResponse:
    job = await svc.start(tenant.brand_id, regenerate=regenerate)
    return MediaNetworkResponse.from_model(job)


@router.get(
    "/v1/brand/{brand_id}/media-network",
    response_model=MediaNetworkResponse,
    summary="Poll the brand media-network job (outlets included once succeeded)",
    dependencies=[Depends(requires_brand_capability(BrandCapability.VIEW_BRAND_DASHBOARD))],
)
@inject
async def get_media_network(
    brand_id: UUID,
    tenant: BrandTenantCtx = Depends(active_brand),
    svc: MediaNetworkJobService = Depends(Provide[MediaContainer.job_service]),
) -> MediaNetworkResponse:
    job = await svc.get(tenant.brand_id)
    return MediaNetworkResponse.from_model(job)
