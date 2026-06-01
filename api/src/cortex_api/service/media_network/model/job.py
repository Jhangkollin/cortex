# api/src/cortex_api/service/media_network/model/job.py
from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from sqlalchemy import Column, text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class MediaJobStatus(StrEnum):
    """Lifecycle of a brand media-network job."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


def _jsonb_list() -> Any:
    return Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))


class BrandMediaNetwork(SQLModel, table=True):
    """The persisted, deterministic media-network result for one brand."""

    __tablename__ = "brand_media_network"

    brand_id: UUID = Field(foreign_key="brand.id", primary_key=True)
    status: MediaJobStatus = Field(
        default=MediaJobStatus.PENDING,
        sa_column=Column(
            SAEnum(
                MediaJobStatus,
                values_callable=lambda enum_cls: [m.value for m in enum_cls],
                name="mediajobstatus",
            ),
            nullable=False,
        ),
    )
    error: str | None = Field(default=None)
    outlets: list[dict[str, Any]] = Field(default_factory=list, sa_column=_jsonb_list())
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow},
    )
