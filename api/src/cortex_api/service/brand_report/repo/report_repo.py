"""CRUD + versioning on the brand_report table (stateless; service owns txn)."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from cortex_api.service.brand_report.model.report import BrandReport, BrandReportStatus


class BrandReportRepo:
    """Brand-scoped CRUD + versioning on `brand_report`."""

    async def create(self, session: AsyncSession, row: BrandReport) -> BrandReport:
        session.add(row)
        await session.flush()
        return row

    async def get(self, session: AsyncSession, brand_id: UUID, report_id: str) -> BrandReport | None:
        result = await session.exec(
            select(BrandReport).where(
                BrandReport.brand_id == brand_id,
                BrandReport.report_id == report_id,
            )
        )
        return result.first()

    async def get_current(self, session: AsyncSession, brand_id: UUID) -> BrandReport | None:
        result = await session.exec(
            select(BrandReport).where(
                BrandReport.brand_id == brand_id,
                BrandReport.status == BrandReportStatus.READY,
                BrandReport.archived_at.is_(None),  # type: ignore[union-attr]
            )
        )
        return result.first()

    async def list_for_brand(self, session: AsyncSession, brand_id: UUID) -> list[BrandReport]:
        result = await session.exec(
            select(BrandReport).where(BrandReport.brand_id == brand_id).order_by(BrandReport.created_at.desc())  # type: ignore[attr-defined]
        )
        return list(result.all())

    async def find_in_flight(self, session: AsyncSession, brand_id: UUID) -> BrandReport | None:
        """Return the newest GENERATING row for the brand, or None.

        Mirrors AnalysisJobRepo.find_in_flight — callers use this to dedupe
        concurrent generate() calls before inserting a new row.
        """
        result = await session.exec(
            select(BrandReport)
            .where(
                BrandReport.brand_id == brand_id,
                BrandReport.status == BrandReportStatus.GENERATING,
            )
            .order_by(BrandReport.created_at.desc())  # type: ignore[attr-defined]
        )
        return result.first()

    async def next_version(self, session: AsyncSession, brand_id: UUID) -> str:
        """Return the next version string for the brand, monotonic across ALL statuses.

        Counts the maximum minor version across every row for the brand
        (regardless of READY / FAILED / GENERATING status) and returns
        v1.{max+1}.  Returns v1.0 if there are no prior rows.

        WHY: with UNIQUE(brand_id, version) a READY-only computation would
        recompute v1.0 after a failed first attempt and collide on retry.
        Counting across all statuses makes version a per-brand monotonic
        counter so retries never reuse a version number.
        """
        result = await session.exec(select(BrandReport.version).where(BrandReport.brand_id == brand_id))
        versions = list(result.all())
        if not versions:
            return "v1.0"
        max_minor = 0
        for ver in versions:
            parts = ver.split(".")
            try:
                minor = int(parts[1]) if len(parts) > 1 else 0
            except ValueError:
                minor = 0
            if minor > max_minor:
                max_minor = minor
        return f"v1.{max_minor + 1}"

    async def mark_ready(
        self, session: AsyncSession, row: BrandReport, *, report_json: dict[str, Any], cost_usd: float | None
    ) -> None:
        prior = await self.get_current(session, row.brand_id)
        if prior is not None and prior.id != row.id:
            prior.archived_at = datetime.utcnow()
            session.add(prior)
            # Flush the archive BEFORE promoting `row`: the partial unique index
            # `uq_brand_report_one_current` is non-deferrable, so prior must stop
            # being "current" before row becomes "current" (no transient 2-current).
            await session.flush()
        row.status = BrandReportStatus.READY
        row.report_json = report_json
        row.cost_usd = cost_usd
        # clear any prior transient error from a failed attempt
        row.error = None
        session.add(row)
        await session.flush()

    async def mark_failed(self, session: AsyncSession, row: BrandReport, *, error: str) -> None:
        row.status = BrandReportStatus.FAILED
        row.error = error[:2000]
        session.add(row)
        await session.flush()

    async def sweep_stale(self, session: AsyncSession, *, older_than_seconds: int) -> int:
        cutoff = datetime.utcnow() - timedelta(seconds=older_than_seconds)
        result = await session.exec(
            select(BrandReport).where(
                BrandReport.status == BrandReportStatus.GENERATING,
                BrandReport.created_at < cutoff,
            )
        )
        stale = list(result.all())
        for row in stale:
            row.status = BrandReportStatus.FAILED
            row.error = "stale: worker did not finish"
            session.add(row)
        await session.flush()
        return len(stale)
