"""ORM mapping for placement_compute_claim (AD8 / COR-75).

PK is ``(publisher_id, article_url_hash)``. The repo layer
(``PlacementClaimRepo``) owns the UPSERT-with-WHERE single-flight logic;
this module is purely the SQLModel shape.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Column, LargeBinary, Text, func, text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, SQLModel


class PlacementClaimStatus(StrEnum):
    IN_FLIGHT = "in_flight"
    DONE = "done"
    FAILED = "failed"


class PlacementComputeClaim(SQLModel, table=True):
    __tablename__ = "placement_compute_claim"

    publisher_id: UUID = Field(sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, nullable=False))
    article_url_hash: bytes = Field(sa_column=Column(LargeBinary, primary_key=True, nullable=False))
    claim_id: UUID = Field(sa_column=Column(PG_UUID(as_uuid=True), nullable=False))
    agent_ws_request_id: str = Field(sa_column=Column(Text, nullable=False))
    brand_ids: list[UUID] = Field(sa_column=Column(ARRAY(PG_UUID(as_uuid=True)), nullable=False))
    claimed_at: datetime = Field(sa_column=Column(nullable=False, server_default=text("NOW()")))
    expires_at: datetime = Field(nullable=False)
    completed_at: datetime | None = Field(default=None, nullable=True)
    placement_audit_id: UUID | None = Field(
        default=None,
        sa_column=Column(PG_UUID(as_uuid=True), nullable=True),
    )
    status: PlacementClaimStatus = Field(
        default=PlacementClaimStatus.IN_FLIGHT,
        sa_column=Column(
            SAEnum(
                PlacementClaimStatus,
                values_callable=lambda enum_cls: [m.value for m in enum_cls],
                name="placement_claim_status",
            ),
            nullable=False,
            server_default=PlacementClaimStatus.IN_FLIGHT.value,
        ),
    )
    created_at: datetime = Field(sa_column=Column(nullable=False, server_default=text("NOW()")))
    # ``onupdate=func.now()`` covers the ORM-update path. The repo uses raw
    # ``text()`` SQL which bypasses this hook, so the UPDATE branches in
    # PlacementClaimRepo also set ``updated_at = NOW()`` explicitly.
    # Per CLAUDE.md hard-won rule #1.
    updated_at: datetime = Field(sa_column=Column(nullable=False, server_default=text("NOW()"), onupdate=func.now()))
