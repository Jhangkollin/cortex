"""Brand Dashboard endpoints — `/v1/brand/{brand_id}/analytics/...`."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from cortex_api.app.api.brand_dashboard.dto import (
    ImpactStatsResponse,
    PublisherBreakdownResponse,
    TimeRange,
)
from cortex_api.app.dependencies.brand import active_brand
from cortex_api.app.dependencies.capability import requires_brand_capability
from cortex_api.service.brand_dashboard.model.metrics import BrandMetric
from cortex_api.service.brand_identity.model.brand_capability import BrandCapability
from cortex_api.service.brand_identity.model.brand_tenant_ctx import BrandTenantCtx

router = APIRouter(prefix="/v1/brand/{brand_id}/analytics", tags=["brand_dashboard"])


@router.get(
    "/metrics",
    response_model=ImpactStatsResponse,
    summary="Brand impact stats — 4 KPIs for the active brand",
    dependencies=[Depends(requires_brand_capability(BrandCapability.VIEW_BRAND_DASHBOARD))],
)
async def summarize_brand_impact(
    brand_id: UUID,
    range: TimeRange = Query(default=TimeRange.DAYS_30),
    tenant: BrandTenantCtx = Depends(active_brand),
) -> ImpactStatsResponse:
    # NOTE: scaffold — Slice 1 wires BrandDashboardService.summarize_brand_impact
    raise HTTPException(status_code=501, detail="brand/metrics not yet implemented")


@router.get(
    "/metrics/by-publisher",
    response_model=PublisherBreakdownResponse,
    summary="Per-publisher breakdown for one brand metric",
    dependencies=[Depends(requires_brand_capability(BrandCapability.VIEW_BRAND_DASHBOARD))],
)
async def break_down_by_publisher(
    brand_id: UUID,
    metric: BrandMetric = Query(description="One of: answer_produced, answer_views, llm_citations, brand_clicks"),
    range: TimeRange = Query(default=TimeRange.DAYS_30),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    tenant: BrandTenantCtx = Depends(active_brand),
) -> PublisherBreakdownResponse:
    # NOTE: scaffold — Slice 4 wires BrandDashboardService.break_down_by_publisher
    raise HTTPException(status_code=501, detail="brand/metrics/by-publisher not yet implemented")
