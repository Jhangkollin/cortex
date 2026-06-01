"""Typed errors. Mirrors agent-will-smith's UpstreamError/UpstreamTimeoutError
naming so cortex-api error handling stays consistent when it consumes the lib.
"""

from __future__ import annotations


class ExtractError(Exception):
    """Base for all extraction failures."""

    def __init__(self, message: str, *, stage: str | None = None) -> None:
        super().__init__(message)
        self.stage = stage


class UpstreamError(ExtractError):
    """An upstream dependency (LLM, network) failed."""


class UpstreamTimeoutError(UpstreamError):
    """An upstream dependency timed out."""
