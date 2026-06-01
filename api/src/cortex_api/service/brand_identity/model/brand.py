"""Brand SQLModel — Active Record entity.

`id` (UUID v7) is the universal scoping key — same value used as `brand_uuid`
in Databricks WHERE clauses against gold tables.

No `slug` field at MVP. URL handle is the UUID itself. Display name lives
separately because it changes more freely (marketing rename, typo fix).
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlmodel import Field, SQLModel

from cortex_api.core.identifiers import uuid7


class Brand(SQLModel, table=True):
    """Brand tenant — owns memberships and analytical scope on the brand side."""

    __tablename__ = "brand"

    id: UUID = Field(default_factory=uuid7, primary_key=True)
    display_name: str = Field(max_length=255)
    industry: str | None = Field(default=None, max_length=128)
    domain: str | None = Field(default=None, max_length=255, description="Brand's primary web domain")
    archived_at: datetime | None = Field(default=None)
    onboarded_at: datetime | None = Field(
        default=None,
        description="Set once the brand finishes onboarding (manual or AI); NULL = not onboarded",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow},
    )
