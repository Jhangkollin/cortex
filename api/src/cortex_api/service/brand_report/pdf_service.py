"""Brand IQ Report PDF service.

Orchestrates: load report → assert READY → render HTML → render PDF → return
bytes + filename.  The renderer is injected so tests can override it with a
fast fake that returns ``b"%PDF-1.4..."`` without launching Chromium.
"""

from __future__ import annotations

import urllib.parse
from typing import Protocol
from uuid import UUID

import structlog

from cortex_api.core.exceptions import ConflictError
from cortex_api.service.brand_report.config import Config
from cortex_api.service.brand_report.model.report import BrandReportStatus
from cortex_api.service.brand_report.pdf.template import render_report_html, sanitize_filename
from cortex_api.service.brand_report.service import BrandReportService


class RendererFn(Protocol):
    """The renderer callable contract — matches ``render_pdf``'s signature.

    Tests supply a fake implementing this Protocol; production injects the
    real ``render_pdf``. The keyword args are passed from Config at call time.
    """

    async def __call__(self, html: str, *, timeout_ms: int, max_concurrent: int) -> bytes: ...


class BrandReportPdfService:
    """Generate a downloadable Brand IQ Report PDF."""

    def __init__(
        self,
        service: BrandReportService,
        renderer: RendererFn,
        config: Config,
    ) -> None:
        self._logger = structlog.get_logger(__name__)
        self._service = service
        self._renderer = renderer
        self._config = config

    async def generate_pdf(
        self,
        brand_id: UUID,
        report_id: str,
    ) -> tuple[bytes, str]:
        """Return ``(pdf_bytes, filename)`` for a READY report.

        Args:
            brand_id: The scoping brand UUID (from the JWT active context).
            report_id: The report identifier (e.g. ``BIQ-2026-05-22-ACMEBA``).

        Returns:
            A tuple of raw PDF bytes and a safe filename string.

        Raises:
            NotFoundError: If the report does not exist for this brand.
            ConflictError: If the report exists but is not in READY status.
            UpstreamError: If Chromium rendering fails.
        """
        row = await self._service.get_report(brand_id, report_id)

        if row.status != BrandReportStatus.READY or not row.report_json:
            raise ConflictError(f"Report {report_id} is not ready for PDF export (status={row.status})")

        report_json = row.report_json
        meta = report_json.get("meta", {})
        subject = str(meta.get("subject") or "Brand")
        version = str(row.version)

        self._logger.info("pdf_render_start", report_id=report_id, brand_id=str(brand_id))

        html = render_report_html(report_json)
        pdf_bytes = await self._renderer(
            html,
            timeout_ms=self._config.pdf_render_timeout_ms,
            max_concurrent=self._config.pdf_max_concurrent_renders,
        )

        self._logger.info(
            "pdf_render_done",
            report_id=report_id,
            brand_id=str(brand_id),
            size_bytes=len(pdf_bytes),
        )

        filename = _build_filename(subject, version)
        return pdf_bytes, filename


def _build_filename(subject: str, version: str) -> str:
    """Build a safe ASCII filename with a UTF-8 star form for Content-Disposition.

    Returns only the plain filename string; the router builds both the
    ``filename=`` (ASCII fallback) and ``filename*=UTF-8''...`` (full unicode)
    forms in the header.
    """
    safe_subject = sanitize_filename(subject)
    safe_version = sanitize_filename(version)
    return f"{safe_subject} Brand IQ Report {safe_version}.pdf"


def build_content_disposition(filename: str) -> str:
    """Build a RFC 5987 Content-Disposition header value.

    Produces both the ASCII fallback (``filename=``) and the percent-encoded
    UTF-8 form (``filename*=``) so both old and modern clients can read the
    filename correctly.

    Args:
        filename: The desired filename (may contain CJK / non-ASCII chars).

    Returns:
        A string suitable for the ``Content-Disposition`` response header value.
    """
    # ASCII fallback — replace non-ASCII with underscores
    ascii_name = sanitize_filename(filename.encode("ascii", "replace").decode("ascii"))
    # RFC 5987 UTF-8 percent-encoded form. safe="" so spaces become %20
    # (a literal space in filename* is invalid and breaks strict clients).
    utf8_encoded = urllib.parse.quote(filename, safe="")
    return f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{utf8_encoded}"
