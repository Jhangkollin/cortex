"""Publisher identity DTOs — publisher metadata + membership management."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr

from cortex_api.service.publisher_identity.model.publisher_role import PublisherRole


class PublisherResponse(BaseModel):
    id: UUID
    display_name: str
    primary_domain: str | None = None
    traffic_tier: str | None = None
    created_at: datetime


class PublisherMemberRow(BaseModel):
    user_id: UUID
    email: EmailStr
    display_name: str | None = None
    role: PublisherRole
    created_at: datetime


class PublisherMembersResponse(BaseModel):
    rows: list[PublisherMemberRow]


class GrantPublisherMembershipRequest(BaseModel):
    invitee_email: EmailStr
    role: PublisherRole
