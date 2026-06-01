"""Hook A — BrandService.upsert_profile schedules composer task (COR-56).

After a profile upsert commits, BrandService MUST schedule a
``composer.compose(brand_id)`` task on the shared BackgroundTaskTracker
*outside* the session/transaction (per AD7 transaction-boundary verdict
R2). Composer failures must NOT propagate — the tracker's done-callback
logs them; the caller sees a successful upsert regardless.
"""

from __future__ import annotations

import asyncio
from uuid import UUID

from cortex_api.core.background import BackgroundTaskTracker
from cortex_api.core.identifiers import uuid7
from cortex_api.service.brand.model.profile import BrandProfile
from cortex_api.service.brand.service import BrandService


class _FakeSessionCtx:
    async def __aenter__(self) -> object:
        return object()

    async def __aexit__(self, *_: object) -> bool:
        return False


class _FakeDB:
    def session(self) -> _FakeSessionCtx:
        return _FakeSessionCtx()


class _FakeRepo:
    def __init__(self) -> None:
        self.store: dict[UUID, BrandProfile] = {}

    async def get(self, _session: object, brand_id: UUID) -> BrandProfile | None:
        return self.store.get(brand_id)

    async def upsert(self, _session: object, profile: BrandProfile) -> BrandProfile:
        self.store[profile.brand_id] = profile
        return profile


class _SpyComposer:
    def __init__(self, raise_on_compose: bool = False) -> None:
        self.calls: list[UUID] = []
        self._raise = raise_on_compose

    async def compose(self, brand_id: UUID) -> None:
        self.calls.append(brand_id)
        if self._raise:
            raise RuntimeError("composer boom")


def _svc(composer: _SpyComposer, tracker: BackgroundTaskTracker) -> BrandService:
    return BrandService(
        database_client=_FakeDB(),
        profile_repo=_FakeRepo(),
        config=object(),
        composer=composer,
        tracker=tracker,
    )


async def test_upsert_profile_schedules_composer_task() -> None:
    composer = _SpyComposer()
    tracker = BackgroundTaskTracker()
    svc = _svc(composer, tracker)
    bid = uuid7()

    saved = await svc.upsert_profile(bid, BrandProfile(brand_id=bid, name="Hooked Co"))

    # Task scheduled — exactly one in-flight before drain.
    assert tracker.count == 1
    await tracker.drain()

    assert composer.calls == [bid]
    assert saved.brand_id == bid
    assert saved.name == "Hooked Co"


async def test_upsert_profile_returns_saved_even_when_composer_fails() -> None:
    composer = _SpyComposer(raise_on_compose=True)
    tracker = BackgroundTaskTracker()
    svc = _svc(composer, tracker)
    bid = uuid7()

    saved = await svc.upsert_profile(bid, BrandProfile(brand_id=bid, name="Resilient Co"))

    # Caller is unaffected by composer failure.
    assert saved.brand_id == bid
    assert saved.name == "Resilient Co"

    # Composer was invoked; tracker drains without re-raising.
    await tracker.drain()
    assert composer.calls == [bid]
    # Give the done callback a tick to clean up.
    await asyncio.sleep(0)
    assert tracker.count == 0
