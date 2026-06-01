"""Async voice jobs: dedupe, in-process worker, sweep (structural twin of MediaNetworkJobService)."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any
from uuid import UUID

import structlog

from cortex_api.core.exceptions import NotFoundError
from cortex_api.infra.database_client import DatabaseClient
from cortex_api.service.brand.repo.profile_repo import BrandProfileRepo
from cortex_api.service.voice.config import Config
from cortex_api.service.voice.generator import generate_voice
from cortex_api.service.voice.model.job import BrandVoice, VoiceJobStatus
from cortex_api.service.voice.repo.brand_voice_repo import BrandVoiceRepo

GenerateFn = Callable[..., Awaitable[dict[str, str]]]


class VoiceJobService:
    """Owns the voice job lifecycle and the in-process generator worker.

    Structural twin of MediaNetworkJobService, minus snapshot/member repo.
    ``_tasks`` dict, create_task + done-callback, dedupe-on-start, drain,
    cancel_all, sweep_stale, and the ``_run`` try/except/CancelledError/mark_failed
    shape mirror MediaNetworkJobService exactly.

    Key difference from MediaNetworkJobService: no MemberRepo, no catalog fetch,
    no outlets. Profile is read via BrandProfileRepo; samples are produced by
    the generate_voice function.
    """

    def __init__(
        self,
        database_client: DatabaseClient,
        brand_voice_repo: BrandVoiceRepo,
        config: Config,
        brand_profile_repo: BrandProfileRepo,
        provider: Any | None = None,
        _generate: GenerateFn = generate_voice,
    ) -> None:
        self._logger = structlog.get_logger(__name__)
        self._db = database_client
        self._jobs = brand_voice_repo
        self._config = config
        self._brand_profile_repo = brand_profile_repo
        self._provider = provider
        self._generate = _generate
        # Maps each in-flight worker task to the brand_id it owns so graceful
        # shutdown can FAIL-mark the DB row before cancellation. Mirrors
        # MediaNetworkJobService._tasks — the add_done_callback below pops on
        # completion, keeping the dict bounded to genuinely in-flight work.
        self._tasks: dict[asyncio.Task[None], UUID] = {}

    async def start(self, brand_id: UUID, regenerate: bool = False) -> BrandVoice:
        """Start (or return) a voice job for brand_id.

        Dedupe logic mirrors MediaNetworkJobService.start:
        - If a row is PENDING or RUNNING, return it immediately (already in flight).
        - If a row is SUCCEEDED and regenerate=False, return the SUCCEEDED row.
        - A SUCCEEDED row generated BEFORE the brand profile was last updated is
          stale: the profile is the generator's input, so re-extracting it
          (e.g. re-onboarding the same brand with a different site) must
          regenerate — otherwise the brand keeps showing the previous profile's
          voice preview. Self-heals on the next start() with no caller change.
          (Same class of bug fixed for weekly questions in cortex#70.)
        - Otherwise, create/reset the row to PENDING and spawn a worker task.

        Invalidation is read-time (compare `profile.updated_at` here) rather
        than event-driven. This mirrors the weekly-questions service; both are
        profile-derived caches that each rediscover staleness independently. A
        shared invalidation seam (or a `BrandProfileUpdated` domain event) is
        the right consolidation now that a second cache needs this signal —
        tracked as a follow-up rather than blocking this fix.
        """
        async with self._db.session() as session:
            existing = await self._jobs.get(session, brand_id)
            stale_vs_profile = False
            profile_updated_at = None
            if existing is not None and existing.status == VoiceJobStatus.SUCCEEDED:
                profile = await self._brand_profile_repo.get(session, brand_id)
                profile_updated_at = profile.updated_at if profile is not None else None
                stale_vs_profile = (
                    profile_updated_at is not None
                    and existing.updated_at is not None
                    and profile_updated_at > existing.updated_at
                )
            existing_is_dedupable = existing is not None and (
                existing.status in (VoiceJobStatus.PENDING, VoiceJobStatus.RUNNING)
                or (existing.status == VoiceJobStatus.SUCCEEDED and not stale_vs_profile)
            )
            if existing is not None and not regenerate and existing_is_dedupable:
                self._logger.info(
                    "voice_job_dedup",
                    brand_id=str(brand_id),
                    status=existing.status,
                )
                return existing
            # Falling through to (re)generation. Log WHY dedup did not apply so the
            # stale-vs-profile self-heal leaves a breadcrumb — diagnosing the
            # "voice preview shows the previous brand" bug otherwise requires
            # reading both updated_at columns out of the DB by hand.
            self._logger.info(
                "voice_job_regenerate",
                brand_id=str(brand_id),
                reason=self._regenerate_reason(regenerate, existing, stale_vs_profile),
                existing_status=(existing.status if existing is not None else None),
                profile_updated_at=(str(profile_updated_at) if profile_updated_at is not None else None),
                existing_updated_at=(
                    str(existing.updated_at) if existing is not None and existing.updated_at is not None else None
                ),
            )
            job = await self._jobs.create(session, BrandVoice(brand_id=brand_id))
        task = asyncio.create_task(self._run(brand_id))
        self._tasks[task] = brand_id
        task.add_done_callback(lambda t: self._tasks.pop(t, None))
        return job

    @staticmethod
    def _regenerate_reason(
        regenerate: bool,
        existing: BrandVoice | None,
        stale_vs_profile: bool,
    ) -> str:
        """Classify why a (re)generation is happening, for the structured log."""
        if regenerate:
            return "regenerate_flag"
        if existing is None:
            return "no_row"
        if existing.status == VoiceJobStatus.FAILED:
            return "prior_failed"
        if stale_vs_profile:
            return "stale_vs_profile"
        return "not_dedupable"

    async def get(self, brand_id: UUID) -> BrandVoice:
        async with self._db.session() as session:
            row = await self._jobs.get(session, brand_id)
        if row is None:
            raise NotFoundError(f"no voice job for brand {brand_id}")
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
                    "voice_cancel_fail_write_failed",
                    brand_id=str(brand_id),
                )
            task.cancel()
        await self.drain()

    async def _run(self, brand_id: UUID) -> None:
        """In-process voice generator worker.

        Session split is deliberate (mirrors MediaNetworkJobService._run):
        - mark_running commits in its OWN session so RUNNING is visible to
          dedupe and stale-sweep while work is in flight.
        - mark_succeeded commits in ONE session with the samples payload so
          the write is atomic — never a half-state of samples-written-but-status-RUNNING.
        """
        try:
            async with self._db.session() as session:
                await self._jobs.mark_running(session, brand_id)
                profile_row = await self._brand_profile_repo.get(session, brand_id)
            profile = {
                "name": (profile_row.name if profile_row else "") or "",
                # industry_vertical is the semantic equivalent of "category" in the
                # brand profile — maps to the generator's category key.
                "category": (profile_row.industry_vertical if profile_row else "") or "",
                "about": (profile_row.about if profile_row else "") or "",
                "tagline": (profile_row.tagline if profile_row else "") or "",
                "products": (profile_row.products if profile_row else []) or [],
                "competitors": (profile_row.competitors if profile_row else []) or [],
                "voice_samples": (profile_row.voice_samples if profile_row else []) or [],
            }
            samples = await self._generate(profile, self._provider)
            async with self._db.session() as session:
                await self._jobs.mark_succeeded(session, brand_id, samples)
        except asyncio.CancelledError:
            raise
        except Exception as e:  # noqa: BLE001 — worker boundary must not die silently
            self._logger.exception("voice_job_failed", brand_id=str(brand_id))
            await self._fail(brand_id, str(e))

    async def _fail(self, brand_id: UUID, message: str) -> None:
        """Best-effort mark-failed helper — mirrors MediaNetworkJobService._fail."""
        try:
            async with self._db.session() as session:
                await self._jobs.mark_failed(session, brand_id, message)
        except Exception:  # noqa: BLE001 — stale-sweep is the backstop; never mask the caller's error
            self._logger.exception("voice_fail_write_failed", brand_id=str(brand_id))
            return
        self._logger.warning("voice_job_failed_marked", brand_id=str(brand_id))
