"""Brand profile DTOs.

The request is the persistable subset a caller PUTs. SP-1 does NOT import
cortex-brand-extract; mapping the SP-2 `BrandProfile` extraction type to
`UpsertProfileRequest` is SP-3's `HttpOnboardingApi` projection job.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from cortex_api.service.brand.model.analysis_job import BrandProfileAnalysisJob
from cortex_api.service.brand.model.profile import BrandProfile


class ProductDTO(BaseModel):
    name: str
    category: str | None = None
    url: str | None = None
    confidence: int = 0


class CompetitorDTO(BaseModel):
    name: str
    domain: str | None = None
    match_score: int = 0


class VoiceSampleDTO(BaseModel):
    src: str
    text: str


class MediaMatchDTO(BaseModel):
    outlet_id: str
    name: str
    relevance: int = 0


class CategoryDTO(BaseModel):
    value: str | None = None
    confidence: int | None = None
    alternatives: list[str] = Field(default_factory=list)


class UpsertProfileRequest(BaseModel):
    """Body for `PUT /v1/brand/{brand_id}/profile`. Only `name` is required."""

    name: str = Field(min_length=1, max_length=255)
    legal_name: str | None = None
    tagline: str | None = None
    monogram: str | None = None
    brand_color: str | None = None
    founded: str | None = None
    about: str | None = None
    source_url: str | None = None
    industry_vertical: str | None = None
    primary_jurisdiction: str | None = None
    category: CategoryDTO | None = None
    region: list[str] = Field(default_factory=list)
    voice_samples: list[VoiceSampleDTO] = Field(default_factory=list)
    products: list[ProductDTO] = Field(default_factory=list)
    competitors: list[CompetitorDTO] = Field(default_factory=list)
    media_matches: list[MediaMatchDTO] = Field(default_factory=list)
    extraction_meta: dict[str, Any] | None = None

    def to_model(self, brand_id: UUID) -> BrandProfile:
        cat = self.category
        return BrandProfile(
            brand_id=brand_id,
            name=self.name,
            legal_name=self.legal_name,
            tagline=self.tagline,
            monogram=self.monogram,
            brand_color=self.brand_color,
            founded=self.founded,
            about=self.about,
            source_url=self.source_url,
            industry_vertical=self.industry_vertical,
            primary_jurisdiction=self.primary_jurisdiction,
            category_value=cat.value if cat else None,
            category_confidence=cat.confidence if cat else None,
            category_alternatives=cat.alternatives if cat else [],
            region=list(self.region),
            voice_samples=[v.model_dump() for v in self.voice_samples],
            products=[p.model_dump() for p in self.products],
            competitors=[c.model_dump() for c in self.competitors],
            media_matches=[m.model_dump() for m in self.media_matches],
            extraction_meta=self.extraction_meta,
        )


class BrandProfileResponse(BaseModel):
    brand_id: UUID
    name: str
    legal_name: str | None = None
    tagline: str | None = None
    monogram: str | None = None
    brand_color: str | None = None
    founded: str | None = None
    about: str | None = None
    source_url: str | None = None
    industry_vertical: str | None = None
    primary_jurisdiction: str | None = None
    category_value: str | None = None
    category_confidence: int | None = None
    category_alternatives: list[str] = Field(default_factory=list)
    region: list[str] = Field(default_factory=list)
    voice_samples: list[dict[str, Any]] = Field(default_factory=list)
    products: list[dict[str, Any]] = Field(default_factory=list)
    competitors: list[dict[str, Any]] = Field(default_factory=list)
    media_matches: list[dict[str, Any]] = Field(default_factory=list)
    extraction_meta: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, m: BrandProfile) -> BrandProfileResponse:
        return cls(
            brand_id=m.brand_id,
            name=m.name,
            legal_name=m.legal_name,
            tagline=m.tagline,
            monogram=m.monogram,
            brand_color=m.brand_color,
            founded=m.founded,
            about=m.about,
            source_url=m.source_url,
            industry_vertical=m.industry_vertical,
            primary_jurisdiction=m.primary_jurisdiction,
            category_value=m.category_value,
            category_confidence=m.category_confidence,
            category_alternatives=m.category_alternatives,
            region=m.region,
            voice_samples=m.voice_samples,
            products=m.products,
            competitors=m.competitors,
            media_matches=m.media_matches,
            extraction_meta=m.extraction_meta,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )


class AnalyzeRequest(BaseModel):
    """Body for POST /v1/brand/{brand_id}/profile/analyze."""

    url: str = Field(min_length=1, max_length=2048)


class AnalyzeJobDTO(BaseModel):
    """Analyze-job status; `profile` present only when succeeded."""

    job_id: UUID
    status: str
    error: str | None = None
    cost_usd: float | None = None
    profile: BrandProfileResponse | None = None

    @classmethod
    def from_model(
        cls,
        job: BrandProfileAnalysisJob,
        *,
        profile: BrandProfile | None,
    ) -> AnalyzeJobDTO:
        return cls(
            job_id=job.id,
            status=str(job.status),
            error=job.error,
            cost_usd=job.cost_usd,
            profile=BrandProfileResponse.from_model(profile) if profile else None,
        )
