"""Brand report read service — poll and list report rows."""

from __future__ import annotations

from uuid import UUID

import structlog

from cortex_api.core.exceptions import NotFoundError
from cortex_api.infra.database_client import DatabaseClient
from cortex_api.service.brand_report.model.report import BrandReport
from cortex_api.service.brand_report.repo.report_repo import BrandReportRepo


class BrandReportService:
    """Read-only access to brand report rows (poll + list)."""

    def __init__(
        self,
        database_client: DatabaseClient,
        report_repo: BrandReportRepo,
    ) -> None:
        self._logger = structlog.get_logger(__name__)
        self._db = database_client
        self._report_repo = report_repo

    async def get_report(self, brand_id: UUID, report_id: str) -> BrandReport:
        async with self._db.session() as s:
            row = await self._report_repo.get(s, brand_id, report_id)
            if row is None:
                raise NotFoundError(f"report {report_id} not found for brand {brand_id}")
            return row

    async def list_reports(self, brand_id: UUID) -> list[BrandReport]:
        async with self._db.session() as s:
            return await self._report_repo.list_for_brand(s, brand_id)
