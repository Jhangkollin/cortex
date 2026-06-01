"""DTOs for the F2b placement-claims API (COR-75)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from cortex_api.app.api.eligible_brands.dto import EligibleBrandDTO


class ClaimRequest(BaseModel):
    article_url: str
    agent_ws_request_id: str


class ClaimResponse(BaseModel):
    winner: bool
    claim_id: UUID
    expires_at: datetime
    eligible_brands: list[EligibleBrandDTO]


class DeleteClaimResponse(BaseModel):
    deleted: bool


# ``Literal`` validates at the Pydantic boundary so garbage input returns
# 422 (not a deferred ValueError that bubbles to 500). Mirrors the valid
# transitions out of in_flight; never accepts in_flight back from a client.
class CompleteRequest(BaseModel):
    status: Literal["done", "failed"]
    placement_audit_id: UUID | None = None
