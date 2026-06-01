"""Orchestrator. Wires the stages, emits progress, isolates per-stage
failures into warnings, and accumulates cost into extraction_meta.
"""

from __future__ import annotations

from cortex_brand_extract.corpus import build_corpus
from cortex_brand_extract.crawl import select_pages
from cortex_brand_extract.fetch.deep import fetch_deep
from cortex_brand_extract.fetch.detect import looks_js_rendered
from cortex_brand_extract.fetch.lite import fetch_lite
from cortex_brand_extract.llm.base import LLMProvider
from cortex_brand_extract.match.competitors import rank_competitors
from cortex_brand_extract.match.media import rank_media
from cortex_brand_extract.parse import parse_site
from cortex_brand_extract.progress import ProgressEvent, ProgressSink, emit
from cortex_brand_extract.synthesize import synthesize_profile
from cortex_brand_extract.types import (
    BrandProfile,
    CompetitorCandidate,
    ExtractionMeta,
    ExtractTier,
    MediaOutlet,
)


async def _fetch(url: str, tier: ExtractTier) -> tuple[str, str, str]:
    page = await fetch_deep(url) if tier == "deep" else await fetch_lite(url)
    return page.final_url, page.html, ("" if page.status == 200 else f"status {page.status}")


async def extract_brand_profile(
    url: str,
    *,
    tier: ExtractTier = "lite",
    provider: LLMProvider,
    max_pages: int = 12,
    competitor_candidates: list[CompetitorCandidate] | None = None,
    seed_media_catalog: list[MediaOutlet] | None = None,
    progress: ProgressSink | None = None,
    max_corpus_chars: int = 60_000,
) -> BrandProfile:
    warnings: list[str] = []
    cost = 0.0

    await emit(progress, ProgressEvent(stage="fetch", status="running", detail=url))
    home_url, home_html, fetch_warn = await _fetch(url, tier)
    if fetch_warn:
        warnings.append(f"homepage fetch: {fetch_warn}")
    js_detected, why = looks_js_rendered(home_html)
    if js_detected and tier == "lite":
        warnings.append(f"site looks JS-rendered ({why}); deep tier recommended")
    await emit(progress, ProgressEvent(stage="fetch", status="ok", detail=home_url))

    await emit(progress, ProgressEvent(stage="parse", status="running"))
    meta = parse_site(home_url, home_html)
    await emit(progress, ProgressEvent(stage="parse", status="ok", detail=meta.title))

    await emit(progress, ProgressEvent(stage="crawl", status="running"))
    chosen = select_pages(home_url, meta.internal_links, max_pages=max_pages)
    pages: list[tuple[str, str]] = [(home_url, meta.visible_text)]
    for link in chosen[1:]:
        _, html, warn = await _fetch(link, tier)
        if warn:
            warnings.append(f"{link}: {warn}")
            continue
        pages.append((link, parse_site(link, html).visible_text))
    await emit(progress, ProgressEvent(stage="crawl", status="ok", detail=f"{len(pages)} pages"))

    await emit(progress, ProgressEvent(stage="corpus", status="running"))
    corpus = build_corpus(pages, max_chars=max_corpus_chars)
    if corpus.truncated:
        warnings.append("corpus truncated to char budget")
    await emit(progress, ProgressEvent(stage="corpus", status="ok"))

    await emit(progress, ProgressEvent(stage="synthesize", status="running"))
    core = await synthesize_profile(provider, meta, corpus)
    cost += core.cost_usd
    await emit(progress, ProgressEvent(stage="synthesize", status="ok", detail=core.name))

    await emit(progress, ProgressEvent(stage="competitors", status="running"))
    competitors, comp_warn, comp_cost = await rank_competitors(
        provider,
        brand_name=core.name,
        category=core.category.value,
        candidates=competitor_candidates or [],
    )
    if comp_warn:
        warnings.append(comp_warn)
    cost += comp_cost
    await emit(progress, ProgressEvent(stage="competitors", status="ok"))

    await emit(progress, ProgressEvent(stage="media", status="running"))
    media, media_warn, media_cost = await rank_media(
        provider,
        brand_name=core.name,
        category=core.category.value,
        catalog=seed_media_catalog or [],
    )
    if media_warn:
        warnings.append(media_warn)
    cost += media_cost
    await emit(progress, ProgressEvent(stage="media", status="ok"))

    await emit(progress, ProgressEvent(stage="done", status="ok"))
    return BrandProfile(
        url=home_url,
        name=core.name,
        legal_name=core.legal_name or meta.jsonld_org_name,
        tagline=core.tagline,
        monogram=core.monogram,
        brand_color=core.brand_color or meta.theme_color,
        category=core.category,
        region=core.region,
        founded=core.founded or meta.founded,
        about=core.about,
        voice_samples=core.voice_samples,
        products=core.products,
        competitors=competitors,
        media_matches=media,
        extraction_meta=ExtractionMeta(
            tier=tier,
            model=provider.model,
            cost_usd=round(cost, 6),
            js_detected=js_detected,
            warnings=warnings,
        ),
    )
