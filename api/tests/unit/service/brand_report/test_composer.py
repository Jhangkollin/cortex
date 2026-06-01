from __future__ import annotations

import pytest
from cortex_brand_extract.errors import UpstreamError
from cortex_brand_extract.llm.base import FakeProvider

from cortex_api.service.brand_report.composer import ReportSources, compose, compose_live
from cortex_api.service.brand_report.contract import INSUFFICIENT_DATA


def _profile(**over):
    base = dict(  # noqa: C408
        name="Acme Bank Asia",
        legal_name="Acme Holdings",
        tagline="Banking, redesigned.",
        monogram="A",
        brand_color="#225D59",
        founded="1998",
        about="An Asian bank.",
        source_url="https://acme.tw",
        category_value="數位銀行",
        category_confidence=96,
        region=["台灣", "香港"],
        voice_samples=[{"text": "We serve people."}],
        products=[{"name": "信用卡", "category": "海外回饋", "url": "/cards", "confidence": 98}],
        competitors=[{"name": "國泰世華", "domain": "cathay.tw", "match_score": 90}],
        extraction_meta={"tier": "lite", "model": "claude-opus-4-7", "warnings": []},
    )
    base.update(over)
    return base


def _sources(profile_over=None, outlets=None, questions=None) -> ReportSources:
    return ReportSources(
        profile=_profile(**(profile_over or {})),
        outlets=outlets
        if outlets is not None
        else [
            {
                "member_name": "MoneyDJ",
                "audience_descriptor": "投資人",
                "wau": 1_200_000,
                "relevance": 94,
                "topics": ["ETF"],
            }
        ],
        questions=questions
        if questions is not None
        else [{"text": "哪家手續費最低?", "media": "MoneyDJ", "intent": "high", "score": 88}],
    )


def test_live_sections_map_from_sources() -> None:
    dto = compose_live(_sources(), page_count=8, prepared_by="Cortex")
    assert dto.meta.subject == "Acme Bank Asia"
    assert dto.meta.reportId.startswith("BIQ-") and dto.meta.reportId.endswith("ACMEBA")
    assert dto.productLines[0].line == "信用卡"
    assert dto.mediaNetwork[0].name == "MoneyDJ"
    assert dto.competitors[0].brands == "國泰世華"
    assert dto.faq[0].q == "哪家手續費最低?" and dto.faq[0].source == "MoneyDJ"


def test_absent_sections_are_marked_insufficient() -> None:
    dto = compose_live(_sources(outlets=[], questions=[]), page_count=8, prepared_by="Cortex")
    assert dto.endorsements.status == INSUFFICIENT_DATA
    assert dto.ipCollabs.status == INSUFFICIENT_DATA
    assert dto.mediaNetwork == []
    assert dto.faq == []
    ip_row = next(sb for sb in dto.subBrands if sb.type == "聯名 / IP")
    assert ip_row.note == INSUFFICIENT_DATA


def test_low_confidence_downgrades_core_certainty() -> None:
    dto = compose_live(_sources(profile_over={"category_confidence": 50}), page_count=8, prepared_by="Cortex")
    assert any(c.certainty == INSUFFICIENT_DATA for c in dto.core)


def test_llm_fields_are_placeholders_in_live() -> None:
    dto = compose_live(_sources(), page_count=8, prepared_by="Cortex")
    assert dto.coreJudgement == "" and dto.productNote == "" and dto.competitorNote == ""
    assert dto.insights.confirmed == [] and dto.risks == []
    assert all(f.a == INSUFFICIENT_DATA for f in dto.faq)


@pytest.mark.asyncio
async def test_compose_fills_llm_sections_from_provider() -> None:
    provider = FakeProvider(
        [
            {
                "coreJudgement": "J",
                "productNote": "P",
                "competitorNote": "C",
                "insights": {"confirmed": ["a"], "inferences": ["b"], "hypotheses": ["c"]},
                "faqAnswers": ["每月前5筆免手續費。"],
            },
            {
                "risks": [
                    {
                        "theme": "績效宣稱",
                        "trigger": "優於市場",
                        "where": "Voice",
                        "note": "n",
                        "level": "高",
                        "action": "送法遵",
                    }
                ]
            },
        ]
    )
    dto, cost = await compose(_sources(), provider, page_count=8, prepared_by="Cortex")
    assert dto.insights.confirmed == ["a"]
    assert dto.coreJudgement == "J"
    assert dto.faq[0].a == "每月前5筆免手續費。"
    assert dto.risks[0].theme == "績效宣稱"
    assert cost == pytest.approx(0.002)


@pytest.mark.asyncio
async def test_compose_degrades_when_provider_raises() -> None:
    provider = FakeProvider([UpstreamError("llm down"), UpstreamError("llm down")])
    dto, cost = await compose(_sources(), provider, page_count=8, prepared_by="Cortex")
    assert dto.insights.confirmed == []
    assert dto.risks == []
    assert dto.faq[0].a == INSUFFICIENT_DATA


@pytest.mark.asyncio
async def test_compose_projects_known_risk_fields_when_extra_keys() -> None:
    provider = FakeProvider(
        [
            {},
            {
                "risks": [
                    {
                        "theme": "績效宣稱",
                        "trigger": "優於市場",
                        "where": "Voice",
                        "note": "n",
                        "level": "高",
                        "action": "送法遵",
                        "severity": "x",
                    }
                ]
            },
        ]
    )
    dto, _ = await compose(_sources(), provider, page_count=8, prepared_by="Cortex")
    assert len(dto.risks) == 1
    assert dto.risks[0].theme == "績效宣稱"


@pytest.mark.asyncio
async def test_compose_keeps_placeholders_on_empty_objects() -> None:
    provider = FakeProvider([{}, {}])
    dto, cost = await compose(_sources(), provider, page_count=8, prepared_by="Cortex")
    assert dto.insights.confirmed == []
    assert dto.coreJudgement == ""
    assert dto.risks == []
    assert dto.faq[0].a == INSUFFICIENT_DATA
    assert cost == pytest.approx(0.002)


@pytest.mark.asyncio
async def test_compose_ignores_wrong_typed_insights() -> None:
    provider = FakeProvider([{"insights": "not-a-dict"}, {"risks": []}])
    dto, _ = await compose(_sources(), provider, page_count=8, prepared_by="Cortex")
    assert dto.insights.confirmed == []
    assert dto.insights.inferences == []
    assert dto.insights.hypotheses == []
