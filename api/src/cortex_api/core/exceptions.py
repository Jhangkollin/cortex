"""Cortex API exception hierarchy.

All raised exceptions in cortex-api MUST come from this module. Always chain
with `from e` to preserve cause. Exception → HTTP status mapping happens in
app/exception_handlers.py.

Mirrors agent-will-smith's exception design.
"""

from __future__ import annotations


class CortexException(Exception):
    """Root exception for all cortex-api errors."""


# --- Client errors (4xx) ----------------------------------------------------


class BadRequestError(CortexException):
    """Malformed request, bad input."""


class DomainValidationError(CortexException):
    """Validation failed at the domain layer (beyond Pydantic shape)."""


class UnauthorizedError(CortexException):
    """JWT missing, invalid, or expired."""


class ForbiddenError(CortexException):
    """Authenticated but not authorized for this resource (role / capability)."""


class NotFoundError(CortexException):
    """Resource does not exist (or is hidden by tenant scope)."""


class ConflictError(CortexException):
    """Resource state conflict (e.g. duplicate, optimistic concurrency)."""


class RateLimitedError(CortexException):
    """Caller exceeded rate limits."""


# --- Tenancy / auth errors --------------------------------------------------


class WrongContextError(CortexException):
    """Active context kind doesn't match route expectation.

    Example: route expects brand context but JWT says active context is publisher.
    """


class ContextMismatchError(CortexException):
    """URL identifier doesn't match the active context in the JWT.

    Example: URL says /v1/brand/{X}/... but JWT's active context id is Y.
    """


class MembershipError(CortexException):
    """User has no valid membership for the requested tenant."""


# --- Server / upstream errors (5xx) -----------------------------------------


class UpstreamError(CortexException):
    """A dependency (Databricks SQL, RDS, Redis, OAuth provider) failed."""


class UpstreamTimeoutError(UpstreamError):
    """Upstream call timed out."""


class DataPipelineError(CortexException):
    """Underlying gold table is missing/empty/stale beyond tolerance."""


class CacheError(CortexException):
    """Redis read/write failure that we couldn't degrade past."""


# --- Implementation status --------------------------------------------------


class NotImplementedYetError(CortexException):
    """Endpoint is registered but the feature isn't implemented yet (501).

    Used for routers that exist for OpenAPI / contract surface area before
    the underlying service work lands. Distinct from a 500 — the caller
    can rely on a 501 meaning "deliberately stubbed, retry later won't help".
    """
