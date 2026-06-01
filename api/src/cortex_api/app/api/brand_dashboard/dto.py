"""Brand Dashboard endpoint DTOs."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from cortex_api.service.brand_dashboard.model.metrics import BrandMetric


class TimeRange(StrEnum):
    DAYS_7 = "7d"
    DAYS_30 = "30d"
    DAYS_90 = "90d"
    MTD = "mtd"


class MetricSnapshot(BaseModel):
    value: int
    delta_pct: float = Field(description="% change vs previous same-length period")
    points: list[int] = Field(description="Sparkline series, daily grain")


class ImpactStatsResponse(BaseModel):
    range: TimeRange
    refreshed_at: datetime
    metrics: dict[BrandMetric, MetricSnapshot] = Field(
        description="Keyed by metric: answer_produced, answer_views, llm_citations, brand_clicks"
    )


class PublisherRow(BaseModel):
    publisher_id: str
    publisher_name: str
    value: int
    delta_pct: float
    points: list[int]


class PublisherBreakdownResponse(BaseModel):
    metric: BrandMetric
    range: TimeRange
    total: int
    rows: list[PublisherRow]
