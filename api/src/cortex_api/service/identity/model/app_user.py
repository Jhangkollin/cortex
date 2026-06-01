"""AppUser SQLModel — one row per OAuth subject (Active Record).

Shared identity across brand/publisher contexts. A single user can hold
memberships in many brands AND many publishers.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlmodel import Field, SQLModel

from cortex_api.core.identifiers import uuid7


class AppUser(SQLModel, table=True):
    """Mlytics-internal user identity (Google OAuth subject)."""

    __tablename__ = "app_user"

    id: UUID = Field(default_factory=uuid7, primary_key=True)
    oauth_subject: str = Field(unique=True, index=True, max_length=255, description="Google `sub` claim")
    email: str = Field(index=True, max_length=255)
    display_name: str | None = Field(default=None, max_length=255)
    avatar_url: str | None = Field(default=None, max_length=512)
    last_login_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow},
    )
