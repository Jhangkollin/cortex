"""Async brand-profile analyze jobs: dedupe, in-process worker, sweep."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from uuid import UUID

import structlog
from cortex_brand_extract import extract_brand_profile
from cortex_brand_extract.errors import ExtractError
from cortex_brand_extract.errors import UpstreamError as SP2UpstreamError
from cortex_brand_extract.errors import UpstreamTimeoutError as SP2UpstreamTimeoutError
from cortex_brand_extract.types import BrandProfile as SP2Profile

from cortex_api.core.background import BackgroundTaskTracker
from cortex_api.core.exceptions import (
    NotFoundError,
    UpstreamError,
    UpstreamTimeoutError,
)
from cortex_api.infra.database_client import DatabaseClient
from cortex_api.service.brand.analyze_config import AnalyzeConfig
from cortex_api.service.brand.analyze_mapping import sp2_to_sp1_profile
from cortex_api.service.brand.analyze_provider import build_provider
from cortex_api.service.brand.model.analysis_job import BrandProfileAnalysisJob
from cortex_api.service.brand.repo.analysis_job_repo import AnalysisJobRepo
from cortex_api.service.brand.repo.profile_repo import BrandProfileRepo
from cortex_api.service.placement.composer import BrandPlacementComposer

ExtractFn = Callable[..., Awaitable[SP2Profile]]


class AnalyzeJobService:
    """Owns the analyze-job lifecycle and the in-process extraction worker."""

    def __init__(
        self,
        database_client: DatabaseClient,
        analysis_job_repo: AnalysisJobRepo,
        profile_repo: BrandProfileRepo,
        config: AnalyzeConfig,
        composer: BrandPlacementComposer,
        tracker: BackgroundTaskTracker,
        _extract: ExtractFn = extract_brand_profile,
    ) -> None:
        self._logger = structlog.get_logger(__name__)
        self._db = database_client
        self._jobs = analysis_job_repo
        self._profiles = profile_repo
        self._config = config
        self._composer = composer
        self._tracker = tracker
        self._extract = _extract
        # Maps each in-flight worker task to the (brand_id, job_id) it owns so
        # a graceful shutdown can FAIL-mark the DB row (not just cancel the
        # in-memory task and leave the row RUNNING until the TTL sweep). The
        # add_done_callback below pops the entry, keeping this bounded to
        # genuinely in-flight work.
        self._tasks: dict[asyncio.Task[None], tuple[UUID, UUID]] = {}

    async def start_analyze(self, brand_id: UUID, url: str) -> BrandProfileAnalysisJob:
        async with self._db.session() as session:
            in_flight = await self._jobs.find_in_flight(session, brand_id)
            if in_flight is not None:
                self._logger.info("analyze_dedup", brand_id=str(brand_id), job_id=str(in_flight.id))
                return in_flight
            job = await self._jobs.create(session, BrandProfileAnalysisJob(brand_id=brand_id, source_url=url))
        task = asyncio.create_task(self._run(brand_id, job.id, url))
        self._tasks[task] = (brand_id, job.id)
        task.add_done_callback(lambda t: self._tasks.pop(t, None))
        return job

    async def get_job(self, brand_id: UUID, job_id: UUID) -> BrandProfileAnalysisJob:
        async with self._db.session() as session:
            job = await self._jobs.get(session, brand_id, job_id)
            if job is None:
                raise NotFoundError(f"analyze job {job_id} not found")
            return job

    async def sweep_stale(self) -> int:
        async with self._db.session() as session:
            return await self._jobs.sweep_stale(session, older_than_seconds=self._config.stale_job_seconds)

    async def drain(self) -> None:
        """Await all in-flight worker tasks (tests + graceful shutdown)."""
        if self._tasks:
            await asyncio.gather(*tuple(self._tasks), return_exceptions=True)

    async def cancel_all(self) -> None:
        """Shutdown path: FAIL-mark every in-flight job, then cancel + drain.

        We snapshot ``(brand_id, job_id)`` BEFORE cancelling so a graceful
        SIGTERM leaves a clean DB immediately instead of stranding rows in
        RUNNING until the TTL sweep. The fail-write is best-effort: ``_fail``
        is already guarded (Task-7 follow-up) so a write failure there is
        logged and swallowed — the stale-sweep remains the backstop. We
        cancel after the writes so the worker's own ``_fail`` can't race a
        half-committed success path.
        """
        in_flight = tuple(self._tasks.items())
        for task, (brand_id, job_id) in in_flight:
            try:
                await self._fail(brand_id, job_id, "cancelled at shutdown")
            except Exception:  # noqa: BLE001 — stale-sweep is the backstop; shutdown must not raise
                self._logger.exception(
                    "analyze_cancel_fail_write_failed",
                    brand_id=str(brand_id),
                    job_id=str(job_id),
                )
            task.cancel()
        await self.drain()

    async def _run(self, brand_id: UUID, job_id: UUID, url: str) -> None:
        """In-process extraction worker. The session split here is deliberate.

        `mark_running` commits in its OWN session/txn before the long
        `await self._extract(...)` so the RUNNING status is visible to dedupe
        (`find_in_flight`) and to the stale-sweep while extraction is in flight
        — folding it into the success session would hide RUNNING for minutes.
        The success path keeps `profile_repo.upsert` + `mark_succeeded` in ONE
        session/txn so they commit atomically — never a "profile written but
        job not SUCCEEDED" half-state. The job is re-`get`-ed inside each
        `async with self._db.session()` block because the prior session's
        instance is detached on block exit: re-fetch, never reuse across
        sessions.
        """
        async with self._db.session() as session:
            job = await self._jobs.get(session, brand_id, job_id)
            if job is None:
                return
            await self._jobs.mark_running(session, job)
        try:
            provider = build_provider(self._config)
            result = await self._extract(url, provider=provider, tier=self._config.tier)
        except (SP2UpstreamTimeoutError, SP2UpstreamError, ExtractError) as e:
            await self._fail(brand_id, job_id, str(e))
            if isinstance(e, SP2UpstreamTimeoutError):
                raise UpstreamTimeoutError(f"brand extraction timed out: {e}") from e
            raise UpstreamError(f"brand extraction failed: {e}") from e
        except Exception as e:  # noqa: BLE001 — worker boundary must not die silently
            self._logger.error("analyze_worker_unexpected", job_id=str(job_id), error=str(e))
            await self._fail(brand_id, job_id, f"unexpected: {type(e).__name__}")
            return
        async with self._db.session() as session:
            mapped = sp2_to_sp1_profile(brand_id, result)
            await self._profiles.upsert(session, mapped)
            job = await self._jobs.get(session, brand_id, job_id)
            if job is not None:
                await self._jobs.mark_succeeded(session, job, cost_usd=result.extraction_meta.cost_usd)
        # Hook B (AD7): schedule placement composer after the profile commit,
        # outside the session, before logging success. Composer failure is
        # logged by the tracker; never re-raises into the analyze worker.
        self._tracker.track(asyncio.create_task(self._composer.compose(brand_id)))
        self._logger.info("analyze_succeeded", brand_id=str(brand_id), job_id=str(job_id))

    async def _fail(self, brand_id: UUID, job_id: UUID, message: str) -> None:
        try:
            async with self._db.session() as session:
                job = await self._jobs.get(session, brand_id, job_id)
                if job is not None:
                    await self._jobs.mark_failed(session, job, error=message)
        except Exception:  # noqa: BLE001 — stale-sweep is the backstop; never mask the caller's error
            self._logger.exception("analyze_fail_write_failed", brand_id=str(brand_id), job_id=str(job_id))
            return
        self._logger.warning("analyze_failed", brand_id=str(brand_id), job_id=str(job_id))
