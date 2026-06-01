"""Process-wide tracker for fire-and-forget asyncio tasks.

Hook A (``BrandService.upsert_profile``) and Hook B
(``AnalyzeJobService._run`` success branch) schedule
``BrandPlacementComposer.compose`` via ``asyncio.create_task``. Holding a
strong reference is required — see ``asyncio.create_task`` docs: "the
event loop only keeps weak references to tasks." Without a tracker a
task may be garbage-collected mid-flight, surfacing as a silent
"Task was destroyed but it is pending!" warning.

The tracker owns three concerns:

* **Strong refs** so tasks finish before being collected.
* **Auto-cleanup** via ``add_done_callback`` so the set doesn't grow.
* **Exception logging** so a hook task's failure shows up in logs
  instead of vanishing.

``drain()`` is the lifespan-shutdown entry point: awaits everything
in-flight before the process exits. Exceptions are swallowed (already
logged in the done callback) so shutdown can't hang or raise.
"""

from __future__ import annotations

import asyncio

import structlog


class BackgroundTaskTracker:
    """Hold strong refs to fire-and-forget tasks; drain on shutdown."""

    def __init__(self) -> None:
        self._logger = structlog.get_logger(__name__)
        self._tasks: set[asyncio.Task[None]] = set()

    @property
    def count(self) -> int:
        return len(self._tasks)

    def track(self, task: asyncio.Task[None]) -> None:
        self._tasks.add(task)
        task.add_done_callback(self._on_done)

    async def drain(self) -> None:
        if not self._tasks:
            return
        await asyncio.gather(*tuple(self._tasks), return_exceptions=True)

    def _on_done(self, task: asyncio.Task[None]) -> None:
        self._tasks.discard(task)
        if task.cancelled():
            return
        exc = task.exception()
        if exc is not None:
            self._logger.error(
                "background_task_failed",
                task_name=task.get_name(),
                error=str(exc),
                error_type=type(exc).__name__,
            )
