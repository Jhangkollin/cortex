"""Unit tests for BrandReportPdfService.

Uses DI-override pattern (fake renderer injected via constructor, never
mock.patch).  The renderer fake returns b"%PDF-1.4 ..." — sufficient to
verify the service orchestration without launching Chromium.
"""

from __future__ import annotations

import pytest

from cortex_api.core.exceptions import ConflictError, NotFoundError
from cortex_api.core.identifiers import uuid7
from cortex_api.service.brand_report.config import Config
from cortex_api.service.brand_report.model.report import BrandReport, BrandReportStatus
from cortex_api.service.brand_report.pdf_service import BrandReportPdfService, build_content_disposition
from cortex_api.service.brand_report.service import BrandReportService

# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------

_FAKE_PDF = b"%PDF-1.4 fake-bytes-for-testing"

_FULL_REPORT_JSON: dict = {
    "meta": {
        "subject": "Acme Bank Asia",
        "enName": "Acme Bank Asia",
        "reportDate": "2026-05-22",
        "windowFrom": "2025-05-22",
        "windowTo": "2026-05-22",
        "monogram": "A",
        "primaryMarket": "台灣",
        "extendedMarkets": ["香港"],
        "confidence": 96,
        "reportId": "BIQ-2026-05-22-ACMEBA",
        "pageCount": 8,
        "preparedFor": "Marketing Manager",
        "preparedBy": "Cortex · Brand Agent",
    },
    "core": [],
    "coreJudgement": "",
    "productLines": [],
    "productNote": "",
    "subBrands": [],
    "endorsements": {"status": "資料不足", "body": ""},
    "ipCollabs": {"status": "資料不足", "body": ""},
    "mediaNetwork": [],
    "competitors": [],
    "competitorNote": "",
    "insights": {"confirmed": [], "inferences": [], "hypotheses": []},
    "faq": [],
    "channels": [],
    "risks": [],
    "sources": {"A": [], "B": [], "C": []},
    "quality": {"high": "", "midLow": "", "gaps": "", "conflicts": "", "open": ""},
}


class _SessCtx:
    async def __aenter__(self):
        return object()

    async def __aexit__(self, *a):
        return False


class _DB:
    def session(self):
        return _SessCtx()


class _ReportRepo:
    def __init__(self, rows: dict):
        self.rows = rows

    async def get(self, _s, _bid, rid):
        return self.rows.get(rid)

    async def list_for_brand(self, _s, _bid):
        return list(self.rows.values())


def _make_ready_row(brand_id, report_id: str = "BIQ-test") -> BrandReport:
    row = BrandReport(brand_id=brand_id, report_id=report_id, version="v1.0")
    row.status = BrandReportStatus.READY
    row.report_json = _FULL_REPORT_JSON
    return row


def _make_generating_row(brand_id, report_id: str = "BIQ-gen") -> BrandReport:
    row = BrandReport(brand_id=brand_id, report_id=report_id, version="v1.0")
    row.status = BrandReportStatus.GENERATING
    return row


async def _fake_renderer(html: str, *, timeout_ms: int, max_concurrent: int) -> bytes:
    """A fast fake renderer that returns stub PDF bytes without Chromium.

    Matches the RendererFn Protocol — accepts the timeout/concurrency kwargs
    that pdf_service passes through from Config.
    """
    assert "<html" in html  # sanity: must receive actual HTML
    return _FAKE_PDF


def _make_pdf_svc(rows: dict, renderer=None):
    """Build a BrandReportPdfService with fake collaborators."""
    if renderer is None:
        renderer = _fake_renderer
    report_repo = _ReportRepo(rows)
    brand_svc = BrandReportService(database_client=_DB(), report_repo=report_repo)
    return BrandReportPdfService(service=brand_svc, renderer=renderer, config=Config())


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------


