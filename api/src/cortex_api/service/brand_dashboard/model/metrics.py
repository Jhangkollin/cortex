"""Brand Dashboard API projection models.

The common metric/time-range primitives live in `service.insights`. This module
keeps only the Brand Dashboard's metric catalog binding and breakdown row
names. Future persona projections should reuse Insights primitives and define
their own app/API shaping instead of copying this package.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel

from cortex_api.service.insights.model import metrics as insights_metrics

__all__ = [
    "BrandMetric",
    "BrandMetricSet",
    "PublisherBreakdown",
    "PublisherRow",
]


class BrandMetric(StrEnum):
    """Metrics exposed by the Brand Dashboard projection."""

    ANSWER_PRODUCED = "answer_produced"
    ANSWER_VIEWS = "answer_views"
    LLM_CITATIONS = "llm_citations"
    BRAND_CLICKS = "brand_clicks"


BrandMetricSet = insights_metrics.MetricSet[BrandMetric]


class PublisherRow(BaseModel):
    """One row of the per-publisher breakdown."""

    publisher_id: str
    publisher_name: str
    value: int
    delta_pct: float
    points: list[int]


class PublisherBreakdown(BaseModel):
    """Full payload for `/v1/brand/{brand_id}/analytics/metrics/by-publisher`."""

    metric: BrandMetric
    range: insights_metrics.TimeRange
    total: int
    rows: list[PublisherRow]
