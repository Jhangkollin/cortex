"""Persona-neutral insights value objects.

These are read-side models for Databricks gold-table projections. They are not
SQLModel entities and do not represent persisted Cortex aggregates.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class TimeRange(StrEnum):
    """Supported time windows for insights projections."""

    DAYS_7 = "7d"
    DAYS_30 = "30d"
    DAYS_90 = "90d"
    MTD = "mtd"


class MetricSnapshot(BaseModel):
    """Single metric value for one period."""

    value: int
    delta_pct: float
    points: list[int]


class MetricSet[MetricName: StrEnum](BaseModel):
    """A named collection of metric snapshots for one time range."""

    range: TimeRange
    refreshed_at: datetime
    metrics: dict[MetricName, MetricSnapshot]
