# api/src/cortex_api/service/questions/model/job.py
from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from sqlalchemy import Column, text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class QuestionJobStatus(StrEnum):
    """Lifecycle of a brand weekly-questions job."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


def _jsonb_list() -> Any:
    return Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))


class BrandWeeklyQuestions(SQLModel, table=True):
    """The persisted, deterministic weekly-questions result for one brand."""

    __tablename__ = "brand_weekly_questions"

    brand_id: UUID = Field(foreign_key="brand.id", primary_key=True)
    status: QuestionJobStatus = Field(
        default=QuestionJobStatus.PENDING,
        sa_column=Column(
            SAEnum(
                QuestionJobStatus,
                values_callable=lambda enum_cls: [m.value for m in enum_cls],
                name="questionjobstatus",
            ),
            nullable=False,
        ),
    )
    error: str | None = Field(default=None)
    questions: list[dict[str, Any]] = Field(default_factory=list, sa_column=_jsonb_list())
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow},
    )
