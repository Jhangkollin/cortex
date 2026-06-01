"""brand_report_ui_state — server-side dashboard UI flags, owned by brand_report.

One row per brand (brand_id is the PK). Tracks the one-time celebration and
hero-dismiss state that used to live in localStorage. Lives in the brand_report
bounded context (NOT on the `brand` identity aggregate) per CLAUDE.md.

  celebrate_pending  — armed at onboarding completion; consumed (→ false) on the
                       first Discover visit where the modal is shown.
  celebrate_consumed — set once the celebration has been consumed/dismissed.
                       Latches the "arm once" semantic: arm_celebrate refuses to
                       re-arm once this is true, so re-running onboarding can't
                       resurrect a dismissed celebration.
  hero_dismissed     — set when the user closes the hero card (permanent).
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, func, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, SQLModel


class BrandReportUiState(SQLModel, table=True):
    __tablename__ = "brand_report_ui_state"

    brand_id: UUID = Field(
        sa_column=Column(
            PG_UUID(as_uuid=True),
            ForeignKey("brand.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )
    celebrate_pending: bool = Field(
        sa_column=Column(Boolean, nullable=False, server_default=text("false")),
        default=False,
    )
    hero_dismissed: bool = Field(
        sa_column=Column(Boolean, nullable=False, server_default=text("false")),
        default=False,
    )
    celebrate_consumed: bool = Field(
        sa_column=Column(Boolean, nullable=False, server_default=text("false")),
        default=False,
    )
    created_at: datetime = Field(sa_column=Column(DateTime, nullable=False, server_default=text("NOW()")))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, nullable=False, server_default=text("NOW()"), onupdate=func.now())
    )
