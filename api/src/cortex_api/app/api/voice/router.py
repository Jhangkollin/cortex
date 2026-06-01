"""Brand-voice endpoints — tenant-scoped start/poll for brand voice jobs.

Pattern mirrors ``app/api/media_network/router.py``: explicit ``/v1/brand``
paths, ``@inject`` + ``Provide[VoiceContainer.job_service]``, ``active_brand``
builds the BrandTenantCtx from JWT claims, capability gate via
``requires_brand_capability``. Service raises ``NotFoundError``; the app's
registered exception handlers map it to HTTP 404.
"""

from __future__ import annotations

from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from cortex_api.app.api.voice.dto import BrandVoiceResponse
from cortex_api.app.dependencies.brand import active_brand
from cortex_api.app.dependencies.capability import requires_brand_capability
from cortex_api.service.brand_identity.model.brand_capability import BrandCapability
from cortex_api.service.brand_identity.model.brand_tenant_ctx import BrandTenantCtx
from cortex_api.service.voice.container import Container as VoiceContainer
from cortex_api.service.voice.job_service import VoiceJobService

router = APIRouter(tags=["brand-voice"])


@router.post(
    "/v1/brand/{brand_id}/brand-voice",
    response_model=BrandVoiceResponse,
    status_code=202,
    summary="Start (or return) an async brand voice job",
    dependencies=[Depends(requires_brand_capability(BrandCapability.EDIT_BRAND_SETTINGS))],
)
@inject
async def start_brand_voice(
    brand_id: UUID,
    regenerate: bool = False,
    tenant: BrandTenantCtx = Depends(active_brand),
    svc: VoiceJobService = Depends(Provide[VoiceContainer.job_service]),
) -> BrandVoiceResponse:
    job = await svc.start(tenant.brand_id, regenerate=regenerate)
    return BrandVoiceResponse.from_model(job)


@router.get(
    "/v1/brand/{brand_id}/brand-voice",
    response_model=BrandVoiceResponse,
    summary="Poll the brand voice job (samples included once succeeded)",
    dependencies=[Depends(requires_brand_capability(BrandCapability.VIEW_BRAND_DASHBOARD))],
)
@inject
async def get_brand_voice(
    brand_id: UUID,
    tenant: BrandTenantCtx = Depends(active_brand),
    svc: VoiceJobService = Depends(Provide[VoiceContainer.job_service]),
) -> BrandVoiceResponse:
    job = await svc.get(tenant.brand_id)
    return BrandVoiceResponse.from_model(job)
