"""F2 — GET /v1/publishers/{publisher_uuid}/eligible-brands.

Protected by ServiceBearerMiddleware (path-scoped to /v1/publishers/*).
"""

from __future__ import annotations

from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query

from cortex_api.app.api.eligible_brands.dto import EligibleBrandDTO
from cortex_api.service.brand.container import Container as BrandContainer
from cortex_api.service.placement.service.eligible_brands_service import EligibleBrandsService

router = APIRouter(tags=["eligible-brands"])


@router.get(
    "/v1/publishers/{publisher_uuid}/eligible-brands",
    response_model=list[EligibleBrandDTO],
)
@inject
async def list_eligible_brands(
    publisher_uuid: UUID,
    lang: str = Query(...),
    service: EligibleBrandsService = Depends(Provide[BrandContainer.eligible_brands_service]),
) -> list[EligibleBrandDTO]:
    payload = await service.list_eligible(publisher_uuid=publisher_uuid, lang=lang)
    return [EligibleBrandDTO.model_validate(item) for item in payload]
