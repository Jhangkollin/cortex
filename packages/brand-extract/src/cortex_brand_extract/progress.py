"""Progress reporting. A ProgressSink is any object with `async emit(event)`.
The pipeline emits one or more events per stage; the MCP server maps them to
MCP progress notifications.
"""

from __future__ import annotations

from typing import Literal, Protocol

from pydantic import BaseModel

StageStatus = Literal["running", "ok", "warn", "error"]


class ProgressEvent(BaseModel):
    stage: str
    status: StageStatus
    detail: str = ""


class ProgressSink(Protocol):
    async def emit(self, event: ProgressEvent) -> None: ...


class ListSink:
    """Test/in-memory sink."""

    def __init__(self) -> None:
        self.events: list[ProgressEvent] = []

    async def emit(self, event: ProgressEvent) -> None:
        self.events.append(event)


async def emit(sink: ProgressSink | None, event: ProgressEvent) -> None:
    """None-safe emit so call sites stay terse."""
    if sink is not None:
        await sink.emit(event)
