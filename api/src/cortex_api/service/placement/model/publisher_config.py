"""PublisherPlacementConfig — publisher-level placement knobs.

**MVP status (2026-05-21 / coordinator D7):** future scaffold, NOT read
at MVP. PHP retains the source of truth for ``brand_match_global_ratio``
via the request payload: ``MyAPI::get_question`` ships the publisher's
ratio with each call, and ``agent-ws`` coin-flips on it before forking
the placement subgraph (COR-64). This avoids a redundant cortex round
trip when the dice say skip, and matches the broader MVP rule that PHP
keeps publisher state until cortex absorbs publisher onboarding.

This table becomes the canonical source when publisher onboarding moves
from PHP to Cortex (post-MVP). Until then, rows here are not produced
and not consumed.

1:1 with publisher. No FK on ``publisher_id`` (publisher onboarding
still owned by PHP).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Column, Numeric
from sqlmodel import Field, SQLModel


class PublisherPlacementConfig(SQLModel, table=True):
    __tablename__ = "publisher_placement_config"

    publisher_id: UUID = Field(primary_key=True)

    global_match_ratio: Decimal | None = Field(
        default=None,
        sa_column=Column(Numeric(3, 2), nullable=True),
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow},
    )
