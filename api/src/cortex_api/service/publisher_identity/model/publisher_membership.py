"""PublisherMembership SQLModel — N-to-N AppUser ↔ Publisher with role."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlmodel import Field, SQLModel, UniqueConstraint

from cortex_api.core.identifiers import uuid7
from cortex_api.service.publisher_identity.model.publisher_role import PublisherRole


class PublisherMembership(SQLModel, table=True):
    """Membership row binding an AppUser to a Publisher with a role."""

    __tablename__ = "publisher_membership"
    __table_args__ = (UniqueConstraint("user_id", "publisher_id", name="uq_publisher_membership_user_publisher"),)

    id: UUID = Field(default_factory=uuid7, primary_key=True)
    user_id: UUID = Field(foreign_key="app_user.id", index=True)
    publisher_id: UUID = Field(foreign_key="publisher.id", index=True)
    role: PublisherRole = Field(default=PublisherRole.VIEWER)
    invited_by: UUID | None = Field(default=None, foreign_key="app_user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
