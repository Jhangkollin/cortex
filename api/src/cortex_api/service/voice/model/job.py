from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from sqlalchemy import Column, text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class VoiceJobStatus(StrEnum):
    """Lifecycle of a brand voice job."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


def _jsonb_obj() -> Any:
    return Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))


class BrandVoice(SQLModel, table=True):
    """The persisted, deterministic voice result for one brand."""

    __tablename__ = "brand_voice"

    brand_id: UUID = Field(foreign_key="brand.id", primary_key=True)
    status: VoiceJobStatus = Field(
        default=VoiceJobStatus.PENDING,
        sa_column=Column(
            SAEnum(
                VoiceJobStatus,
                values_callable=lambda enum_cls: [m.value for m in enum_cls],
                name="voicejobstatus",
            ),
            nullable=False,
        ),
    )
    error: str | None = Field(default=None)
    samples: dict[str, str] = Field(default_factory=dict, sa_column=_jsonb_obj())
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow},
    )
