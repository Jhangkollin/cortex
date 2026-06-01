"""CRUD on the `brand_report_ui_state` table.

Thin query object — does not own a transaction; callers supply the session.
The row is created lazily on first write (upsert via get-or-create).
"""

from __future__ import annotations

from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from cortex_api.service.brand_report.model.ui_state import BrandReportUiState


class ReportUiStateRepo:
    """CRUD on `brand_report_ui_state` (one row per brand)."""

    async def get(self, session: AsyncSession, brand_id: UUID) -> BrandReportUiState | None:
        result = await session.exec(select(BrandReportUiState).where(BrandReportUiState.brand_id == brand_id))
        return result.first()

    async def get_or_create(self, session: AsyncSession, brand_id: UUID) -> BrandReportUiState:
        """Return the brand's UI-state row, creating a defaults row if absent.

        The FK to brand.id means a non-existent brand_id raises IntegrityError
        on flush — callers that need a 404 should pre-check brand existence.
        """
        row = await self.get(session, brand_id)
        if row is not None:
            return row
        row = BrandReportUiState(brand_id=brand_id)
        session.add(row)
        await session.flush()
        return row
