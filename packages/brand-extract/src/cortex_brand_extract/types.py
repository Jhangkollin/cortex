"""Frozen value objects for extraction output.

Field names align with the web `ExtractedBrand` TS type
(web/src/components/onboarding-v2/data.ts) where they overlap, so the wizard
consumes results with minimal translation. `media_matches` is a deliberate
aggregation extension (the wizard's media network is a separate dataset), and
UI-only counts such as `productMoreCount` are derived at the API projection
layer, not stored here.

These are NOT SQLModel — persistence mapping is SP-1.

Note: `model_config = frozen=True` blocks attribute reassignment but does NOT
deep-freeze list fields; treat list contents as read-only by convention — do
not mutate them in place.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ExtractTier = Literal["lite", "deep"]
ProviderKind = Literal["claude", "openai_compat"]


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True)


class ProviderConfig(_Frozen):
    kind: ProviderKind
    api_key: str
    model: str
    base_url: str | None = None


class MediaOutlet(_Frozen):
    """Caller-supplied media catalog entry (input to media match)."""

    outlet_id: str
    name: str
    audience: str | None = None
    topics: list[str] = Field(default_factory=list)


class CompetitorCandidate(_Frozen):
    """Caller-supplied competitor candidate (input to competitor match)."""

    name: str
    domain: str | None = None


class Category(_Frozen):
    value: str
    confidence: int = Field(ge=0, le=100)
    alternatives: list[str] = Field(default_factory=list)


class VoiceSample(_Frozen):
    src: str
    text: str


class Product(_Frozen):
    name: str
    category: str
    url: str | None = None
    confidence: int = Field(default=0, ge=0, le=100)


class Competitor(_Frozen):
    name: str
    domain: str | None = None
    match_score: int = Field(default=0, ge=0, le=100)


class MediaMatch(_Frozen):
    outlet_id: str
    name: str
    relevance: int = Field(default=0, ge=0, le=100)


class ExtractionMeta(_Frozen):
    tier: ExtractTier
    model: str = Field(
        description="resolved model identifier actually used, e.g. 'claude-sonnet-4-6'"
    )
    cost_usd: float = 0.0
    js_detected: bool = False
    warnings: list[str] = Field(default_factory=list)
    extracted_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class BrandProfile(_Frozen):
    url: str = Field(description="bare hostname or full URL of the brand site")
    name: str
    legal_name: str | None = None
    tagline: str | None = None
    monogram: str | None = None
    brand_color: str | None = None
    category: Category
    region: list[str] = Field(default_factory=list)
    founded: str | None = None
    about: str | None = None
    voice_samples: list[VoiceSample] = Field(default_factory=list)
    products: list[Product] = Field(default_factory=list)
    competitors: list[Competitor] = Field(default_factory=list)
    media_matches: list[MediaMatch] = Field(default_factory=list)
    extraction_meta: ExtractionMeta
