"""BrandMembership SQLModel — N-to-N AppUser ↔ Brand with role."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import Column, ForeignKey
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel, UniqueConstraint

from cortex_api.core.identifiers import uuid7
from cortex_api.service.brand_identity.model.brand_role import BrandRole


class BrandMembership(SQLModel, table=True):
    """Membership row binding an AppUser to a Brand with a role."""

    __tablename__ = "brand_membership"
    __table_args__ = (UniqueConstraint("user_id", "brand_id", name="uq_brand_membership_user_brand"),)

    id: UUID = Field(default_factory=uuid7, primary_key=True)
    user_id: UUID = Field(foreign_key="app_user.id", index=True)
    brand_id: UUID = Field(foreign_key="brand.id", index=True)
    role: BrandRole = Field(
        default=BrandRole.VIEWER,
        sa_column=Column(
            SAEnum(
                BrandRole,
                values_callable=lambda enum_cls: [m.value for m in enum_cls],
                name="brandrole",
            ),
            nullable=False,
        ),
    )
    invited_by: UUID | None = Field(
        default=None,
        sa_column=Column(
            sa.Uuid,
            ForeignKey("app_user.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow},
    )
