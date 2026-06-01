"""Pure section builders and deterministic compose_live function.

No LLM calls happen here — all logic is deterministic and synchronous.
"""
# ruff: noqa: N815  # camelCase field names mirror the contract

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

from cortex_api.service.brand_report.contract import (
    INSUFFICIENT_DATA,
    Channel,
    CompetitorTier,
    CoreItem,
    FaqItem,
    Insights,
    MediaOutlet,
    ProductLine,
    Quality,
    ReportDTO,
    ReportMeta,
    SectionStatusBody,
    Sources,
    SubBrand,
)


@dataclass
class ReportSources:
    """Plain-dict inputs passed from the service layer."""

    profile: dict[str, Any]
    outlets: list[dict[str, Any]] = field(default_factory=list)
    questions: list[dict[str, Any]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def code(name: str | None) -> str:
    """Derive a short uppercase alphanum slug for use in reportId.

    The service layer (Task 6) always supplies an explicit ``report_id``, so the
    "BRAND" fallback for fully non-Latin names is a last resort only.
    """
    return re.sub(r"[^A-Za-z0-9]", "", name or "").upper()[:6] or "BRAND"


def _certainty(conf: int | None) -> str:
    """Map a confidence int to a certainty label."""
    if conf is None or conf < 70:
        return INSUFFICIENT_DATA
    if conf >= 90:
        return "已確認"
    return "高可能"


def _weekly(wau: int | None) -> str:
    """Format weekly-active-user count as human-readable string."""
    if not wau or wau < 0:
        return "0"
    if wau >= 1_000_000:
        return f"{wau / 1_000_000:.1f}M"
    if wau >= 1_000:
        return f"{wau // 1_000}K"
    return str(wau)


def _domain(profile: dict[str, Any]) -> str | None:
    """Resolve the brand's canonical domain: explicit ``domain`` else source URL."""
    return profile.get("domain") or profile.get("source_url")


def _faq_level(intent: str | None, score: int | None) -> str:
    """Derive FAQ importance level from intent/score signals."""
    raw_score = score or 0
    if intent == "high" or raw_score >= 80:
        return "A 級"
    return "B 級"


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------


def _build_meta(
    profile: dict[str, Any],
    *,
    domain: str | None,
    page_count: int,
    prepared_by: str,
    report_id: str | None,
    today: date,
) -> ReportMeta:
    name: str = profile.get("name") or ""
    region: list[str] = profile.get("region") or []
    raw_conf: int | None = profile.get("category_confidence")
    confidence: int = raw_conf or 0

    computed_id = report_id or f"BIQ-{today.isoformat()}-{code(name)}"
    window_from = (today - timedelta(days=365)).isoformat()
    window_to = today.isoformat()

    return ReportMeta(
        subject=name,
        enName=code(name),
        legalName=profile.get("legal_name"),
        domain=domain,
        primaryMarket=region[0] if region else None,
        extendedMarkets=region[1:],
        reportDate=today.isoformat(),
        windowFrom=window_from,
        windowTo=window_to,
        monogram=profile.get("monogram"),
        brandColor=profile.get("brand_color"),
        tagline=profile.get("tagline"),
        founded=profile.get("founded"),
        category=profile.get("category_value"),
        confidence=confidence,
        reportId=computed_id,
        pageCount=page_count,
        preparedFor="Brand Account",
        preparedBy=prepared_by,
    )


def _build_core(profile: dict[str, Any]) -> list[CoreItem]:
    conf: int | None = profile.get("category_confidence")
    certainty = _certainty(conf)

    name: str = profile.get("name") or ""
    legal_name: str | None = profile.get("legal_name")
    region: list[str] = profile.get("region") or []
    tagline: str | None = profile.get("tagline")
    about: str | None = profile.get("about")
    voice_samples: list[dict[str, Any]] = profile.get("voice_samples") or []

    voice_text = (voice_samples[0].get("text") or INSUFFICIENT_DATA) if voice_samples else INSUFFICIENT_DATA

    items: list[CoreItem] = [
        CoreItem(
            item="品牌主體",
            body=legal_name or name,
            certainty=certainty,
        ),
        CoreItem(
            item="主要市場",
            body="、".join(region) if region else INSUFFICIENT_DATA,
            certainty=certainty,
        ),
        CoreItem(
            item="品牌定位",
            body=tagline or about or INSUFFICIENT_DATA,
            certainty=certainty,
        ),
        CoreItem(
            item="Brand Voice",
            body=voice_text,
            certainty=certainty,
        ),
    ]
    return items


def _build_product_lines(profile: dict[str, Any]) -> list[ProductLine]:
    products: list[dict[str, Any]] = profile.get("products") or []
    lines: list[ProductLine] = []
    for p in products:
        lines.append(
            ProductLine(
                line=p.get("name") or "",
                thesis=p.get("category") or "",
                examples=p.get("url") or p.get("name") or "",
                signal="",
                confidence=int(p.get("confidence") or 0),
            )
        )
    return lines


def _build_sub_brands(profile: dict[str, Any]) -> list[SubBrand]:
    name: str = profile.get("name") or ""
    products: list[dict[str, Any]] = profile.get("products") or []

    rows: list[SubBrand] = [SubBrand(type="主品牌", name=name, note="")]

    # Product-series row, only when products exist.
    product_names = "、".join(p.get("name", "") for p in products if p.get("name"))
    if product_names:
        rows.append(SubBrand(type="產品線", name=product_names, note=""))

    rows.append(SubBrand(type="聯名 / IP", name="", note=INSUFFICIENT_DATA))
    return rows


def _build_media_network(outlets: list[dict[str, Any]]) -> list[MediaOutlet]:
    result: list[MediaOutlet] = []
    for o in outlets:
        topics: list[str] = o.get("topics") or []
        result.append(
            MediaOutlet(
                name=o.get("member_name") or "",
                audience=o.get("audience_descriptor") or "",
                weekly=_weekly(o.get("wau")),
                relevance=int(o.get("relevance") or 0),
                topics="、".join(topics),
                trend="持平",
            )
        )
    return result


def _build_competitors(profile: dict[str, Any]) -> list[CompetitorTier]:
    competitors: list[dict[str, Any]] = profile.get("competitors") or []
    if not competitors:
        return []
    names = [c.get("name") or "" for c in competitors]
    category: str = profile.get("category_value") or "同類品牌"
    return [
        CompetitorTier(
            tier="直接競品",
            brands="、".join(names),
            basis=f"同為{category}領域，依市場重疊度排序",
            position="",
        )
    ]


def _build_faq(questions: list[dict[str, Any]]) -> list[FaqItem]:
    result: list[FaqItem] = []
    for q in questions:
        result.append(
            FaqItem(
                q=q.get("text") or "",
                a=INSUFFICIENT_DATA,
                source=q.get("media") or "",
                level=_faq_level(q.get("intent"), q.get("score")),
            )
        )
    return result


def _build_channels(
    profile: dict[str, Any],
    outlets: list[dict[str, Any]],
    *,
    domain: str | None,
) -> list[Channel]:
    region: list[str] = profile.get("region") or []
    channels: list[Channel] = []

    # D2C / owned
    channels.append(
        Channel(
            type="D2C / 官網",
            surfaces=domain or INSUFFICIENT_DATA,
            read="官方資料來源",
        )
    )

    # Media-network row when outlets exist
    if outlets:
        outlet_surfaces = "、".join(o.get("member_name") or "" for o in outlets)
        channels.append(
            Channel(
                type="媒體通路",
                surfaces=outlet_surfaces,
                read="夥伴媒體資料",
            )
        )

    # Physical channel — unknown unless profile says otherwise
    channels.append(
        Channel(
            type="實體通路",
            surfaces=INSUFFICIENT_DATA,
            read=INSUFFICIENT_DATA,
        )
    )

    # Overseas
    overseas_markets = "、".join(region[1:]) if len(region) > 1 else INSUFFICIENT_DATA
    channels.append(
        Channel(
            type="海外市場",
            surfaces=overseas_markets,
            read=INSUFFICIENT_DATA,
        )
    )

    return channels


def _build_sources(
    profile: dict[str, Any],
    outlets: list[dict[str, Any]],
) -> Sources:
    source_url: str | None = profile.get("source_url")
    a_sources = [source_url] if source_url else []

    b_sources: list[str] = []
    for o in outlets:
        name = o.get("member_name") or ""
        if name:
            b_sources.append(f"媒體夥伴：{name}")
    competitors: list[dict[str, Any]] = profile.get("competitors") or []
    for c in competitors:
        name = c.get("name") or ""
        domain = c.get("domain") or ""
        if name:
            b_sources.append(f"競品參考：{name}" + (f"（{domain}）" if domain else ""))

    return Sources(
        A=a_sources,
        B=b_sources,
        C=["社群口碑僅作線索"],
    )


def _build_quality(profile: dict[str, Any]) -> Quality:
    meta: dict[str, Any] = profile.get("extraction_meta") or {}
    tier: str = meta.get("tier") or "unknown"
    model: str = meta.get("model") or "unknown"
    warnings: list[Any] = meta.get("warnings") or []

    high_note = f"官網資料已抽取（tier={tier}, model={model}）"
    mid_note = "部分欄位依賴推斷，信心度中等"
    gaps_note = "社群資料、廣告投放紀錄尚未涵蓋"
    conflicts_note = "警告：" + "；".join(str(w) for w in warnings) if warnings else "無明顯矛盾"
    open_note = "媒體觸及率與競品定位待 LLM 補充"

    return Quality(
        high=high_note,
        midLow=mid_note,
        gaps=gaps_note,
        conflicts=conflicts_note,
        open=open_note,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compose_live(
    sources: ReportSources,
    *,
    page_count: int,
    prepared_by: str,
    report_id: str | None = None,
) -> ReportDTO:
    """Map brand onboarding data into a ReportDTO.

    Deterministic / LIVE sections are populated from real data.
    LLM-backed fields (coreJudgement, productNote, competitorNote,
    insights, risks, faq.a) are left as honesty-marker placeholders.
    """
    profile = sources.profile
    outlets = sources.outlets
    questions = sources.questions
    today = date.today()
    domain = _domain(profile)

    return ReportDTO(
        meta=_build_meta(
            profile,
            domain=domain,
            page_count=page_count,
            prepared_by=prepared_by,
            report_id=report_id,
            today=today,
        ),
        core=_build_core(profile),
        coreJudgement="",
        productLines=_build_product_lines(profile),
        productNote="",
        subBrands=_build_sub_brands(profile),
        endorsements=SectionStatusBody(
            status=INSUFFICIENT_DATA,
            body="品牌代言人資料尚未收錄，待後續補充。",
        ),
        ipCollabs=SectionStatusBody(
            status=INSUFFICIENT_DATA,
            body="聯名 / IP 合作資料尚未收錄，待後續補充。",
        ),
        mediaNetwork=_build_media_network(outlets),
        competitors=_build_competitors(profile),
        competitorNote="",
        insights=Insights(confirmed=[], inferences=[], hypotheses=[]),
        faq=_build_faq(questions),
        channels=_build_channels(profile, outlets, domain=domain),
        risks=[],
        sources=_build_sources(profile, outlets),
        quality=_build_quality(profile),
    )
