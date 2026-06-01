"""Async orchestrator that manages brand-report generation jobs."""

from __future__ import annotations

import asyncio
from datetime import date
from uuid import UUID

import structlog
from cortex_brand_extract.llm.base import LLMProvider
from sqlalchemy.exc import IntegrityError

from cortex_api.core.exceptions import ConflictError, NotFoundError
from cortex_api.core.identifiers import uuid7
from cortex_api.infra.database_client import DatabaseClient
from cortex_api.service.brand.repo.profile_repo import BrandProfileRepo
from cortex_api.service.brand_report.composer import ReportSources, code, compose
from cortex_api.service.brand_report.config import Config
from cortex_api.service.brand_report.model.report import BrandReport
from cortex_api.service.brand_report.repo.report_repo import BrandReportRepo
from cortex_api.service.media_network.repo.brand_media_repo import BrandMediaRepo
from cortex_api.service.questions.repo.brand_questions_repo import BrandQuestionsRepo


def _build_report_id(name: str, report_uuid: UUID) -> str:
    return f"BIQ-{date.today().isoformat()}-{code(name)}-{report_uuid.hex[:8]}"


class BrandReportJobService:
    """Owns the brand-report generation lifecycle and in-process worker."""

    def __init__(
        self,
        database_client: DatabaseClient,
        report_repo: BrandReportRepo,
        profile_repo: BrandProfileRepo,
        media_repo: BrandMediaRepo,
        questions_repo: BrandQuestionsRepo,
        provider: LLMProvider,
        config: Config,
    ) -> None:
        self._logger = structlog.get_logger(__name__)
        self._db = database_client
        self._report_repo = report_repo
        self._profile_repo = profile_repo
        self._media_repo = media_repo
        self._questions_repo = questions_repo
        self._provider = provider
        self._config = config
        # Maps each in-flight worker task to the (brand_id, report_id) it owns
        # so graceful shutdown can FAIL-mark the DB row immediately rather than
        # waiting for the TTL sweep. Popped via add_done_callback on completion.
        self._tasks: dict[asyncio.Task[None], tuple[UUID, str]] = {}

    @property
    def estimated_seconds(self) -> int:
        return self._config.estimated_seconds

    async def generate(self, brand_id: UUID) -> BrandReport:
        """Create a new GENERATING report row and spawn the background worker.

        Deduplication: if a generation is already in-flight for this brand,
        return the existing row without starting a second worker.

        Concurrent-insert safety: if two callers both pass the find_in_flight
        check simultaneously they will race to INSERT; the loser's INSERT
        violates UNIQUE(brand_id, version) and raises IntegrityError, which is
        mapped to ConflictError (HTTP 409).
        """
        async with self._db.session() as s:
            profile = await self._profile_repo.get(s, brand_id)
            if profile is None:
                raise NotFoundError(f"brand {brand_id} has no profile to report on")
            in_flight = await self._report_repo.find_in_flight(s, brand_id)
            if in_flight is not None:
                return in_flight
            version = await self._report_repo.next_version(s, brand_id)
            report_uuid = uuid7()
            report_id = _build_report_id(profile.name, report_uuid)
            try:
                row = await self._report_repo.create(
                    s,
                    BrandReport(id=report_uuid, brand_id=brand_id, report_id=report_id, version=version),
                )
            except IntegrityError as e:
                raise ConflictError("a brand report generation is already in progress") from e

        task = asyncio.create_task(self._run(brand_id, row.report_id))
        self._tasks[task] = (brand_id, row.report_id)
        task.add_done_callback(lambda t: self._tasks.pop(t, None))
        return row

    async def sweep_stale(self) -> int:
        async with self._db.session() as s:
            return await self._report_repo.sweep_stale(s, older_than_seconds=self._config.stale_job_seconds)

    async def drain(self) -> None:
        """Await all in-flight worker tasks (tests + graceful shutdown)."""
        if self._tasks:
            await asyncio.gather(*tuple(self._tasks), return_exceptions=True)

    async def cancel_all(self) -> None:
        """Shutdown path: FAIL-mark every in-flight report, then cancel + drain.

        We snapshot (brand_id, report_id) BEFORE cancelling so a graceful
        SIGTERM leaves a clean DB immediately instead of stranding rows in
        GENERATING until the TTL sweep. The fail-write is best-effort; a
        write failure there is logged and swallowed — the stale-sweep remains
        the backstop.
        """
        in_flight = tuple(self._tasks.items())
        for task, (brand_id, report_id) in in_flight:
            try:
                await self._fail(brand_id, report_id, "cancelled at shutdown")
            except Exception:  # noqa: BLE001 — stale-sweep is the backstop; shutdown must not raise
                self._logger.exception(
                    "brand_report_cancel_fail_write_failed",
                    brand_id=str(brand_id),
                    report_id=report_id,
                )
            task.cancel()
        await self.drain()

    async def _run(self, brand_id: UUID, report_id: str) -> None:
        """In-process report worker.

        Two separate session blocks mirror AnalyzeJobService discipline:
        - Block 1: load sources (re-fetch; the generate() session is detached).
        - Block 2: commit mark_ready atomically after a successful compose().

        compose() already swallows LLM errors and degrades gracefully, so the
        only realistic failures here are DB / unexpected exceptions, caught by
        the broad except below.
        """
        # --- Block 1: load sources ---
        async with self._db.session() as s:
            profile = await self._profile_repo.get(s, brand_id)
            if profile is None:
                await self._fail(brand_id, report_id, "profile disappeared before worker ran")
                return
            media = await self._media_repo.get(s, brand_id)
            q = await self._questions_repo.get(s, brand_id)

        outlets = media.outlets if media is not None else []
        questions = q.questions if q is not None else []
        profile_dict = profile.model_dump()

        sources = ReportSources(profile=profile_dict, outlets=outlets, questions=questions)

        try:
            dto, cost = await compose(
                sources,
                self._provider,
                page_count=self._config.page_count,
                prepared_by=self._config.prepared_by,
                report_id=report_id,
            )

            # --- Block 2: persist success (inside the try so a transient DB
            #     error here is caught and routed to _fail instead of leaving
            #     the row stuck in GENERATING until the sweep) ---
            async with self._db.session() as s:
                row = await self._report_repo.get(s, brand_id, report_id)
                if row is not None:
                    await self._report_repo.mark_ready(
                        s,
                        row,
                        report_json=dto.model_dump(),
                        cost_usd=cost,
                    )
                    self._logger.info("brand_report_succeeded", brand_id=str(brand_id), report_id=report_id)
        except asyncio.CancelledError:
            raise
        except Exception as e:  # noqa: BLE001 — worker boundary must not die silently
            self._logger.error(
                "brand_report_worker_unexpected",
                report_id=report_id,
                brand_id=str(brand_id),
                error=str(e),
            )
            await self._fail(brand_id, report_id, f"unexpected: {type(e).__name__}")
            return

    async def _fail(self, brand_id: UUID, report_id: str, message: str) -> None:
        try:
            async with self._db.session() as s:
                row = await self._report_repo.get(s, brand_id, report_id)
                if row is not None:
                    await self._report_repo.mark_failed(s, row, error=message)
        except Exception:  # noqa: BLE001 — stale-sweep is the backstop; never mask the caller's error
            self._logger.exception(
                "brand_report_fail_write_failed",
                brand_id=str(brand_id),
                report_id=report_id,
            )
            return
        self._logger.warning("brand_report_failed", brand_id=str(brand_id), report_id=report_id)
