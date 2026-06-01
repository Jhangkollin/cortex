# api/src/cortex_api/service/questions/model/question.py
from __future__ import annotations

from datetime import date, datetime

from sqlmodel import Field, SQLModel


class WeeklyQuestion(SQLModel, table=True):
    """Snapshot of one real AIGC Q&A unit readers engaged with (from Databricks)."""

    __tablename__ = "weekly_question"

    id: str = Field(primary_key=True, max_length=64)  # hash(question_title|publisher_name)
    question_title: str = Field(max_length=2048)
    publisher_name: str = Field(max_length=255)
    clicks: int = Field(default=0)
    last_event_date: date | None = Field(default=None)
    synced_at: datetime = Field(default_factory=datetime.utcnow)
