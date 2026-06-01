"""BrandDashboardService — query service over Databricks gold tables.

CQRS read side. Takes `BrandTenantCtx` (already authorized at the dep level),
returns frozen read models. Use case names follow domain verbs:
`summarize_brand_impact`, `break_down_by_publisher` — describe what the actor
is doing in domain terms, not the underlying SQL.
"""

from __future__ import annotations

import structlog

from cortex_api.service.brand_dashboard.config import Config
from cortex_api.service.brand_dashboard.model.metrics import (
    BrandMetric,
    BrandMetricSet,
    PublisherBreakdown,
)
from cortex_api.service.brand_dashboard.repo.brand_metrics_repo import BrandMetricsRepo
from cortex_api.service.brand_identity.model.brand_tenant_ctx import BrandTenantCtx
from cortex_api.service.insights.model.metrics import TimeRange


class BrandDashboardService:
    """Brand Dashboard query service."""

    def __init__(
        self,
        repo: BrandMetricsRepo,
        redis_client: object,
        config: Config,
    ) -> None:
        self._logger = structlog.get_logger(__name__)
        self._repo = repo
        self._redis = redis_client
        self._config = config

    async def summarize_brand_impact(
        self,
        tenant: BrandTenantCtx,
        range: TimeRange,
    ) -> BrandMetricSet:
        """Return the 4 KPI snapshot for the tenant's brand. Redis-cached."""
        raise NotImplementedError("BrandDashboardService.summarize_brand_impact — Slice 1")

    async def break_down_by_publisher(
        self,
        tenant: BrandTenantCtx,
        metric: BrandMetric,
        range: TimeRange,
        limit: int = 20,
        offset: int = 0,
    ) -> PublisherBreakdown:
        """Per-publisher drill-down for one metric. Redis-cached per page."""
        raise NotImplementedError("BrandDashboardService.break_down_by_publisher — Slice 4")
