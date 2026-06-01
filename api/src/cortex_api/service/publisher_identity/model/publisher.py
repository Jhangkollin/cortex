"""Publisher SQLModel — Active Record entity.

`id` (UUID v7) is the universal scoping key — same value used as
`publisher_uuid` in Databricks WHERE clauses against publisher-side gold
tables.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlmodel import Field, SQLModel

from cortex_api.core.identifiers import uuid7


class Publisher(SQLModel, table=True):
    """Publisher tenant — owns memberships and analytical scope on the publisher side."""

    __tablename__ = "publisher"

    id: UUID = Field(default_factory=uuid7, primary_key=True)
    display_name: str = Field(max_length=255)
    primary_domain: str | None = Field(default=None, max_length=255)
    traffic_tier: str | None = Field(default=None, max_length=32, description="tier1/tier2/...")
    archived_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
