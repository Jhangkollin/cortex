"""CRUD on the brand_profile_analysis_job table (stateless; service owns txn)."""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from cortex_api.service.brand.model.analysis_job import (
    AnalyzeJobStatus,
    BrandProfileAnalysisJob,
)

_IN_FLIGHT = (AnalyzeJobStatus.PENDING, AnalyzeJobStatus.RUNNING)


class AnalysisJobRepo:
    """Brand-scoped access to analyze jobs."""

    async def create(self, session: AsyncSession, job: BrandProfileAnalysisJob) -> BrandProfileAnalysisJob:
        session.add(job)
        await session.flush()
        return job

    async def get(self, session: AsyncSession, brand_id: UUID, job_id: UUID) -> BrandProfileAnalysisJob | None:
        result = await session.exec(
            select(BrandProfileAnalysisJob).where(
                BrandProfileAnalysisJob.id == job_id,
                BrandProfileAnalysisJob.brand_id == brand_id,
            )
        )
        return result.first()

    async def find_in_flight(self, session: AsyncSession, brand_id: UUID) -> BrandProfileAnalysisJob | None:
        result = await session.exec(
            select(BrandProfileAnalysisJob)
            .where(
                BrandProfileAnalysisJob.brand_id == brand_id,
                BrandProfileAnalysisJob.status.in_(_IN_FLIGHT),  # type: ignore[attr-defined]
            )
            .order_by(BrandProfileAnalysisJob.created_at.desc())  # type: ignore[attr-defined]
        )
        return result.first()

    async def mark_running(self, session: AsyncSession, job: BrandProfileAnalysisJob) -> None:
        job.status = AnalyzeJobStatus.RUNNING
        session.add(job)
        await session.flush()

    async def mark_succeeded(self, session: AsyncSession, job: BrandProfileAnalysisJob, *, cost_usd: float) -> None:
        job.status = AnalyzeJobStatus.SUCCEEDED
        job.cost_usd = cost_usd
        session.add(job)
        await session.flush()

    async def mark_failed(self, session: AsyncSession, job: BrandProfileAnalysisJob, *, error: str) -> None:
        job.status = AnalyzeJobStatus.FAILED
        job.error = error[:2000]
        session.add(job)
        await session.flush()

    async def sweep_stale(self, session: AsyncSession, *, older_than_seconds: int) -> int:
        cutoff = datetime.utcnow() - timedelta(seconds=older_than_seconds)
        result = await session.exec(
            select(BrandProfileAnalysisJob).where(
                BrandProfileAnalysisJob.status.in_(_IN_FLIGHT),  # type: ignore[attr-defined]
                BrandProfileAnalysisJob.created_at < cutoff,
            )
        )
        stale = list(result.all())
        for job in stale:
            job.status = AnalyzeJobStatus.FAILED
            job.error = "stale: worker did not finish"
            session.add(job)
        await session.flush()
        return len(stale)
