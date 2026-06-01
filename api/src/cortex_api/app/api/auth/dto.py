"""Auth DTOs — shape of the /v1/auth/me and /v1/auth/resolve-context payloads.

Pattern B JWT — cortex-api does NOT mint JWTs. NextAuth signs the session
token; cortex-api only enriches it (via callback at sign-in) and resolves
capabilities on demand. So this module exposes a `ResolveContextResponse`
shape (role + capabilities for a given membership) rather than an
`access_token`-bearing switch endpoint.
"""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr


class MembershipSummary(BaseModel):
    """One membership in the user's list (brand or publisher)."""

    kind: Literal["brand", "publisher"]
    id: UUID
    display_name: str
    role: str  # BrandRole or PublisherRole as string


class ActiveContextResponse(BaseModel):
    """The user's currently active context (from JWT claims)."""

    kind: Literal["brand", "publisher"]
    id: UUID
    role: str
    capabilities: list[str]


class MeResponse(BaseModel):
    """Whoami payload — calling user + active context + all memberships.

    `active_context` is null when the caller has no memberships yet (new
    user on first sign-in, persona-picker path).
    """

    user_id: UUID
    email: EmailStr
    display_name: str | None = None
    active_context: ActiveContextResponse | None = None
    memberships: list[MembershipSummary]


class ResolveContextRequest(BaseModel):
    """Body for /v1/auth/resolve-context.

    Caller asks: "for this user + this membership, what role and capabilities?"
    cortex-api verifies membership exists and returns the resolved set so
    NextAuth's jwt callback can bake it into the next session JWT.
    """

    kind: Literal["brand", "publisher"]
    id: UUID
