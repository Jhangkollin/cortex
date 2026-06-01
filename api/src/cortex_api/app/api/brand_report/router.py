"""Brand IQ Report endpoints — tenant-scoped async report generation + polling.

Pattern mirrors `app/api/brand/router.py`: explicit `/v1/brand` paths,
`@inject` + `Provide[BrandReportContainer.*]`, `active_brand` builds the
BrandTenantCtx from JWT claims, capability gates via
`requires_brand_capability`. Service raises `NotFoundError`; the app's
registered exception handlers map it to HTTP 404.

``generate_report`` uses ``job_service`` (lifecycle); ``get_report`` and
``list_reports`` use ``service`` (read-only).  ``download_report_pdf`` uses
``pdf_service`` (render + download).
"""

from __future__ import annotations

from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from fastapi.responses import Response

from cortex_api.app.api.brand_report.dto import (
    GenerateReportResponse,
    ReportEnvelope,
    ReportUiStateResponse,
    ReportVersionItem,
)
from cortex_api.app.dependencies.brand import active_brand
from cortex_api.app.dependencies.capability import requires_brand_capability
from cortex_api.service.brand_identity.model.brand_capability import BrandCapability
from cortex_api.service.brand_identity.model.brand_tenant_ctx import BrandTenantCtx
from cortex_api.service.brand_report.container import Container as BrandReportContainer
from cortex_api.service.brand_report.job_service import BrandReportJobService
from cortex_api.service.brand_report.pdf_service import BrandReportPdfService, build_content_disposition
from cortex_api.service.brand_report.service import BrandReportService
from cortex_api.service.brand_report.ui_state_service import BrandReportUiStateService

router = APIRouter(tags=["brand_report"])
_VIEW = Depends(requires_brand_capability(BrandCapability.VIEW_BRAND_DASHBOARD))


@router.post(
    "/v1/brand/{brand_id}/report",
    response_model=GenerateReportResponse,
    status_code=202,
    summary="Generate a Brand IQ report (async)",
    dependencies=[_VIEW],
)
@inject
async def generate_report(
    brand_id: UUID,
    tenant: BrandTenantCtx = Depends(active_brand),
    job_service: BrandReportJobService = Depends(Provide[BrandReportContainer.job_service]),
) -> GenerateReportResponse:
    row = await job_service.generate(tenant.brand_id)
    return GenerateReportResponse.from_model(
        row,
        brand_id=tenant.brand_id,
        estimated_seconds=job_service.estimated_seconds,
    )


# ---------------------------------------------------------------------------
# UI-state routes (COR-82).
#
# ROUTE ORDERING IS LOAD-BEARING: these STATIC `.../report/ui-state*` paths
# MUST be declared BEFORE the parameterized `.../report/{report_id}` route
# below. Starlette matches routes in declaration order — if `{report_id}` came
# first, a request to `.../report/ui-state` would bind `report_id="ui-state"`
# and the ui-state handlers would be unreachable (the GET would 404). Do not
# reorder these below the `{report_id}` route.
# ---------------------------------------------------------------------------


@router.get(
    "/v1/brand/{brand_id}/report/ui-state",
    response_model=ReportUiStateResponse,
    summary="Get report UI-state flags (celebratePending, heroDismissed)",
    dependencies=[_VIEW],
)
@inject
async def get_report_ui_state(
    brand_id: UUID,
    tenant: BrandTenantCtx = Depends(active_brand),
    ui_state_service: BrandReportUiStateService = Depends(Provide[BrandReportContainer.ui_state_service]),
) -> ReportUiStateResponse:
    state = await ui_state_service.get_ui_state(tenant.brand_id)
    return ReportUiStateResponse(
        celebratePending=state.celebrate_pending,
        heroDismissed=state.hero_dismissed,
        celebrateReady=state.celebrate_ready,
    )


@router.post(
    "/v1/brand/{brand_id}/report/ui-state/arm",
    status_code=204,
    summary="Arm the celebration flag (called at onboarding completion)",
    dependencies=[_VIEW],
)
@inject
async def arm_report_celebrate(
    brand_id: UUID,
    tenant: BrandTenantCtx = Depends(active_brand),
    ui_state_service: BrandReportUiStateService = Depends(Provide[BrandReportContainer.ui_state_service]),
) -> None:
    await ui_state_service.arm_celebrate(tenant.brand_id)


@router.post(
    "/v1/brand/{brand_id}/report/ui-state/celebrate-consume",
    status_code=204,
    summary="Consume the celebration flag (idempotent; called on first Discover visit)",
    dependencies=[_VIEW],
)
@inject
async def consume_report_celebrate(
    brand_id: UUID,
    tenant: BrandTenantCtx = Depends(active_brand),
    ui_state_service: BrandReportUiStateService = Depends(Provide[BrandReportContainer.ui_state_service]),
) -> None:
    await ui_state_service.consume_celebrate(tenant.brand_id)


@router.post(
    "/v1/brand/{brand_id}/report/ui-state/hero-dismiss",
    status_code=204,
    summary="Dismiss the Brand IQ Report hero card (permanent)",
    dependencies=[_VIEW],
)
@inject
async def dismiss_report_hero(
    brand_id: UUID,
    tenant: BrandTenantCtx = Depends(active_brand),
    ui_state_service: BrandReportUiStateService = Depends(Provide[BrandReportContainer.ui_state_service]),
) -> None:
    await ui_state_service.dismiss_hero(tenant.brand_id)


@router.get(
    "/v1/brand/{brand_id}/report/{report_id}",
    response_model=ReportEnvelope,
    summary="Fetch a report (poll until ready)",
    dependencies=[_VIEW],
)
@inject
async def get_report(
    brand_id: UUID,
    report_id: str,
    tenant: BrandTenantCtx = Depends(active_brand),
    service: BrandReportService = Depends(Provide[BrandReportContainer.service]),
) -> ReportEnvelope:
    return ReportEnvelope.from_model(await service.get_report(tenant.brand_id, report_id))


@router.get(
    "/v1/brand/{brand_id}/reports",
    response_model=list[ReportVersionItem],
    summary="List report versions (newest first)",
    dependencies=[_VIEW],
)
@inject
async def list_reports(
    brand_id: UUID,
    tenant: BrandTenantCtx = Depends(active_brand),
    service: BrandReportService = Depends(Provide[BrandReportContainer.service]),
) -> list[ReportVersionItem]:
    rows = await service.list_reports(tenant.brand_id)
    return [ReportVersionItem.from_model(r) for r in rows]


@router.get(
    "/v1/brand/{brand_id}/report/{report_id}/pdf",
    summary="Download Brand IQ Report as PDF",
    dependencies=[_VIEW],
    response_class=Response,
)
@inject
async def download_report_pdf(
    brand_id: UUID,
    report_id: str,
    tenant: BrandTenantCtx = Depends(active_brand),
    pdf_service: BrandReportPdfService = Depends(Provide[BrandReportContainer.pdf_service]),
) -> Response:
    """Render the Brand IQ Report to a downloadable PDF.

    Returns HTTP 200 application/pdf on success.
    Returns HTTP 409 if the report is not yet in READY status.
    Returns HTTP 404 if the report does not exist for this brand.
    """
    pdf_bytes, filename = await pdf_service.generate_pdf(tenant.brand_id, report_id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": build_content_disposition(filename)},
    )
