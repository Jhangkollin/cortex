"""Brand identity DTOs — brand metadata + membership management."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from cortex_api.service.brand_identity.model.brand_role import BrandRole


class BrandResponse(BaseModel):
    id: UUID
    display_name: str
    industry: str | None = None
    domain: str | None = None
    created_at: datetime


class CreateBrandRequest(BaseModel):
    """Body for `POST /v1/brand` (self-serve brand creation).

    `display_name` is optional — when omitted, the route derives it from
    the caller's JWT display_name (`"{name}'s brand"`).
    """

    display_name: str | None = Field(default=None, min_length=1, max_length=255)


class CreateBrandResponse(BaseModel):
    """Returned by `POST /v1/brand` — brand + caller's resolved active context.

    Frontend uses `role` + `capabilities` to immediately call
    `session.update({kind:"brand", id:brand.id})` so the next request
    carries the new JWT claim. The active-context bake-in happens via
    `/v1/auth/resolve-context` (called by NextAuth's jwt callback) —
    these fields here let the frontend skip that round-trip on the
    immediate-after-create navigation.
    """

    brand: BrandResponse
    role: BrandRole
    capabilities: list[str]


class UpdateBrandRequest(BaseModel):
    """Body for `PATCH /v1/brand/{brand_id}` — partial update."""

    display_name: str | None = Field(default=None, min_length=1, max_length=255)
    industry: str | None = Field(default=None, max_length=128)
    domain: str | None = Field(default=None, max_length=255)


class BrandMemberRow(BaseModel):
    user_id: UUID
    email: EmailStr
    display_name: str | None = None
    role: BrandRole
    created_at: datetime


class BrandMembersResponse(BaseModel):
    rows: list[BrandMemberRow]


class GrantBrandMembershipRequest(BaseModel):
    invitee_email: EmailStr
    role: BrandRole


class OnboardingStatusResponse(BaseModel):
    onboarded: bool


class OnboardingCompleteResponse(BaseModel):
    onboarded_at: datetime


class BrandListItem(BaseModel):
    id: UUID
    display_name: str
    domain: str | None = None
    role: BrandRole
    onboarded_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class BrandListResponse(BaseModel):
    brands: list[BrandListItem]
