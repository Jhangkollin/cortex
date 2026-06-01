"""Frozen Pydantic contract mirroring brand-report/data.jsx `BRAND_IQ`.

Public read contract consumed by PDF (COR-80), viewer (COR-81), dashboard
(COR-82/83). Field names are camelCase to match the prototype's JSON exactly.
Immutable: a report is a point-in-time snapshot, never mutated after compose.
"""
# ruff: noqa: N815  # camelCase field names are intentional — mirror BRAND_IQ JSON keys

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

INSUFFICIENT_DATA = "資料不足"


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class ReportMeta(_Frozen):
    subject: str
    enName: str
    legalName: str | None
    domain: str | None
    primaryMarket: str | None
    extendedMarkets: list[str]
    reportDate: str
    windowFrom: str
    windowTo: str
    monogram: str | None
    brandColor: str | None
    tagline: str | None
    founded: str | None
    category: str | None
    confidence: int
    reportId: str
    pageCount: int
    preparedFor: str
    preparedBy: str


class CoreItem(_Frozen):
    item: str
    body: str
    certainty: str


class ProductLine(_Frozen):
    line: str
    thesis: str
    examples: str
    signal: str
    confidence: int


class SubBrand(_Frozen):
    type: str
    name: str
    note: str


class SectionStatusBody(_Frozen):
    status: str
    body: str


class MediaOutlet(_Frozen):
    name: str
    audience: str
    weekly: str
    relevance: int
    topics: str
    trend: str


class CompetitorTier(_Frozen):
    tier: str
    brands: str
    basis: str
    position: str


class Insights(_Frozen):
    confirmed: list[str]
    inferences: list[str]
    hypotheses: list[str]


class FaqItem(_Frozen):
    q: str
    a: str
    source: str
    level: str


class Channel(_Frozen):
    type: str
    surfaces: str
    read: str


class Risk(_Frozen):
    theme: str
    trigger: str
    where: str
    note: str
    level: str
    action: str


class Sources(_Frozen):
    A: list[str]
    B: list[str]
    C: list[str]


class Quality(_Frozen):
    high: str
    midLow: str
    gaps: str
    conflicts: str
    open: str


class ReportDTO(_Frozen):
    meta: ReportMeta
    core: list[CoreItem]
    coreJudgement: str
    productLines: list[ProductLine]
    productNote: str
    subBrands: list[SubBrand]
    endorsements: SectionStatusBody
    ipCollabs: SectionStatusBody
    mediaNetwork: list[MediaOutlet]
    competitors: list[CompetitorTier]
    competitorNote: str
    insights: Insights
    faq: list[FaqItem]
    channels: list[Channel]
    risks: list[Risk]
    sources: Sources
    quality: Quality
