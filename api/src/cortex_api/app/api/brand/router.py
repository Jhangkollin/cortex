"""Brand profile endpoints — tenant-scoped read/write.

Pattern mirrors `app/api/brand_identity/router.py`: explicit `/v1/brand`
paths, `@inject` + `Provide[BrandContainer.service]`, `active_brand` builds
the BrandTenantCtx from JWT claims, capability gates via
`requires_brand_capability`. Service raises `NotFoundError`; the app's
registered exception handlers map it to HTTP 404.
"""

from __future__ import annotations

import contextlib
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from cortex_api.app.api.brand.dto import (
    AnalyzeJobDTO,
    AnalyzeRequest,
    BrandProfileResponse,
    UpsertProfileRequest,
)
from cortex_api.app.dependencies.brand import active_brand
from cortex_api.app.dependencies.capability import requires_brand_capability
from cortex_api.core.exceptions import NotFoundError
from cortex_api.service.brand.analyze_service import AnalyzeJobService
from cortex_api.service.brand.container import Container as BrandContainer
from cortex_api.service.brand.model.analysis_job import AnalyzeJobStatus
from cortex_api.service.brand.service import BrandService
from cortex_api.service.brand_identity.model.brand_capability import BrandCapability
from cortex_api.service.brand_identity.model.brand_tenant_ctx import BrandTenantCtx

router = APIRouter(tags=["brand"])


@router.get(
    "/v1/brand/{brand_id}/profile",
    response_model=BrandProfileResponse,
    summary="Get the brand's current profile",
    dependencies=[Depends(requires_brand_capability(BrandCapability.VIEW_BRAND_DASHBOARD))],
)
@inject
async def get_brand_profile(
    brand_id: UUID,
    tenant: BrandTenantCtx = Depends(active_brand),
    brand_service: BrandService = Depends(Provide[BrandContainer.service]),
) -> BrandProfileResponse:
    profile = await brand_service.get_profile(tenant.brand_id)
    return BrandProfileResponse.from_model(profile)


@router.put(
    "/v1/brand/{brand_id}/profile",
    response_model=BrandProfileResponse,
    summary="Upsert (insert-or-replace) the brand's current profile",
    dependencies=[Depends(requires_brand_capability(BrandCapability.EDIT_BRAND_SETTINGS))],
)
@inject
async def upsert_brand_profile(
    brand_id: UUID,
    body: UpsertProfileRequest,
    tenant: BrandTenantCtx = Depends(active_brand),
    brand_service: BrandService = Depends(Provide[BrandContainer.service]),
) -> BrandProfileResponse:
    saved = await brand_service.upsert_profile(tenant.brand_id, body.to_model(tenant.brand_id))
    return BrandProfileResponse.from_model(saved)


@router.post(
    "/v1/brand/{brand_id}/profile/analyze",
    response_model=AnalyzeJobDTO,
    status_code=202,
    summary="Start an async brand-profile extraction job",
    dependencies=[Depends(requires_brand_capability(BrandCapability.EDIT_BRAND_SETTINGS))],
)
@inject
async def start_brand_analyze(
    brand_id: UUID,
    body: AnalyzeRequest,
    tenant: BrandTenantCtx = Depends(active_brand),
    analyze_service: AnalyzeJobService = Depends(Provide[BrandContainer.analyze_service]),
) -> AnalyzeJobDTO:
    job = await analyze_service.start_analyze(tenant.brand_id, body.url)
    return AnalyzeJobDTO.from_model(job, profile=None)


@router.get(
    "/v1/brand/{brand_id}/profile/analyze/{job_id}",
    response_model=AnalyzeJobDTO,
    summary="Poll an analyze job (profile included once succeeded)",
    dependencies=[Depends(requires_brand_capability(BrandCapability.VIEW_BRAND_DASHBOARD))],
)
@inject
async def get_brand_analyze_job(
    brand_id: UUID,
    job_id: UUID,
    tenant: BrandTenantCtx = Depends(active_brand),
    analyze_service: AnalyzeJobService = Depends(Provide[BrandContainer.analyze_service]),
    brand_service: BrandService = Depends(Provide[BrandContainer.service]),
) -> AnalyzeJobDTO:
    job = await analyze_service.get_job(tenant.brand_id, job_id)
    profile = None
    if job.status == AnalyzeJobStatus.SUCCEEDED:
        # Tolerate only the benign succeeded-but-profile-not-yet-readable race;
        # real infra errors must still propagate to the 500 handler, not be
        # masked as {"status":"succeeded","profile":null}.
        with contextlib.suppress(NotFoundError):
            profile = await brand_service.get_profile(tenant.brand_id)
    return AnalyzeJobDTO.from_model(job, profile=profile)
