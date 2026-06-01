"""structlog configuration — JSON output to stdout for CloudWatch / Loki.

Always import via `structlog.get_logger(__name__)` inside class `__init__` or
function bodies. Never as a module-level singleton (it picks up the wrong
processor chain at import time).
"""

from __future__ import annotations

import logging
import sys

import structlog

from cortex_api.core.config.log_config import LogConfig


def configure_logging(config: LogConfig) -> None:
    """Configure structlog and the stdlib root logger.

    Called once at app startup from main.create_app(). Uses the stdlib
    LoggerFactory so structlog plays cleanly with uvicorn's own log handlers
    and so `add_logger_name` works (PrintLoggerFactory has no `.name`).
    """
    level_name = config.level.upper()
    level = logging.getLevelNamesMapping().get(level_name, logging.INFO)

    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    renderer: structlog.types.Processor
    if config.format == "json":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=sys.stdout.isatty())

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure root stdlib logger so uvicorn / library logs go through the
    # same handler chain. Format is `%(message)s` because structlog has
    # already rendered.
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    for noisy in ("uvicorn.access", "httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
