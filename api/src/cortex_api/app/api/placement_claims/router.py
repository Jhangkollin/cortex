"""F2b — POST /v1/publishers/{publisher_uuid}/placement-claims and /complete.

Protected by ``ServiceBearerMiddleware`` (already path-scoped to
``/v1/publishers/*`` in main.py — no extra wiring).
"""

from __future__ import annotations

from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Query

from cortex_api.app.api.eligible_brands.dto import EligibleBrandDTO
from cortex_api.app.api.placement_claims.dto import (
    ClaimRequest,
    ClaimResponse,
    CompleteRequest,
    DeleteClaimResponse,
)
from cortex_api.service.brand.container import Container as BrandContainer
from cortex_api.service.placement.model.placement_compute_claim import (
    PlacementClaimStatus,
)
from cortex_api.service.placement.service.placement_claim_service import (
    PlacementClaimService,
)

router = APIRouter(tags=["placement-claims"])


@router.post(
    "/v1/publishers/{publisher_uuid}/placement-claims",
    response_model=ClaimResponse,
)
@inject
async def claim_placement(
    publisher_uuid: UUID,
    body: ClaimRequest,
    lang: str = Query(...),
    service: PlacementClaimService = Depends(Provide[BrandContainer.placement_claim_service]),
) -> ClaimResponse:
    outcome, eligible = await service.claim(
        publisher_uuid=publisher_uuid,
        article_url=body.article_url,
        agent_ws_request_id=body.agent_ws_request_id,
        lang=lang,
    )
    return ClaimResponse(
        winner=outcome.winner,
        claim_id=outcome.claim_id,
        expires_at=outcome.expires_at,
        eligible_brands=[EligibleBrandDTO.model_validate(item) for item in eligible],
    )


@router.delete("/v1/publishers/{publisher_uuid}/placement-claims", response_model=DeleteClaimResponse)
@inject
async def delete_placement_claim(
    publisher_uuid: UUID,
    article_url: str = Query(...),
    service: PlacementClaimService = Depends(Provide[BrandContainer.placement_claim_service]),
) -> DeleteClaimResponse:
    deleted = await service.delete_claim(
        publisher_uuid=publisher_uuid,
        article_url=article_url,
    )
    return DeleteClaimResponse(deleted=deleted)


@router.post(
    "/v1/publishers/{publisher_uuid}/placement-claims/{claim_id}/complete",
)
@inject
async def complete_placement_claim(
    publisher_uuid: UUID,
    claim_id: UUID,
    body: CompleteRequest,
    service: PlacementClaimService = Depends(Provide[BrandContainer.placement_claim_service]),
) -> dict[str, bool]:
    ok = await service.complete(
        publisher_uuid=publisher_uuid,
        claim_id=claim_id,
        status=PlacementClaimStatus(body.status),
        placement_audit_id=body.placement_audit_id,
    )
    if not ok:
        raise HTTPException(status_code=404, detail="claim not found")
    return {"ok": True}
