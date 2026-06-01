"""Brand Dashboard adapter onto Databricks gold tables.

Note: this is NOT a DDD repository. It is a Brand Dashboard adapter over
Databricks gold tables and does not own any persisted aggregate. This class
translates rows into read models built from shared insights primitives.
"""

from __future__ import annotations

from uuid import UUID

from cortex_api.infra.databricks_client import DatabricksClient
from cortex_api.service.brand_dashboard.config import Config
from cortex_api.service.brand_dashboard.model.metrics import (
    BrandMetric,
    BrandMetricSet,
    PublisherBreakdown,
)
from cortex_api.service.insights.model.metrics import TimeRange


class BrandMetricsRepo:
    """Reads from `gold_brand_answer_metrics` and `gold_brand_publisher_breakdown`."""

    def __init__(self, databricks_client: DatabricksClient, config: Config) -> None:
        self._db = databricks_client
        self._config = config

    async def fetch_impact_stats(self, brand_id: UUID, range: TimeRange) -> BrandMetricSet:
        """SELECT one row from `gold_brand_answer_metrics` filtered by brand_uuid."""
        raise NotImplementedError("BrandMetricsRepo.fetch_impact_stats — Slice 1")

    async def fetch_by_publisher(
        self,
        brand_id: UUID,
        metric: BrandMetric,
        range: TimeRange,
        limit: int,
        offset: int,
    ) -> PublisherBreakdown:
        """SELECT N rows from `gold_brand_publisher_breakdown` filtered by brand_uuid."""
        raise NotImplementedError("BrandMetricsRepo.fetch_by_publisher — Slice 4")
