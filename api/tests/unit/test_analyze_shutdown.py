from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest

import cortex_api.main as main_mod
from cortex_api.service.brand.analyze_service import AnalyzeJobService


@pytest.mark.asyncio
async def test_cancel_all_cancels_running_tasks() -> None:
    svc = object.__new__(AnalyzeJobService)
    svc._tasks = {}  # type: ignore[attr-defined]

    fail_calls: list[tuple] = []

    async def _fake_fail(brand_id, job_id, message):  # noqa: ANN001, ANN202
        fail_calls.append((brand_id, job_id, message))

    svc._fail = _fake_fail  # type: ignore[attr-defined,method-assign]

    async def _forever() -> None:
        await asyncio.sleep(3600)

    brand_id, job_id = uuid4(), uuid4()
    t = asyncio.create_task(_forever())
    svc._tasks[t] = (brand_id, job_id)  # type: ignore[attr-defined]
    t.add_done_callback(lambda task: svc._tasks.pop(task, None))  # type: ignore[attr-defined]

    await AnalyzeJobService.cancel_all(svc)

    assert t.cancelled()
    assert svc._tasks == {}  # type: ignore[attr-defined]
    # cancel_all FAIL-marks the in-flight row before cancelling the task.
    assert fail_calls == [(brand_id, job_id, "cancelled at shutdown")]


@pytest.mark.asyncio
async def test_periodic_sweep_task_created_and_cancelled_on_shutdown(monkeypatch) -> None:  # noqa: ANN001
    """The lifespan must spawn the periodic sweep task and cancel it cleanly
    on shutdown (no 'Task exception was never retrieved').

    The fake ``sleep`` blocks on an Event after the first periodic tick so the
    loop fires exactly once and then *parks* (no busy-spin) — proving both the
    happy path and that shutdown cancels a parked loop cleanly.
    """
    startup_swept = asyncio.Event()
    periodic_swept = asyncio.Event()
    park = asyncio.Event()

    class _FakeAnalyzeService:
        def __init__(self) -> None:
            self.sweep_calls = 0
            self.cancel_all_called = False

        async def sweep_stale(self) -> int:
            self.sweep_calls += 1
            if self.sweep_calls == 1:
                startup_swept.set()
            else:
                periodic_swept.set()
            return 0

        async def cancel_all(self) -> None:
            self.cancel_all_called = True

    class _FakeAnalyzeConfig:
        stale_job_seconds = 1

    fake_svc = _FakeAnalyzeService()
    monkeypatch.setattr(main_mod._brand_container, "analyze_service", lambda: fake_svc)
    monkeypatch.setattr(main_mod._brand_container, "analyze_config", lambda: _FakeAnalyzeConfig())

    async def _fake_sleep(_seconds: float) -> None:
        # First call: return immediately so the loop ticks once. After that,
        # block on `park` so the loop suspends instead of busy-looping until
        # shutdown cancels it.
        if not periodic_swept.is_set():
            return
        await park.wait()

    monkeypatch.setattr(main_mod.asyncio, "sleep", _fake_sleep)

    tasks_before = asyncio.all_tasks()
    async with main_mod._lifespan(object()):  # type: ignore[arg-type]
        await asyncio.wait_for(startup_swept.wait(), timeout=2.0)
        await asyncio.wait_for(periodic_swept.wait(), timeout=2.0)
        new_tasks = asyncio.all_tasks() - tasks_before
        assert any(not t.done() for t in new_tasks), "periodic sweep task should be running"

    # After the lifespan exits the periodic task is gone and shutdown ran.
    leftover = [t for t in (asyncio.all_tasks() - tasks_before) if not t.done()]
    assert leftover == []
    assert fake_svc.cancel_all_called
    assert fake_svc.sweep_calls == 2  # startup + exactly one periodic tick
