"""Unit tests for brand_report DTOs — pure, no DB or auth required."""

from __future__ import annotations

import datetime as dt
from datetime import datetime
from uuid import UUID

from cortex_api.app.api.brand_report.dto import (
    GenerateReportResponse,
    ReportEnvelope,
    ReportVersionItem,
)
from cortex_api.core.identifiers import uuid7
from cortex_api.service.brand_report.model.report import BrandReport, BrandReportStatus

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_BRAND_ID: UUID = uuid7()
_NOW = datetime(2026, 5, 24, 0, 0, 0, tzinfo=dt.UTC)


def _make_report(
    *,
    status: BrandReportStatus = BrandReportStatus.GENERATING,
    report_json: dict | None = None,
    archived_at: datetime | None = None,
    cost_usd: float | None = None,
    error: str | None = None,
) -> BrandReport:
    return BrandReport(
        brand_id=_BRAND_ID,
        report_id="BIQ-001",
        version="v1.0",
        status=status,
        report_json=report_json,
        archived_at=archived_at,
        cost_usd=cost_usd,
        error=error,
        created_at=_NOW,
        updated_at=_NOW,
    )


# ---------------------------------------------------------------------------
# GenerateReportResponse.from_model
# ---------------------------------------------------------------------------


def test_generate_report_response_report_id() -> None:
    row = _make_report()
    resp = GenerateReportResponse.from_model(row, brand_id=_BRAND_ID, estimated_seconds=60)
    assert resp.reportId == "BIQ-001"


def test_generate_report_response_status() -> None:
    row = _make_report(status=BrandReportStatus.GENERATING)
    resp = GenerateReportResponse.from_model(row, brand_id=_BRAND_ID, estimated_seconds=90)
    assert resp.status == "generating"


def test_generate_report_response_estimated_seconds() -> None:
    row = _make_report()
    resp = GenerateReportResponse.from_model(row, brand_id=_BRAND_ID, estimated_seconds=120)
    assert resp.estimatedSeconds == 120


def test_generate_report_response_poll_url() -> None:
    row = _make_report()
    resp = GenerateReportResponse.from_model(row, brand_id=_BRAND_ID, estimated_seconds=30)
    assert resp.pollUrl == f"/v1/brand/{_BRAND_ID}/report/BIQ-001"


# ---------------------------------------------------------------------------
# ReportEnvelope.from_model
# ---------------------------------------------------------------------------


def test_report_envelope_ready_includes_report() -> None:
    payload = {"meta": {"subject": "Acme"}}
    row = _make_report(status=BrandReportStatus.READY, report_json=payload)
    env = ReportEnvelope.from_model(row)
    assert env.status == "ready"
    assert env.report == payload
    assert env.error is None


def test_report_envelope_generating_report_is_none() -> None:
    row = _make_report(status=BrandReportStatus.GENERATING)
    env = ReportEnvelope.from_model(row)
    assert env.status == "generating"
    assert env.report is None


def test_report_envelope_failed_report_is_none() -> None:
    row = _make_report(status=BrandReportStatus.FAILED, error="LLM timeout")
    env = ReportEnvelope.from_model(row)
    assert env.status == "failed"
    assert env.report is None
    assert env.error == "LLM timeout"


def test_report_envelope_report_id_forwarded() -> None:
    row = _make_report(status=BrandReportStatus.READY, report_json={})
    env = ReportEnvelope.from_model(row)
    assert env.reportId == "BIQ-001"


# ---------------------------------------------------------------------------
# ReportVersionItem.from_model — current flag logic
# ---------------------------------------------------------------------------


def test_version_item_ready_not_archived_is_current() -> None:
    row = _make_report(status=BrandReportStatus.READY, archived_at=None)
    item = ReportVersionItem.from_model(row)
    assert item.current is True


def test_version_item_ready_but_archived_is_not_current() -> None:
    row = _make_report(status=BrandReportStatus.READY, archived_at=_NOW)
    item = ReportVersionItem.from_model(row)
    assert item.current is False


def test_version_item_generating_is_not_current() -> None:
    row = _make_report(status=BrandReportStatus.GENERATING, archived_at=None)
    item = ReportVersionItem.from_model(row)
    assert item.current is False


def test_version_item_failed_is_not_current() -> None:
    row = _make_report(status=BrandReportStatus.FAILED, archived_at=None)
    item = ReportVersionItem.from_model(row)
    assert item.current is False


def test_version_item_cost_usd_forwarded() -> None:
    row = _make_report(status=BrandReportStatus.READY, cost_usd=0.042)
    item = ReportVersionItem.from_model(row)
    assert item.costUsd == 0.042


def test_version_item_created_at_isoformat() -> None:
    row = _make_report()
    item = ReportVersionItem.from_model(row)
    assert item.createdAt == _NOW.isoformat()


def test_version_item_version_forwarded() -> None:
    row = _make_report()
    item = ReportVersionItem.from_model(row)
    assert item.version == "v1.0"
