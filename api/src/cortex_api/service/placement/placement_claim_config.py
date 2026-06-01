"""Config for placement-claims (COR-75 / AD8).

Centralises the lease TTL, L3 freshness window, and GC retention so all
three AD8 constants have a single source of truth and can be tuned per
environment via ``CORTEX_PLACEMENT_*`` env vars.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class PlacementClaimConfig(BaseSettings):
    """Tunable AD8 constants for the placement-claims pipeline."""

    model_config = SettingsConfigDict(env_prefix="CORTEX_PLACEMENT_", extra="forbid")

    # AD8 lease TTL: how long an in_flight claim holds the (publisher, article) lock.
    # Pod-crash takeover fires once expires_at < NOW.
    lease_ttl_seconds: int = 60

    # AD8 L3 freshness window: how long a 'done' claim is reusable as a read-through
    # cache. Past this, the next caller wins and re-computes.
    freshness_window_seconds: int = 300

    # GC retention: how long completed / old-failed rows survive before the daily
    # sweep deletes them.
    gc_retention_days: int = 30
