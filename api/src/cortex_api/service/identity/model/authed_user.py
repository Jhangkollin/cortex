"""AuthedUser — frozen value object representing a verified caller.

Produced by `app/dependencies/auth.py::authenticated_user` after JWT decode.
Carries the user's identity AND the raw JWT claims so downstream deps
(`active_brand`, `active_publisher`) can extract context-specific fields.

NOT persisted — purely a per-request value object.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AuthedUser(BaseModel):
    """Verified caller identity post-JWT-decode."""

    model_config = ConfigDict(frozen=True)

    user_id: UUID
    email: str
    display_name: str | None = None
    raw_claims: dict[str, Any] = Field(default_factory=dict, repr=False)
