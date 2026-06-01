"""Observability middleware — bind a trace id to the request, structured access log.

Pure ASGI. Generates a trace id if absent, propagates via `x-trace-id` header.
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Awaitable, Callable
from typing import Any

import structlog
from structlog.contextvars import bind_contextvars, clear_contextvars


class ObservabilityMiddleware:
    """Bind structured logging context per request and emit access logs."""

    def __init__(self, app: Callable[..., Awaitable[Any]]) -> None:
        self._app = app
        self._logger = structlog.get_logger(__name__)

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Callable[..., Awaitable[Any]],
        send: Callable[..., Awaitable[Any]],
    ) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        trace_id = headers.get(b"x-trace-id", b"").decode() or uuid.uuid4().hex
        path = scope.get("path", "")
        method = scope.get("method", "")

        start = time.monotonic()
        clear_contextvars()
        bind_contextvars(trace_id=trace_id, path=path, method=method)

        # Wrap send so we can capture the status code and inject the trace header.
        status_code = {"value": 500}

        async def _send(message: dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                status_code["value"] = message.get("status", 0)
                hdrs = list(message.get("headers", []))
                hdrs.append((b"x-trace-id", trace_id.encode()))
                message["headers"] = hdrs
            await send(message)

        try:
            await self._app(scope, receive, _send)
        finally:
            duration_ms = (time.monotonic() - start) * 1000
            self._logger.info(
                "request_complete",
                status=status_code["value"],
                duration_ms=round(duration_ms, 2),
            )
            clear_contextvars()
