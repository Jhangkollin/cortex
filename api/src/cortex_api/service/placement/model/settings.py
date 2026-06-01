"""BrandPlacementSettings — placement-specific settings, 1:1 with brand.

Row exists ⇔ brand is placement-ready (D1, locked 2026-05-21). The
columns marked nullable here are the transient mid-compose state: they
are filled post-compose by BrandPlacementComposer (COR-56) or the F5 seed
(COR-60). A future migration can tighten them to NOT NULL once stale
rows are reconciled.

**Compose-ready predicate (set by composer, COR-56):** ``composed_at IS
NOT NULL`` is the canonical "this row is placement-ready" check.
Consumers (eligible-brands API, analytics, debugging) should filter on
``composed_at IS NOT NULL`` rather than spelling out every required
column individually — this centralises the invariant so a new derivable
field doesn't silently break consumers.

``overrides_mask`` (D1) tracks which fields the user has explicitly
overridden so the composer's ``_apply_overrides`` step preserves them
across re-derivation (D2). Empty dict ⇒ no overrides yet. Keys are
column names; values are booleans. The composer is the only writer.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any
from uuid import UUID

from sqlalchemy import Column, Numeric, SmallInteger, text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from cortex_api.service.placement.model.status import PlacementRowStatus


class PlacementMode(StrEnum):
    """How a brand wants its content injected into a publisher page."""

    QUESTION_REPLACEMENT = "question_replacement"
    ANSWER_ONLY = "answer_only"
    BOTH = "both"


def _jsonb_dict_default() -> Any:
    return Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))


class BrandPlacementSettings(SQLModel, table=True):
    __tablename__ = "brand_placement_settings"

    brand_id: UUID = Field(foreign_key="brand.id", primary_key=True)

    use_dynamic_question: bool | None = Field(default=None)
    question_position: int | None = Field(
        default=None,
        sa_column=Column(SmallInteger, nullable=True),
    )
    ad_ratio: Decimal | None = Field(
        default=None,
        sa_column=Column(Numeric(3, 2), nullable=True),
    )
    mode: PlacementMode | None = Field(
        default=None,
        sa_column=Column(
            SAEnum(
                PlacementMode,
                values_callable=lambda enum_cls: [m.value for m in enum_cls],
                name="placementmode",
            ),
            nullable=True,
        ),
    )
    matching_rules: str | None = Field(default=None)
    matching_keywords: list[str] | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
    )
    matching_categories: list[str] | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
    )
    brand_answer_prompt: str | None = Field(default=None)
    brand_question_prompt: str | None = Field(default=None)
    brand_cta_text: str | None = Field(default=None)
    brand_cta_url: str | None = Field(default=None)

    status: PlacementRowStatus = Field(
        default=PlacementRowStatus.ACTIVE,
        sa_column=Column(
            SAEnum(
                PlacementRowStatus,
                values_callable=lambda enum_cls: [m.value for m in enum_cls],
                name="placementrowstatus",
                create_type=False,
            ),
            nullable=False,
            server_default=PlacementRowStatus.ACTIVE.value,
        ),
    )

    overrides_mask: dict[str, bool] = Field(
        default_factory=dict,
        sa_column=_jsonb_dict_default(),
    )

    # Set by BrandPlacementComposer (COR-56) when a successful derivation
    # completes. Consumers should filter ``composed_at IS NOT NULL`` to
    # mean "this row is placement-ready" — centralises the invariant
    # instead of spelling out every required column in each consumer.
    composed_at: datetime | None = Field(default=None)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow},
    )

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        if self.question_position is not None and self.question_position < 1:
            raise ValueError("question_position must be >= 1 (1-indexed)")