async def test_generate_pdf_returns_bytes_and_filename() -> None:
    bid = uuid7()
    row = _make_ready_row(bid)
    svc = _make_pdf_svc({row.report_id: row})

    pdf_bytes, filename = await svc.generate_pdf(bid, row.report_id)

    assert pdf_bytes == _FAKE_PDF
    assert isinstance(filename, str)
    assert filename.endswith(".pdf")


async def test_filename_contains_brand_name() -> None:
    bid = uuid7()
    row = _make_ready_row(bid)
    svc = _make_pdf_svc({row.report_id: row})

    _, filename = await svc.generate_pdf(bid, row.report_id)
    # "Acme Bank Asia" sanitised = "Acme Bank Asia" (no unsafe chars)
    assert "Acme" in filename


async def test_filename_contains_version() -> None:
    bid = uuid7()
    row = _make_ready_row(bid)
    svc = _make_pdf_svc({row.report_id: row})

    _, filename = await svc.generate_pdf(bid, row.report_id)
    assert "v1.0" in filename


# ---------------------------------------------------------------------------
# Error paths
# ---------------------------------------------------------------------------


async def test_not_ready_raises_conflict() -> None:
    bid = uuid7()
    row = _make_generating_row(bid)
    svc = _make_pdf_svc({row.report_id: row})

    with pytest.raises(ConflictError):
        await svc.generate_pdf(bid, row.report_id)


async def test_failed_report_raises_conflict() -> None:
    bid = uuid7()
    row = BrandReport(brand_id=bid, report_id="BIQ-fail", version="v1.0")
    row.status = BrandReportStatus.FAILED
    svc = _make_pdf_svc({"BIQ-fail": row})

    with pytest.raises(ConflictError):
        await svc.generate_pdf(bid, "BIQ-fail")


async def test_unknown_report_raises_not_found() -> None:
    bid = uuid7()
    svc = _make_pdf_svc({})

    with pytest.raises(NotFoundError):
        await svc.generate_pdf(bid, "BIQ-nope")


# ---------------------------------------------------------------------------
# Renderer injection (DI override pattern — no mock.patch)
# ---------------------------------------------------------------------------


async def test_custom_renderer_is_called() -> None:
    """Prove the injected renderer is used (not the default Chromium one),
    and that timeout/concurrency kwargs are passed through from Config."""
    bid = uuid7()
    row = _make_ready_row(bid)

    called_with_html: list[str] = []
    called_kwargs: list[dict] = []

    async def recording_renderer(html: str, *, timeout_ms: int, max_concurrent: int) -> bytes:
        called_with_html.append(html)
        called_kwargs.append({"timeout_ms": timeout_ms, "max_concurrent": max_concurrent})
        return _FAKE_PDF

    svc = _make_pdf_svc({row.report_id: row}, renderer=recording_renderer)
    await svc.generate_pdf(bid, row.report_id)

    assert len(called_with_html) == 1
    assert "Acme Bank Asia" in called_with_html[0]
    # Config defaults flow through to the renderer call
    assert called_kwargs[0] == {
        "timeout_ms": Config().pdf_render_timeout_ms,
        "max_concurrent": Config().pdf_max_concurrent_renders,
    }


# ---------------------------------------------------------------------------
# build_content_disposition helper
# ---------------------------------------------------------------------------


def test_content_disposition_attachment() -> None:
    header = build_content_disposition("Acme Brand IQ Report v1.0.pdf")
    assert header.startswith("attachment;")


def test_content_disposition_filename_star() -> None:
    header = build_content_disposition("Acme 銀行 Brand IQ Report v1.0.pdf")
    assert "filename*=UTF-8''" in header
    # CJK characters percent-encoded
    assert "%" in header


def test_content_disposition_ascii_fallback() -> None:
    header = build_content_disposition("Acme Brand IQ Report v1.0.pdf")
    assert 'filename="' in header


def test_content_disposition_cjk_name_no_crash() -> None:
    header = build_content_disposition("台灣 Brand IQ Report v1.0.pdf")
    assert header.startswith("attachment;")
    assert "filename*=UTF-8''" in header
