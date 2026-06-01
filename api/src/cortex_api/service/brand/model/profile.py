"""BrandProfile SQLModel — the brand's current extracted profile.

Hybrid shape: queryable identity fields are real columns; list/nested
snapshot data is JSONB so it evolves with the extraction engine without
migrations.

Keyed by `brand_id` (UUID v7) — the universal brand scoping key, same value
as `brand.id`. Forward-compat invariant: `brand_id` equals the future
`org.id` if/when identity converges on Org/OrgMembership; nothing here
assumes a per-persona identity table. One row per brand (PK = brand_id);
PUT upserts. `extraction_meta.extracted_at` is retained so a future
versioned-history table is a clean migration, not a redesign.

OLTP write-side (Postgres) — NOT a Databricks read model.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Column, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


def _jsonb_list() -> Any:
    return Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))


class BrandProfile(SQLModel, table=True):
    """A brand's current extracted profile (one row per brand)."""

    __tablename__ = "brand_profile"

    brand_id: UUID = Field(foreign_key="brand.id", primary_key=True)

    name: str = Field(max_length=255)
    legal_name: str | None = Field(default=None, max_length=255)
    tagline: str | None = Field(default=None, max_length=512)
    monogram: str | None = Field(default=None, max_length=8)
    brand_color: str | None = Field(default=None, max_length=32)
    founded: str | None = Field(default=None, max_length=32)
    about: str | None = Field(default=None)
    source_url: str | None = Field(default=None, max_length=2048)
    industry_vertical: str | None = Field(default=None, max_length=128)
    primary_jurisdiction: str | None = Field(default=None, max_length=8)
    category_value: str | None = Field(default=None, max_length=255)
    category_confidence: int | None = Field(default=None)

    category_alternatives: list[str] = Field(default_factory=list, sa_column=_jsonb_list())
    topics: list[str] = Field(default_factory=list, sa_column=_jsonb_list())
    region: list[str] = Field(default_factory=list, sa_column=_jsonb_list())
    voice_samples: list[dict[str, Any]] = Field(default_factory=list, sa_column=_jsonb_list())
    products: list[dict[str, Any]] = Field(default_factory=list, sa_column=_jsonb_list())
    competitors: list[dict[str, Any]] = Field(default_factory=list, sa_column=_jsonb_list())
    media_matches: list[dict[str, Any]] = Field(default_factory=list, sa_column=_jsonb_list())
    extraction_meta: dict[str, Any] | None = Field(default=None, sa_column=Column(JSONB, nullable=True))

    created_at: datetime = Field(default_factory=datetime.utcnow)
    # INVARIANT: updated_at MUST be DB-clocked (sa.func.now()) on every write.
    # The profile-derived caches (brand_weekly_questions / brand_voice /
    # brand_media_network) compare their own DB-clocked updated_at against THIS
    # column to decide staleness on re-onboard; a Python-clock value here would
    # drift relative to those and mis-trigger (or miss) regeneration. The sole
    # writer, BrandProfileRepo.upsert, sets updated_at = sa.func.now() to honor
    # this. The default_factory / onupdate below are app-clock fallbacks kept
    # for type-checker + unit-test ergonomics ONLY — any NEW write path must
    # set sa.func.now() explicitly (PG has no native ON UPDATE to enforce it).
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow},
    )
