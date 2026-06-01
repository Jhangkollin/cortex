"""Analyze-job write model (one row per brand-profile extraction attempt)."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Column, Index
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel

from cortex_api.core.identifiers import uuid7


class AnalyzeJobStatus(StrEnum):
    """Lifecycle of a brand-profile analyze job."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class BrandProfileAnalysisJob(SQLModel, table=True):
    """An async SP-2 extraction attempt for a brand."""

    __tablename__ = "brand_profile_analysis_job"
    __table_args__ = (
        Index(
            "ix_brand_profile_analysis_job_brand_id_status",
            "brand_id",
            "status",
        ),
    )

    id: UUID = Field(default_factory=uuid7, primary_key=True)
    brand_id: UUID = Field(foreign_key="brand.id", index=True)
    status: AnalyzeJobStatus = Field(
        default=AnalyzeJobStatus.PENDING,
        sa_column=Column(
            SAEnum(
                AnalyzeJobStatus,
                values_callable=lambda enum_cls: [m.value for m in enum_cls],
                name="analyzejobstatus",
            ),
            nullable=False,
        ),
    )
    source_url: str = Field(max_length=2048)
    cost_usd: float | None = Field(default=None)
    error: str | None = Field(default=None)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow},
    )
