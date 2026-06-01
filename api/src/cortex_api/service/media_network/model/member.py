# api/src/cortex_api/service/media_network/model/member.py
from __future__ import annotations

from datetime import datetime

from sqlmodel import Field, SQLModel


class MediaNetworkMember(SQLModel, table=True):
    """Snapshot of one real Mlytics network publisher (synced from Databricks)."""

    __tablename__ = "media_network_member"

    hostname: str = Field(primary_key=True, max_length=255)
    member_name: str = Field(max_length=255)
    customer_uuid: str | None = Field(default=None, max_length=64)
    wau: int | None = Field(default=None)
    category_hint: str | None = Field(default=None, max_length=128)
    synced_at: datetime = Field(default_factory=datetime.utcnow)
