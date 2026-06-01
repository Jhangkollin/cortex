"""Brand Report UI-state service — owns the `brand_report_ui_state` lifecycle.

  get_ui_state       — read the flags; returns defaults if no row exists yet.
  arm_celebrate      — set celebrate_pending=true, but ONLY IF celebrate_consumed
                       is false (so re-running onboarding can't resurrect a
                       celebration the user already dismissed — "arm once").
  consume_celebrate  — set celebrate_pending=false, celebrate_consumed=true
                       (idempotent; latches the consumed state).
  dismiss_hero       — set hero_dismissed=true (permanent).

The row is created lazily on first write. Reads of a brand that has never
written UI state return all-false defaults (not an error) — the absence of a
row simply means "nothing armed, nothing dismissed".
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

import structlog

from cortex_api.infra.database_client import DatabaseClient
from cortex_api.service.brand_report.model.report import BrandReportStatus
from cortex_api.service.brand_report.repo.report_repo import BrandReportRepo
from cortex_api.service.brand_report.repo.ui_state_repo import ReportUiStateRepo


@dataclass(slots=True, frozen=True)
class ReportUiState:
    celebrate_pending: bool
    hero_dismissed: bool
    celebrate_ready: bool


class BrandReportUiStateService:
    def __init__(
        self,
        database_client: DatabaseClient,
        ui_state_repo: ReportUiStateRepo,
        report_repo: BrandReportRepo,
    ) -> None:
        self._logger = structlog.get_logger(__name__)
        self._db = database_client
        self._repo = ui_state_repo
        self._report_repo = report_repo

    async def get_ui_state(self, brand_id: UUID) -> ReportUiState:
        async with self._db.session() as session:
            row = await self._repo.get(session, brand_id)
            if row is None:
                return ReportUiState(
                    celebrate_pending=False,
                    hero_dismissed=False,
                    celebrate_ready=False,
                )
            current = await self._report_repo.get_current(session, brand_id)
            celebrate_ready = (
                row.celebrate_pending
                and not row.celebrate_consumed
                and current is not None
                # Defensive re-check: get_current already filters to status==READY,
                # but we re-assert it here so celebrate_ready stays correct even if
                # that contract ever loosens. Intentional, not dead code.
                and current.status == BrandReportStatus.READY
            )
            return ReportUiState(
                celebrate_pending=row.celebrate_pending,
                hero_dismissed=row.hero_dismissed,
                celebrate_ready=celebrate_ready,
            )

    async def arm_celebrate(self, brand_id: UUID) -> None:
        """Set celebrate_pending=true ONLY IF it was never consumed.

        Idempotent + safe to re-run from onboarding: once the celebration has
        been consumed (celebrate_consumed=true), arming is a no-op so a dismissed
        celebration can't be resurrected.
        """
        async with self._db.session() as session:
            row = await self._repo.get_or_create(session, brand_id)
            if row.celebrate_consumed:
                self._logger.info("report_celebrate_arm_skipped_consumed", brand_id=str(brand_id))
                return
            row.celebrate_pending = True
            session.add(row)
            await session.commit()
        self._logger.info("report_celebrate_armed", brand_id=str(brand_id))

    async def consume_celebrate(self, brand_id: UUID) -> None:
        """Set celebrate_pending=false, celebrate_consumed=true. Idempotent."""
        async with self._db.session() as session:
            row = await self._repo.get_or_create(session, brand_id)
            row.celebrate_pending = False
            row.celebrate_consumed = True
            session.add(row)
            await session.commit()
        self._logger.info("report_celebrate_consumed", brand_id=str(brand_id))

    async def dismiss_hero(self, brand_id: UUID) -> None:
        """Set hero_dismissed=true. Permanent dismissal."""
        async with self._db.session() as session:
            row = await self._repo.get_or_create(session, brand_id)
            row.hero_dismissed = True
            session.add(row)
            await session.commit()
        self._logger.info("report_hero_dismissed", brand_id=str(brand_id))
