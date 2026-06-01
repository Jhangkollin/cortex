"""Hook B — AnalyzeJobService._run success branch fires composer task (COR-56).

After the SP-2 extraction commits the profile + `mark_succeeded`,
``_run`` MUST schedule a ``composer.compose(brand_id)`` task on the
shared tracker BEFORE emitting ``analyze_succeeded``. The composer
runs in its own session (per AD7 R2), and its failure must not
re-raise into the analyze worker.

The failure path (extractor raises) MUST NOT fire the composer —
the profile wasn't written, so there's nothing to materialise from.
"""

from __future__ import annotations

from types import SimpleNamespace
from uuid import UUID, uuid4

import structlog

from cortex_api.core.background import BackgroundTaskTracker
from cortex_api.service.brand.analyze_service import AnalyzeJobService


class _FakeSessionCtx:
    async def __aenter__(self) -> object:
        return object()

    async def __aexit__(self, *_: object) -> bool:
        return False


class _FakeDB:
    def session(self) -> _FakeSessionCtx:
        return _FakeSessionCtx()


class _FakeJobsRepo:
    def __init__(self) -> None:
        self.marked_running: list[UUID] = []
        self.marked_succeeded: list[UUID] = []
        self.marked_failed: list[tuple[UUID, str]] = []

    async def get(self, _session: object, _brand_id: UUID, job_id: UUID) -> object:
        return SimpleNamespace(id=job_id)

    async def mark_running(self, _session: object, job: object) -> None:
        self.marked_running.append(job.id)  # type: ignore[attr-defined]

    async def mark_succeeded(self, _session: object, job: object, *, cost_usd: float) -> None:
        self.marked_succeeded.append(job.id)  # type: ignore[attr-defined]
        del cost_usd

    async def mark_failed(self, _session: object, job: object, *, error: str) -> None:
        self.marked_failed.append((job.id, error))  # type: ignore[attr-defined]


class _FakeProfileRepo:
    def __init__(self) -> None:
        self.upserts: list[UUID] = []

    async def upsert(self, _session: object, profile: object) -> None:
        self.upserts.append(profile.brand_id)  # type: ignore[attr-defined]


class _SpyComposer:
    def __init__(self) -> None:
        self.calls: list[UUID] = []

    async def compose(self, brand_id: UUID) -> None:
        self.calls.append(brand_id)


class _FakeConfig:
    tier = "default"
    stale_job_seconds = 60


def _sp2_result(brand_id: UUID) -> SimpleNamespace:
    # Shape sp2_to_sp1_profile reads from; only the attrs `_run` touches
    # need to be set.
    return SimpleNamespace(
        brand_id=brand_id,
        name="Extracted Co",
        extraction_meta=SimpleNamespace(cost_usd=0.123),
    )


def _make_service(
    composer: _SpyComposer,
    tracker: BackgroundTaskTracker,
    jobs: _FakeJobsRepo,
    profiles: _FakeProfileRepo,
    *,
    extract_raises: Exception | None = None,
) -> AnalyzeJobService:
    bid = uuid4()

    async def _fake_extract(_url: str, **_kwargs: object) -> SimpleNamespace:
        if extract_raises is not None:
            raise extract_raises
        return _sp2_result(bid)

    svc = object.__new__(AnalyzeJobService)
    svc._logger = structlog.get_logger(__name__)  # type: ignore[attr-defined]
    svc._db = _FakeDB()  # type: ignore[attr-defined]
    svc._jobs = jobs  # type: ignore[attr-defined]
    svc._profiles = profiles  # type: ignore[attr-defined]
    svc._config = _FakeConfig()  # type: ignore[attr-defined]
    svc._extract = _fake_extract  # type: ignore[attr-defined]
    svc._tasks = {}  # type: ignore[attr-defined]
    svc._composer = composer  # type: ignore[attr-defined]
    svc._tracker = tracker  # type: ignore[attr-defined]
    return svc


async def test_run_success_schedules_composer_task(monkeypatch) -> None:  # noqa: ANN001
    composer = _SpyComposer()
    tracker = BackgroundTaskTracker()
    jobs = _FakeJobsRepo()
    profiles = _FakeProfileRepo()

    brand_id = uuid4()
    job_id = uuid4()

    # build_provider is called inside _run; stub it out so no real SP-2 path is hit.
    import cortex_api.service.brand.analyze_service as mod

    monkeypatch.setattr(mod, "build_provider", lambda _cfg: object())
    monkeypatch.setattr(mod, "sp2_to_sp1_profile", lambda bid, _r: SimpleNamespace(brand_id=bid))

    svc = _make_service(composer, tracker, jobs, profiles)

    await svc._run(brand_id, job_id, "https://example.com")

    # Profile written, job succeeded.
    assert profiles.upserts == [brand_id]
    assert jobs.marked_succeeded == [job_id]

    # Hook B fired exactly one composer task.
    assert tracker.count == 1
    await tracker.drain()
    assert composer.calls == [brand_id]


async def test_run_failure_does_not_schedule_composer_task(monkeypatch) -> None:  # noqa: ANN001
    from cortex_brand_extract.errors import ExtractError

    composer = _SpyComposer()
    tracker = BackgroundTaskTracker()
    jobs = _FakeJobsRepo()
    profiles = _FakeProfileRepo()

    brand_id = uuid4()
    job_id = uuid4()

    import cortex_api.service.brand.analyze_service as mod

    monkeypatch.setattr(mod, "build_provider", lambda _cfg: object())

    svc = _make_service(
        composer,
        tracker,
        jobs,
        profiles,
        extract_raises=ExtractError("boom"),
    )

    # ExtractError is re-raised as UpstreamError by the service.
    import contextlib

    with contextlib.suppress(Exception):
        await svc._run(brand_id, job_id, "https://example.com")

    # Profile NOT written, job FAILED, composer NOT scheduled.
    assert profiles.upserts == []
    assert jobs.marked_failed and jobs.marked_failed[0][0] == job_id
    assert composer.calls == []
    assert tracker.count == 0
