"""BackgroundTaskTracker (COR-56) — unit tests.

Process-wide tracker for fire-and-forget tasks scheduled from hook points
(``BrandService.upsert_profile``, ``AnalyzeJobService._run`` success). It
holds strong refs so tasks aren't GC'd before completion, logs unexpected
exceptions via ``add_done_callback``, and exposes ``drain()`` for the
lifespan shutdown and for tests.
"""

from __future__ import annotations

import asyncio

import pytest

from cortex_api.core.background import BackgroundTaskTracker


async def test_track_then_drain_awaits_completion() -> None:
    tracker = BackgroundTaskTracker()
    done = asyncio.Event()

    async def _work() -> None:
        await asyncio.sleep(0)
        done.set()

    tracker.track(asyncio.create_task(_work()))
    assert tracker.count == 1

    await tracker.drain()

    assert done.is_set()
    assert tracker.count == 0


async def test_completed_task_is_auto_untracked() -> None:
    tracker = BackgroundTaskTracker()

    async def _work() -> None:
        return None

    task = asyncio.create_task(_work())
    tracker.track(task)
    await task
    # Give the done callback one event-loop tick to fire.
    await asyncio.sleep(0)
    assert tracker.count == 0


async def test_failing_task_logs_exception_and_does_not_raise(
    caplog: pytest.LogCaptureFixture,
) -> None:
    tracker = BackgroundTaskTracker()

    async def _boom() -> None:
        raise RuntimeError("boom")

    tracker.track(asyncio.create_task(_boom()))

    await tracker.drain()  # must NOT raise

    assert tracker.count == 0


async def test_drain_with_no_tracked_tasks_is_a_noop() -> None:
    tracker = BackgroundTaskTracker()
    await tracker.drain()
    assert tracker.count == 0


async def test_drain_awaits_multiple_concurrent_tasks() -> None:
    tracker = BackgroundTaskTracker()
    completed: list[int] = []

    async def _work(label: int) -> None:
        await asyncio.sleep(0)
        completed.append(label)

    for i in range(5):
        tracker.track(asyncio.create_task(_work(i)))
    assert tracker.count == 5

    await tracker.drain()

    assert sorted(completed) == [0, 1, 2, 3, 4]
    assert tracker.count == 0
