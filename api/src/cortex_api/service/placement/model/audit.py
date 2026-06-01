"""PlacementAudit — append-only audit row per placement decision.

Replaces aigc-mvp's ``brand_injection_audits`` for the new path. Logs
the winner of the multi-brand selection plus every losing candidate (R2
audit: ``selection_weight = confidence × ad_ratio``). ``trace_id`` +
``parent_trace_id`` stitch the row back to MLflow + Loki (R4).

No FK on ``brand_id`` / ``publisher_id`` by design: the audit row
outlives soft-deletes so historical decisions stay queryable. No
``updated_at``: this is append-only.

**Trace ID contract.** Placement is always invoked from a parent trace
(the router agent that forks the subgraph, per R4 + AD7), so both
``trace_id`` and ``parent_trace_id`` are required (NOT NULL). The
``max_length=64`` ceiling covers MLflow run-id (32 hex), W3C traceparent
(55 chars), and Mlytics' internal trace formats with room to spare.

**Document shape for ``losing_candidates``** (locked here for the
schema; the typed write-side VO lives with the composer/router in
COR-56 / COR-62): each entry is
``{"brand_id": str, "confidence": float, "ad_ratio": float, "weight":
float}``.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import Column, Numeric, SmallInteger, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from cortex_api.core.identifiers import uuid7


def _jsonb_list_default() -> Any:
    return Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))


class PlacementAudit(SQLModel, table=True):
    __tablename__ = "placement_audit"

    id: UUID = Field(default_factory=uuid7, primary_key=True)

    brand_id: UUID
    publisher_id: UUID

    article_url: str
    article_url_hash: str = Field(max_length=64)

    question_text: str
    answer_text: str
    placement_position: int = Field(sa_column=Column(SmallInteger, nullable=False))
    rationale: str

    selection_weight: Decimal = Field(
        sa_column=Column(Numeric(5, 4), nullable=False),
    )
    losing_candidates: list[dict[str, Any]] = Field(
        default_factory=list,
        sa_column=_jsonb_list_default(),
    )

    trace_id: str = Field(max_length=64)
    parent_trace_id: str = Field(max_length=64)

    created_at: datetime = Field(default_factory=datetime.utcnow)
