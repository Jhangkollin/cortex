"""Brand IQ Report API DTOs.

Response shapes for the brand_report router. camelCase field names mirror the
frontend polling contract and the BRAND_IQ JSON structure.
"""
# ruff: noqa: N815  # camelCase field names are intentional — mirror BRAND_IQ JSON keys

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel

from cortex_api.service.brand_report.model.report import BrandReport, BrandReportStatus


class GenerateReportResponse(BaseModel):
    """Returned immediately (HTTP 202) after kicking off an async report generation."""

    reportId: str
    status: str
    estimatedSeconds: int
    pollUrl: str

    @classmethod
    def from_model(
        cls,
        row: BrandReport,
        *,
        brand_id: UUID,
        estimated_seconds: int,
    ) -> GenerateReportResponse:
        return cls(
            reportId=row.report_id,
            status=row.status.value,
            estimatedSeconds=estimated_seconds,
            pollUrl=f"/v1/brand/{brand_id}/report/{row.report_id}",
        )


class ReportEnvelope(BaseModel):
    """Poll response — `report` is populated only when status == 'ready'."""

    reportId: str
    status: str
    error: str | None = None
    report: dict[str, Any] | None = None

    @classmethod
    def from_model(cls, row: BrandReport) -> ReportEnvelope:
        return cls(
            reportId=row.report_id,
            status=row.status.value,
            error=row.error,
            report=row.report_json if row.status == BrandReportStatus.READY else None,
        )


class ReportUiStateResponse(BaseModel):
    """Response for GET /report/ui-state."""

    celebratePending: bool
    heroDismissed: bool
    celebrateReady: bool


class ReportVersionItem(BaseModel):
    """One entry in the version list returned by GET /reports."""

    reportId: str
    version: str
    createdAt: str
    status: str
    current: bool
    costUsd: float | None = None

    @classmethod
    def from_model(cls, row: BrandReport) -> ReportVersionItem:
        return cls(
            reportId=row.report_id,
            version=row.version,
            createdAt=row.created_at.isoformat(),
            status=row.status.value,
            current=(row.status == BrandReportStatus.READY and row.archived_at is None),
            costUsd=row.cost_usd,
        )
