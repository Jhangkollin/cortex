"""Async weekly-questions jobs: dedupe, in-process worker, sweep (mirrors MediaNetworkJobService)."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Sequence
from typing import Any
from uuid import UUID

import structlog

from cortex_api.core.exceptions import NotFoundError
from cortex_api.infra.database_client import DatabaseClient
from cortex_api.service.brand.repo.profile_repo import BrandProfileRepo
from cortex_api.service.questions.config import Config
from cortex_api.service.questions.matcher import match_questions
from cortex_api.service.questions.model.job import BrandWeeklyQuestions, QuestionJobStatus
from cortex_api.service.questions.model.question import WeeklyQuestion
from cortex_api.service.questions.repo.brand_questions_repo import BrandQuestionsRepo
from cortex_api.service.questions.repo.question_repo import QuestionRepo

MatchFn = Callable[..., Awaitable[list[dict[str, Any]]]]


class QuestionsJobService:
    """Owns the weekly-questions job lifecycle and the in-process ranking worker.

    Structural mirror of MediaNetworkJobService: ``_tasks`` dict, create_task +
    done-callback, dedupe-on-start, drain, cancel_all, sweep_stale, and the
    ``_run`` try/except/CancelledError/mark_failed shape are all identical in
    spirit. Deviations are noted inline.

    Key deviation from MediaNetworkJobService: BrandWeeklyQuestions uses brand_id
    as the sole PK (no separate job_id row), so ``_tasks`` maps each task to a
    single ``UUID`` (brand_id) rather than a ``(brand_id, job_id)`` tuple.
    The ``_fail`` helper is kept private and follows the same best-effort
    pattern (log + swallow on DB failure).
    """

    def __init__(
        self,
        database_client: DatabaseClient,
        brand_questions_repo: BrandQuestionsRepo,
        question_repo: QuestionRepo,
        config: Config,
        brand_profile_repo: BrandProfileRepo,
        provider: Any | None = None,
        _match: MatchFn = match_questions,
    ) -> None:
        self._logger = structlog.get_logger(__name__)
        self._db = database_client
        self._jobs = brand_questions_repo
        self._snap = question_repo
        self._config = config
        self._brand_profile_repo = brand_profile_repo
        self._provider = provider
        self._match = _match
        # Maps each in-flight worker task to the brand_id it owns so graceful
        # shutdown can FAIL-mark the DB row before cancellation. Mirrors
        # MediaNetworkJobService._tasks — the add_done_callback below pops on
        # completion, keeping the dict bounded to genuinely in-flight work.
        self._tasks: dict[asyncio.Task[None], UUID] = {}

    async def start(self, brand_id: UUID, regenerate: bool = False) -> BrandWeeklyQuestions:
        """Start (or return) a weekly-questions job for brand_id.

        Dedupe logic mirrors MediaNetworkJobService.start:
        - If a row is PENDING or RUNNING, return it immediately (already in flight).
        - If a row is SUCCEEDED with a non-empty questions list and
          regenerate=False, return it. A SUCCEEDED row with an EMPTY questions
          list is NOT treated as a valid dedup target — it is a stale degraded
          result (persisted during a transient empty-snapshot / no-category
          state by older code) and must be recomputed so it self-heals.
        - A SUCCEEDED row generated BEFORE the brand profile was last updated is
          also stale: the profile is the synth/match input, so re-extracting it
          (e.g. re-onboarding the same brand with a different site) must
          regenerate — otherwise the brand keeps showing the previous profile's
          questions. Self-heals on the next start() with no caller change.
        - Otherwise, create/reset the row to PENDING and spawn a worker task.

        Invalidation is read-time (compare `profile.updated_at` here) rather
        than event-driven (the profile write path explicitly clearing this
        cache). Read-time keeps the brand-profile write path unaware of its
        downstream caches, at the cost of each downstream cache rediscovering
        staleness on its own. That trade is deliberate while questions is the
        only profile-derived cache with this need; a shared invalidation seam
        (or a `BrandProfileUpdated` domain event) is the right move once a
        second cache (report versions, recommendations) needs the same signal.
        """
        async with self._db.session() as session:
            existing = await self._jobs.get(session, brand_id)
            stale_vs_profile = False
            profile_updated_at = None
            if existing is not None and existing.status == QuestionJobStatus.SUCCEEDED:
                profile = await self._brand_profile_repo.get(session, brand_id)
                profile_updated_at = profile.updated_at if profile is not None else None
                stale_vs_profile = (
                    profile_updated_at is not None
                    and existing.updated_at is not None
                    and profile_updated_at > existing.updated_at
                )
            existing_is_dedupable = existing is not None and (
                existing.status in (QuestionJobStatus.PENDING, QuestionJobStatus.RUNNING)
                or (
                    existing.status == QuestionJobStatus.SUCCEEDED and bool(existing.questions) and not stale_vs_profile
                )
            )
            if existing is not None and not regenerate and existing_is_dedupable:
                self._logger.info(
                    "questions_job_dedup",
                    brand_id=str(brand_id),
                    status=existing.status,
                )
                return existing
            # Falling through to (re)generation. Log WHY dedup did not apply so the
            # self-heal branches (empty row / stale-vs-profile) leave a breadcrumb —
            # diagnosing the "adidas shows mlytics" bug previously required reading
            # both updated_at columns out of the DB by hand.
            self._logger.info(
                "questions_job_regenerate",
                brand_id=str(brand_id),
                reason=self._regenerate_reason(regenerate, existing, stale_vs_profile),
                existing_status=(existing.status if existing is not None else None),
                profile_updated_at=(str(profile_updated_at) if profile_updated_at is not None else None),
                existing_updated_at=(
                    str(existing.updated_at) if existing is not None and existing.updated_at is not None else None
                ),
            )
            job = await self._jobs.create(session, BrandWeeklyQuestions(brand_id=brand_id))
        task = asyncio.create_task(self._run(brand_id))
        self._tasks[task] = brand_id
        task.add_done_callback(lambda t: self._tasks.pop(t, None))
        return job

    @staticmethod
    def _regenerate_reason(
        regenerate: bool,
        existing: BrandWeeklyQuestions | None,
        stale_vs_profile: bool,
    ) -> str:
        """Classify why a (re)generation is happening, for the structured log."""
        if regenerate:
            return "regenerate_flag"
        if existing is None:
            return "no_row"
        if existing.status == QuestionJobStatus.FAILED:
            return "prior_failed"
        if existing.status == QuestionJobStatus.SUCCEEDED and not existing.questions:
            return "empty_row"
        if stale_vs_profile:
            return "stale_vs_profile"
        return "not_dedupable"

    async def get(self, brand_id: UUID) -> BrandWeeklyQuestions:
        async with self._db.session() as session:
            row = await self._jobs.get(session, brand_id)
        if row is None:
            raise NotFoundError(f"no weekly-questions job for brand {brand_id}")
        return row

    async def sweep_stale(self) -> int:
        async with self._db.session() as session:
            return await self._jobs.sweep_stale(session, self._config.stale_job_seconds)

    async def drain(self) -> None:
        """Await all in-flight worker tasks (tests + graceful shutdown)."""
        if self._tasks:
            await asyncio.gather(*tuple(self._tasks), return_exceptions=True)

    async def cancel_all(self) -> None:
        """Shutdown path: FAIL-mark every in-flight job, then cancel + drain.

        Mirrors MediaNetworkJobService.cancel_all. Snapshots the in-flight set
        BEFORE cancelling so a graceful SIGTERM leaves a clean DB immediately
        instead of stranding rows in RUNNING until the TTL sweep. The
        fail-write is best-effort — a write failure is logged and swallowed so
        shutdown never raises (stale-sweep remains the backstop). We cancel
        AFTER the writes so the worker's own failure path can't race a
        half-committed success path.
        """
        in_flight = tuple(self._tasks.items())
        for task, brand_id in in_flight:
            try:
                await self._fail(brand_id, "cancelled at shutdown")
            except Exception:  # noqa: BLE001 — stale-sweep is the backstop; shutdown must not raise
                self._logger.exception(
                    "questions_cancel_fail_write_failed",
                    brand_id=str(brand_id),
                )
            task.cancel()
        await self.drain()

    async def _run(self, brand_id: UUID) -> None:
        """In-process ranking worker.

        Session split is deliberate (mirrors MediaNetworkJobService._run):
        - mark_running commits in its OWN session so RUNNING is visible to
          dedupe and stale-sweep while work is in flight.
        - mark_succeeded commits in ONE session with the questions payload so
          the write is atomic — never a half-state of questions-written-but-status-RUNNING.
        """
        try:
            async with self._db.session() as session:
                await self._jobs.mark_running(session, brand_id)
                profile_row = await self._brand_profile_repo.get(session, brand_id)
                snapshot: Sequence[WeeklyQuestion] = await self._snap.list_all(session)
            profile = {
                "name": (profile_row.name if profile_row else "") or "",
                # industry_vertical is the semantic equivalent of "category" in the
                # brand profile. The matcher's deterministic fallback reads
                # profile["category"] for matching, so we map it here.
                "category": (profile_row.industry_vertical if profile_row else "") or "",
                "region": (profile_row.region if profile_row else []) or [],
                "products": (profile_row.products if profile_row else []) or [],
                "competitors": (profile_row.competitors if profile_row else []) or [],
                "about": (profile_row.about if profile_row else "") or "",
            }
            questions = await self._match(
                profile,
                snapshot,
                self._provider,
                self._config.question_count,
                min_relevance_score=self._config.min_relevance_score,
            )
            # Enforce the SUCCEEDED contract at the write side: SUCCEEDED always
            # means "produced questions". The matcher's D8 backstop should make
            # an empty result impossible, so empty here is a genuine failure —
            # persist it as FAILED rather than a degraded SUCCEEDED-with-zero row
            # (which start()'s dedup would otherwise have to heal at read time).
            if not questions:
                await self._fail(brand_id, "matcher returned no questions")
                return
            async with self._db.session() as session:
                await self._jobs.mark_succeeded(session, brand_id, questions)
        except asyncio.CancelledError:
            raise
        except Exception as e:  # noqa: BLE001 — worker boundary must not die silently
            self._logger.exception("questions_job_failed", brand_id=str(brand_id))
            await self._fail(brand_id, str(e))

    async def _fail(self, brand_id: UUID, message: str) -> None:
        """Best-effort mark-failed helper — mirrors MediaNetworkJobService._fail."""
        try:
            async with self._db.session() as session:
                await self._jobs.mark_failed(session, brand_id, message)
        except Exception:  # noqa: BLE001 — stale-sweep is the backstop; never mask the caller's error
            self._logger.exception("questions_fail_write_failed", brand_id=str(brand_id))
            return
        self._logger.warning("questions_job_failed_marked", brand_id=str(brand_id))
