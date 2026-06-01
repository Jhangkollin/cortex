"""FastAPI exception handlers — map domain exceptions to HTTP responses.

12-factor rules (wiki §4):
- 5xx CortexExceptions log at `error` (so alerts fire); 4xx log at `warning`.
- Bare `Exception` is a first-class case — caught here so it doesn't leak
  tracebacks via FastAPI's default handler.
- Every error response carries `error_id` = current trace_id, so support
  tickets that screenshot the body can be correlated to log lines.
"""

from __future__ import annotations

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from structlog.contextvars import get_contextvars

from cortex_api.core.exceptions import (
    BadRequestError,
    CacheError,
    ConflictError,
    ContextMismatchError,
    CortexException,
    DataPipelineError,
    DomainValidationError,
    ForbiddenError,
    MembershipError,
    NotFoundError,
    NotImplementedYetError,
    RateLimitedError,
    UnauthorizedError,
    UpstreamError,
    UpstreamTimeoutError,
    WrongContextError,
)


def _status_for(exc: CortexException) -> int:
    """Map a Cortex exception to its HTTP status code."""
    if isinstance(exc, BadRequestError | DomainValidationError | ContextMismatchError | WrongContextError):
        return 400
    if isinstance(exc, UnauthorizedError):
        return 401
    if isinstance(exc, ForbiddenError | MembershipError):
        return 403
    if isinstance(exc, NotFoundError):
        return 404
    if isinstance(exc, ConflictError):
        return 409
    if isinstance(exc, RateLimitedError):
        return 429
    if isinstance(exc, NotImplementedYetError):
        return 501
    if isinstance(exc, UpstreamTimeoutError):
        return 504
    if isinstance(exc, UpstreamError | CacheError | DataPipelineError):
        return 502
    return 500


def _trace_id() -> str:
    """Pull the current trace_id from structlog contextvars."""
    return str(get_contextvars().get("trace_id") or "unknown")


def register_exception_handlers(app: FastAPI) -> None:
    """Register all handlers on the FastAPI app."""
    logger = structlog.get_logger(__name__)

    @app.exception_handler(CortexException)
    async def _cortex_handler(_: Request, exc: CortexException) -> JSONResponse:
        status = _status_for(exc)
        log_method = logger.error if status >= 500 else logger.warning
        log_method(
            "cortex_exception",
            type=type(exc).__name__,
            status=status,
            msg=str(exc),
        )
        return JSONResponse(
            status_code=status,
            content={
                "error": type(exc).__name__,
                "message": str(exc),
                "error_id": _trace_id(),
            },
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": "ValidationError",
                "details": exc.errors(),
                "error_id": _trace_id(),
            },
        )

    @app.exception_handler(Exception)
    async def _bare_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        """Last-resort handler. Never echoes the exception message —
        bare exceptions are the ones most likely to leak upstream text or
        framework internals.
        """
        logger.exception("unhandled_exception", type=type(exc).__name__)
        return JSONResponse(
            status_code=500,
            content={
                "error": "InternalError",
                "error_id": _trace_id(),
            },
        )
