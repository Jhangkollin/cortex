"""Weekly-questions endpoints — tenant-scoped start/poll for brand weekly-questions jobs.

Pattern mirrors ``app/api/media_network/router.py``: explicit ``/v1/brand`` paths,
``@inject`` + ``Provide[QuestionsContainer.job_service]``, ``active_brand`` builds
the BrandTenantCtx from JWT claims, capability gate via
``requires_brand_capability``. Service raises ``NotFoundError``; the app's
registered exception handlers map it to HTTP 404.
"""

from __future__ import annotations

from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from cortex_api.app.api.questions.dto import WeeklyQuestionsResponse
from cortex_api.app.dependencies.brand import active_brand
from cortex_api.app.dependencies.capability import requires_brand_capability
from cortex_api.service.brand_identity.model.brand_capability import BrandCapability
from cortex_api.service.brand_identity.model.brand_tenant_ctx import BrandTenantCtx
from cortex_api.service.questions.container import Container as QuestionsContainer
from cortex_api.service.questions.job_service import QuestionsJobService

router = APIRouter(tags=["weekly-questions"])


@router.post(
    "/v1/brand/{brand_id}/weekly-questions",
    response_model=WeeklyQuestionsResponse,
    status_code=202,
    summary="Start (or return) an async brand weekly-questions job",
    dependencies=[Depends(requires_brand_capability(BrandCapability.EDIT_BRAND_SETTINGS))],
)
@inject
async def start_weekly_questions(
    brand_id: UUID,
    regenerate: bool = False,
    tenant: BrandTenantCtx = Depends(active_brand),
    svc: QuestionsJobService = Depends(Provide[QuestionsContainer.job_service]),
) -> WeeklyQuestionsResponse:
    job = await svc.start(tenant.brand_id, regenerate=regenerate)
    return WeeklyQuestionsResponse.from_model(job)


@router.get(
    "/v1/brand/{brand_id}/weekly-questions",
    response_model=WeeklyQuestionsResponse,
    summary="Poll the brand weekly-questions job (questions included once succeeded)",
    dependencies=[Depends(requires_brand_capability(BrandCapability.VIEW_BRAND_DASHBOARD))],
)
@inject
async def get_weekly_questions(
    brand_id: UUID,
    tenant: BrandTenantCtx = Depends(active_brand),
    svc: QuestionsJobService = Depends(Provide[QuestionsContainer.job_service]),
) -> WeeklyQuestionsResponse:
    job = await svc.get(tenant.brand_id)
    return WeeklyQuestionsResponse.from_model(job)
