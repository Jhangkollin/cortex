"""Async LLM orchestration for brand report synthesis.

Calls compose_live to build the deterministic base, then enriches it with
two LLM calls (insights bundle + risks). Always returns a valid tuple;
degrades gracefully on known upstream/parsing failures.
"""
# ruff: noqa: N815  # camelCase field names mirror the contract

from __future__ import annotations

import contextlib
import json
from typing import Any

import pydantic
import structlog
from cortex_brand_extract.errors import UpstreamError, UpstreamTimeoutError
from cortex_brand_extract.llm.base import LLMProvider

from cortex_api.service.brand_report.composer.sections import ReportSources, compose_live
from cortex_api.service.brand_report.contract import (
    FaqItem,
    Insights,
    ReportDTO,
    Risk,
)

_log = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# LLM prompt constants
# ---------------------------------------------------------------------------

_INSIGHTS_SYSTEM = (
    "You are a brand analyst. Synthesize ONLY from the provided brand data; "
    "invent nothing. Return the requested JSON fields populated strictly from "
    "the evidence in the input. "
    'Return JSON {"coreJudgement": str, "productNote": str, "competitorNote": str, '
    '"insights": {"confirmed": [str], "inferences": [str], "hypotheses": [str]}, '
    '"faqAnswers": [str]}'
)

_INSIGHTS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "coreJudgement": {"type": "string"},
        "productNote": {"type": "string"},
        "competitorNote": {"type": "string"},
        "insights": {
            "type": "object",
            "properties": {
                "confirmed": {"type": "array", "items": {"type": "string"}},
                "inferences": {"type": "array", "items": {"type": "string"}},
                "hypotheses": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["confirmed", "inferences", "hypotheses"],
        },
        "faqAnswers": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["coreJudgement", "productNote", "competitorNote", "insights", "faqAnswers"],
}

_RISKS_SYSTEM = (
    "You are a compliance analyst. Identify marketing and compliance risks "
    "grounded in the voice samples and product copy provided; invent nothing. "
    "Return a JSON object with a 'risks' array. "
    'Return JSON {"risks": [{"theme": str, "trigger": str, "where": str, '
    '"note": str, "level": str, "action": str}]}'
)

_RISKS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "risks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "theme": {"type": "string"},
                    "trigger": {"type": "string"},
                    "where": {"type": "string"},
                    "note": {"type": "string"},
                    "level": {"type": "string"},
                    "action": {"type": "string"},
                },
                "required": ["theme", "trigger", "where", "note", "level", "action"],
            },
        }
    },
    "required": ["risks"],
}

# ---------------------------------------------------------------------------
# Degradable exception types
# ---------------------------------------------------------------------------

_DEGRADABLE = (
    UpstreamError,
    UpstreamTimeoutError,
    pydantic.ValidationError,
    ValueError,
    KeyError,
    TypeError,
)


async def compose(
    sources: ReportSources,
    provider: LLMProvider,
    *,
    page_count: int,
    prepared_by: str,
    report_id: str | None = None,
) -> tuple[ReportDTO, float]:
    """Build a complete ReportDTO by running compose_live then two LLM calls.

    Always returns a valid (dto, cost) tuple. Degrades gracefully on upstream
    and malformed-JSON failures — keeps placeholder values and never raises.
    Programming errors (genuine bugs) are allowed to propagate.
    """
    base = compose_live(
        sources,
        page_count=page_count,
        prepared_by=prepared_by,
        report_id=report_id,
    )
    total_cost: float = 0.0

    # --- Call 1: insights bundle ---
    core_judgement: str = base.coreJudgement
    product_note: str = base.productNote
    competitor_note: str = base.competitorNote
    insights: Insights = base.insights
    faq_answers: list[str] = []

    profile = sources.profile
    user1 = json.dumps(
        {
            "profile": {
                "name": profile.get("name"),
                "about": profile.get("about"),
                "tagline": profile.get("tagline"),
                "category": profile.get("category_value"),
                "region": profile.get("region"),
                "voice_samples": profile.get("voice_samples"),
                "products": profile.get("products"),
                "competitors": profile.get("competitors"),
            },
            "core": [{"item": c.item, "body": c.body} for c in base.core],
            "productLines": [{"line": p.line, "thesis": p.thesis} for p in base.productLines],
            "competitors": [{"tier": t.tier, "brands": t.brands} for t in base.competitors],
            "faqQuestions": [f.q for f in base.faq],
        },
        ensure_ascii=False,
    )

    try:
        result1 = await provider.complete_json(
            system=_INSIGHTS_SYSTEM,
            user=user1,
            schema=_INSIGHTS_SCHEMA,
        )
        total_cost += result1.cost_usd
        d1 = result1.data

        core_judgement = d1.get("coreJudgement") or base.coreJudgement
        product_note = d1.get("productNote") or base.productNote
        competitor_note = d1.get("competitorNote") or base.competitorNote

        raw_insights = d1.get("insights")
        if isinstance(raw_insights, dict):
            confirmed = raw_insights.get("confirmed")
            inferences = raw_insights.get("inferences")
            hypotheses = raw_insights.get("hypotheses")
            if isinstance(confirmed, list) and isinstance(inferences, list) and isinstance(hypotheses, list):
                insights = Insights(
                    confirmed=[str(x) for x in confirmed],
                    inferences=[str(x) for x in inferences],
                    hypotheses=[str(x) for x in hypotheses],
                )

        raw_faq_answers = d1.get("faqAnswers")
        if isinstance(raw_faq_answers, list):
            faq_answers = [str(a) for a in raw_faq_answers]

    except _DEGRADABLE as e:
        _log.warning(
            "brand_report_synthesis_failed",
            error=str(e),
            error_type=type(e).__name__,
            phase="insights",
        )

    # --- Call 2: risks ---
    risks: list[Risk] = base.risks

    user2 = json.dumps(
        {
            "voice_samples": profile.get("voice_samples"),
            "products": profile.get("products"),
            "tagline": profile.get("tagline"),
            "about": profile.get("about"),
        },
        ensure_ascii=False,
    )

    try:
        result2 = await provider.complete_json(
            system=_RISKS_SYSTEM,
            user=user2,
            schema=_RISKS_SCHEMA,
        )
        total_cost += result2.cost_usd
        raw_risks = result2.data.get("risks")
        if isinstance(raw_risks, list):
            parsed_risks: list[Risk] = []
            for r in raw_risks:
                if not isinstance(r, dict):
                    continue
                with contextlib.suppress(Exception):
                    parsed_risks.append(Risk(**{k: v for k, v in r.items() if k in Risk.model_fields}))
            risks = parsed_risks

    except _DEGRADABLE as e:
        _log.warning(
            "brand_report_synthesis_failed",
            error=str(e),
            error_type=type(e).__name__,
            phase="risks",
        )

    # --- Rebuild faq list with answers ---
    updated_faq: list[FaqItem] = []
    for i, faq_item in enumerate(base.faq):
        if i < len(faq_answers) and faq_answers[i].strip():
            updated_faq.append(faq_item.model_copy(update={"a": faq_answers[i]}))
        else:
            updated_faq.append(faq_item)

    dto = base.model_copy(
        update={
            "coreJudgement": core_judgement,
            "productNote": product_note,
            "competitorNote": competitor_note,
            "insights": insights,
            "faq": updated_faq,
            "risks": risks,
        }
    )

    return dto, total_cost
