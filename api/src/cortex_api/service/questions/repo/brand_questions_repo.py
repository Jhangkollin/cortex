# api/src/cortex_api/service/questions/repo/brand_questions_repo.py
from __future__ import annotations

from typing import Any
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from cortex_api.service.questions.model.job import BrandWeeklyQuestions, QuestionJobStatus

_IN_FLIGHT = (QuestionJobStatus.PENDING, QuestionJobStatus.RUNNING)


class BrandQuestionsRepo:
    """Brand-scoped access to the `brand_weekly_questions` table."""

    async def get(self, session: AsyncSession, brand_id: UUID) -> BrandWeeklyQuestions | None:
        result = await session.exec(select(BrandWeeklyQuestions).where(BrandWeeklyQuestions.brand_id == brand_id))
        return result.first()

    async def find_in_flight(self, session: AsyncSession, brand_id: UUID) -> BrandWeeklyQuestions | None:
        row = await self.get(session, brand_id)
        return row if row and row.status in _IN_FLIGHT else None

    async def create(self, session: AsyncSession, job: BrandWeeklyQuestions) -> BrandWeeklyQuestions:
        """Insert or reset-to-PENDING the row for `job.brand_id`.

        Uses INSERT ... ON CONFLICT (brand_id) DO UPDATE so a re-trigger
        resets the row to PENDING atomically without a read-then-write race.
        Mirrors `BrandMediaRepo.create` — `pg_insert(...).returning(Model)` +
        `.scalars().one()` + flush.

        `updated_at` is written `sa.func.now()` (DB clock) on both the insert
        and the conflict-update so every write to this row shares one clock
        with `brand_profile.updated_at` — `QuestionsJobService.start` compares
        the two across tables, so they must not come from different clocks.
        """
        stmt = (
            pg_insert(BrandWeeklyQuestions)
            .values(
                brand_id=job.brand_id,
                status=QuestionJobStatus.PENDING.value,
                error=None,
                updated_at=sa.func.now(),
            )
            .on_conflict_do_update(
                index_elements=["brand_id"],
                set_={
                    "status": QuestionJobStatus.PENDING.value,
                    "error": None,
                    "questions": [],
                    "updated_at": sa.func.now(),
                },
            )
            .returning(BrandWeeklyQuestions)
        )
        result = await session.execute(stmt)
        saved: BrandWeeklyQuestions = result.scalars().one()
        await session.flush()
        return saved

    async def mark_running(self, session: AsyncSession, brand_id: UUID) -> None:
        job = await self.get(session, brand_id)
        if job is None:
            raise ValueError(f"BrandWeeklyQuestions not found for brand_id={brand_id}")
        job.status = QuestionJobStatus.RUNNING
        # SQL expr assigned to a mapped col: valid at runtime, opaque to mypy.
        job.updated_at = sa.func.now()  # type: ignore[assignment]  # DB clock — see create()
        session.add(job)
        await session.flush()

    async def mark_succeeded(self, session: AsyncSession, brand_id: UUID, questions: list[dict[str, Any]]) -> None:
        job = await self.get(session, brand_id)
        if job is None:
            raise ValueError(f"BrandWeeklyQuestions not found for brand_id={brand_id}")
        job.status = QuestionJobStatus.SUCCEEDED
        job.questions = questions
        job.error = None
        job.updated_at = sa.func.now()  # type: ignore[assignment]  # DB clock — see create()
        session.add(job)
        await session.flush()

    async def mark_failed(self, session: AsyncSession, brand_id: UUID, error: str) -> None:
        job = await self.get(session, brand_id)
        if job is None:
            raise ValueError(f"BrandWeeklyQuestions not found for brand_id={brand_id}")
        job.status = QuestionJobStatus.FAILED
        job.error = error[:500]
        job.updated_at = sa.func.now()  # type: ignore[assignment]  # DB clock — see create()
        session.add(job)
        await session.flush()

    async def sweep_stale(self, session: AsyncSession, older_than_seconds: int) -> int:
        """Mark all PENDING/RUNNING rows older than `older_than_seconds` as FAILED.

        Mirrors `BrandMediaRepo.sweep_stale`: load all stale rows, mutate
        each in Python, add + flush — no raw UPDATE SQL.

        The cutoff is computed DB-side (`now() - make_interval(...)`) so it
        shares the same clock as the DB-authored `updated_at` it is compared
        against (see create() docstring).
        """
        cutoff = sa.func.now() - sa.func.make_interval(0, 0, 0, 0, 0, 0, older_than_seconds)
        result = await session.exec(
            select(BrandWeeklyQuestions).where(
                BrandWeeklyQuestions.status.in_([s.value for s in _IN_FLIGHT]),  # type: ignore[attr-defined]
                BrandWeeklyQuestions.updated_at < cutoff,
            )
        )
        stale = list(result.all())
        for job in stale:
            job.status = QuestionJobStatus.FAILED
            job.error = "stale: reclaimed by sweep"
            session.add(job)
        await session.flush()
        return len(stale)
