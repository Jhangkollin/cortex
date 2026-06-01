"""brand_report write-side envelope. The report payload is an immutable
JSONB snapshot (the serialized ReportDTO); this row tracks identity,
version, status, and archival. One brand has many reports (versions)."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from sqlalchemy import Column, DateTime, Index, UniqueConstraint, func, text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from cortex_api.core.identifiers import uuid7


class BrandReportStatus(StrEnum):
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"


class BrandReport(SQLModel, table=True):
    __tablename__ = "brand_report"
    __table_args__ = (
        Index("ix_brand_report_brand_id_status", "brand_id", "status"),
        UniqueConstraint("brand_id", "version", name="uq_brand_report_brand_id_version"),
        Index(
            "uq_brand_report_one_current",
            "brand_id",
            unique=True,
            postgresql_where=text("status = 'ready' AND archived_at IS NULL"),
        ),
    )

    id: UUID = Field(default_factory=uuid7, primary_key=True)
    brand_id: UUID = Field(foreign_key="brand.id", index=True)
    report_id: str = Field(max_length=64, index=True)
    version: str = Field(max_length=16)
    status: BrandReportStatus = Field(
        default=BrandReportStatus.GENERATING,
        sa_column=Column(
            SAEnum(
                BrandReportStatus,
                values_callable=lambda enum_cls: [m.value for m in enum_cls],
                name="brandreportstatus",
            ),
            nullable=False,
        ),
    )
    report_json: dict[str, Any] | None = Field(default=None, sa_column=Column(JSONB, nullable=True))
    cost_usd: float | None = Field(default=None)
    error: str | None = Field(default=None)
    archived_at: datetime | None = Field(default=None)
    created_at: datetime = Field(sa_column=Column(DateTime, nullable=False, server_default=text("NOW()")))
    updated_at: datetime = Field(
        sa_column=Column(DateTime, nullable=False, server_default=text("NOW()"), onupdate=func.now())
    )
