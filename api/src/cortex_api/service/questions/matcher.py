# api/src/cortex_api/service/questions/matcher.py
from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from datetime import date
from typing import Any

import structlog
from cortex_brand_extract.llm.base import LLMProvider

from cortex_api.service.questions.model.question import WeeklyQuestion

_INTENTS = ("Explore", "Understand", "Evaluate", "Act")

# Default relevance floor when no caller-supplied threshold is passed (direct
# unit-test calls). The production value is owned by
# ``Config.min_relevance_score`` (env ``CORTEX_QUESTIONS_MIN_RELEVANCE_SCORE``)
# and threaded in by ``QuestionsJobService``.
_DEFAULT_MIN_RELEVANCE_SCORE = 40

# ---------------------------------------------------------------------------
# Snapshot-rank pass — pick from the real ``weekly_question`` snapshot.
# ---------------------------------------------------------------------------

_SYSTEM = (
    "You rank a fixed list of REAL reader questions for a brand. "
    "Only use question ids from the provided list — never invent questions. "
    "For each, classify intent as one of Explore|Understand|Evaluate|Act, give "
    "score 0-100 (relevance to the brand), and competitorMentions strictly chosen "
    "from the brand's competitor list (never invent competitors). "
    'Return JSON {"questions":[{id, intent, score, competitorMentions[]}]} best-first.'
)
_SCHEMA = {
    "type": "object",
    "properties": {
        "questions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "intent": {"type": "string"},
                    "score": {"type": "integer"},
                    "competitorMentions": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["id", "intent", "score", "competitorMentions"],
            },
        }
    },
    "required": ["questions"],
}

# ---------------------------------------------------------------------------
# D8 — LLM-synth fallback (spec §3 D8). Triggers when snapshot is empty or
# yields fewer items than ``question_count``. Generates realistic reader
# questions strictly grounded in the brand_profile (no invented competitors).
# Synth ids are prefixed ``synth-<hash>`` so the persisted JSONB row is
# self-describing (real vs synth is greppable).
# ---------------------------------------------------------------------------

_SYNTH_SYSTEM = (
    "You generate REAL-WORLD reader questions that readers in this brand's "
    "category are asking right now (purchase intent). Ground each question "
    "strictly in the provided brand profile (category, products, competitors, "
    "about). Invent no facts; never use competitor names outside the provided "
    "list. Mix intents across Explore/Understand/Evaluate/Act. The ``asks`` "
    "field is a realistic engagement count (50-500). "
    'Return JSON {"questions":[{text, intent, score, asks, competitorMentions[]}]}.'
)
_SYNTH_SCHEMA = {
    "type": "object",
    "properties": {
        "questions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "intent": {"type": "string"},
                    "score": {"type": "integer"},
                    "asks": {"type": "integer"},
                    "competitorMentions": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["text", "intent", "score", "asks", "competitorMentions"],
            },
        }
    },
    "required": ["questions"],
}


def _when(q: WeeklyQuestion) -> str:
    return "" if q.last_event_date is None else q.last_event_date.isoformat()


def _base(q: WeeklyQuestion) -> dict[str, Any]:
    return {"id": q.id, "text": q.question_title, "media": q.publisher_name, "asks": q.clicks, "when": _when(q)}


def _synth_id(brand_name: str, text: str, index: int) -> str:
    """Deterministic id for a synthesized question. Prefixed ``synth-`` so a
    consumer reading the persisted JSONB can tell synth from real at a glance."""
    return f"synth-{hashlib.sha256(f'{brand_name}|{text}|{index}'.encode()).hexdigest()[:32]}"


async def _synth(
    profile: dict[str, Any],
    count: int,
    provider: LLMProvider,
) -> list[dict[str, Any]]:
    """D8: LLM-synth ``count`` questions grounded in ``brand_profile`` when
    the real snapshot can't satisfy the requested ``question_count``.

    Contract: never raises (broad except → deterministic placeholder), never
    empty (deterministic placeholder per remaining slot), output keys match the
    snapshot-rank path so downstream projection is uniform.
    """
    if count <= 0:
        return []
    competitors = {str(c) for c in (profile.get("competitors") or [])}
    brand_name = str(profile.get("name") or "Brand")
    category = str(profile.get("category") or "Industry")

    user = json.dumps({"brand": profile, "count": count}, ensure_ascii=False)
    raw: list[Any] = []
    try:
        result = await provider.complete_json(system=_SYNTH_SYSTEM, user=user, schema=_SYNTH_SCHEMA)
        got = result.data.get("questions", [])
        if isinstance(got, list):
            raw = got
    except Exception:  # noqa: BLE001 — D8 degrades to grounded placeholder, never fail closed
        raw = []

    today = date.today().isoformat()
    out: list[dict[str, Any]] = []
    for i, o in enumerate(raw):
        if not isinstance(o, dict):
            continue
        try:
            text = str(o.get("text") or "").strip()
            if not text:
                continue
            intent_raw = str(o.get("intent", "Understand"))
            asks_raw = o.get("asks", 100)
            score_raw = o.get("score", 50)
            mentions = [c for c in (o.get("competitorMentions") or []) if str(c) in competitors]
            out.append(
                {
                    "id": _synth_id(brand_name, text, i),
                    "text": text[:2048],
                    "media": category,
                    "asks": max(0, min(int(asks_raw), 999_999)),
                    "when": today,
                    "intent": intent_raw if intent_raw in _INTENTS else "Understand",
                    "score": max(0, min(int(score_raw), 100)),
                    "competitorMentions": mentions,
                }
            )
            if len(out) >= count:
                break
        except (TypeError, ValueError, AttributeError):
            continue

    # Deterministic placeholder for any remaining slot — the wizard is never empty
    # even when the LLM is broken AND the brand profile is bare. The placeholder
    # is obviously generic (``Top questions about <category>``) so its synth
    # provenance is legible to operators reading the persisted JSONB.
    placeholders = 0
    while len(out) < count:
        i = len(out)
        text = f"Top questions about {category}"
        out.append(
            {
                "id": _synth_id(brand_name, text, i),
                "text": text,
                "media": category,
                "asks": 0,
                "when": today,
                "intent": "Understand",
                "score": 0,
                "competitorMentions": [],
            }
        )
        placeholders += 1

    if placeholders:
        # The placeholder branch is the most operationally dangerous output the
        # matcher produces: it looks like a real question ("Top questions about
        # Watches") but actually means the synth LLM degraded. Emit a WARNING so
        # it is alertable, not just discoverable by reading the wizard.
        structlog.get_logger(__name__).warning(
            "questions_synth_placeholder",
            brand=brand_name,
            category=category,
            placeholders=placeholders,
            requested=count,
        )
    return out[:count]


async def match_questions(
    profile: dict[str, Any],
    snapshot: Sequence[WeeklyQuestion],
    provider: LLMProvider,
    question_count: int,
    min_relevance_score: int = _DEFAULT_MIN_RELEVANCE_SCORE,
) -> list[dict[str, Any]]:
    """Rank/frame REAL snapshot questions for the brand.

    Pass 1 — snapshot rank: the LLM scores each pool question's relevance to the
    brand (0-100). We keep only picks that are ⊆ snapshot, score
    ``>= min_relevance_score``, with competitorMentions ⊆ profile.competitors.
    The score floor is what makes Pass 1 a real *relevance* gate rather than a
    "did the LLM mention this id" gate.
    Pass 2 — D8 LLM-synth: any deficit (the snapshot is empty, OR the ranker
    endorsed nothing relevant — e.g. a Swiss-watch brand against a Taiwanese-
    news pool) is filled with questions synthesized from the brand_profile.
    Synth ids are ``synth-`` prefixed so the persisted JSONB row distinguishes
    real reader engagement from profile-derived simulation.

    DESIGN TRADEOFF (not a universal law): when Pass 1 leaves a deficit we fill
    it with brand-grounded synth, never a relevance-blind "top-clicks backfill".
    Padding with the globally most-clicked pool questions is what surfaced
    off-brand questions (the Hamilton-watch UAT bug). This assumes the rank LLM
    is reliable enough that "ranker endorsed nothing" ≈ "pool is truly
    irrelevant for this brand". The cost: if the ranker misfires against a pool
    that IS on-brand, the output is fully synthetic (real but no reader-
    engagement signal) and, if the synth provider is also down, degrades to the
    deterministic placeholder (see ``_synth``, which now WARN-logs that case).
    A future maintainer weighing restoring top-clicks should read this history
    first. The ``questions_relevance_gate`` log below makes the gate's behavior
    measurable so the threshold can be tuned against real data.
    """
    logger = structlog.get_logger(__name__)
    by_id = {q.id: q for q in snapshot}
    competitors = {str(c) for c in (profile.get("competitors") or [])}
    user = json.dumps(
        {
            "brand": profile,
            "questions": [
                {"id": q.id, "text": q.question_title, "media": q.publisher_name, "clicks": q.clicks} for q in snapshot
            ],
        },
        ensure_ascii=False,
    )
    try:
        result = await provider.complete_json(system=_SYSTEM, user=user, schema=_SCHEMA)
        raw = result.data.get("questions", [])
        if not isinstance(raw, list):
            raw = []
    except Exception:  # noqa: BLE001 — degrade to D8 synth, never fail closed
        raw = []

    picked: list[dict[str, Any]] = []
    seen: set[str] = set()
    dropped_below_floor = 0
    for o in raw:
        if not isinstance(o, dict):
            continue
        try:
            qid = o.get("id")
            if qid not in by_id or qid in seen:
                continue
            score = int(o.get("score", 0))
            if score < min_relevance_score:
                # Endorsed by id but not relevant enough — leave the slot for D8
                # synth rather than show a weak pool match.
                dropped_below_floor += 1
                continue
            q = by_id[qid]
            intent = str(o.get("intent", "Understand"))
            picked.append(
                {
                    **_base(q),
                    "intent": intent if intent in _INTENTS else "Understand",
                    "score": score,
                    "competitorMentions": [c for c in (o.get("competitorMentions") or []) if str(c) in competitors],
                }
            )
            seen.add(qid)
        except (TypeError, ValueError, AttributeError):
            continue

    # D8: fill any deficit with brand-grounded synth (never relevance-blind
    # pool top-clicks). Covers empty pool AND "pool has nothing relevant".
    synth_filled = 0
    if len(picked) < question_count:
        synth_filled = question_count - len(picked)
        picked.extend(await _synth(profile, synth_filled, provider))

    logger.info(
        "questions_relevance_gate",
        brand=str(profile.get("name") or ""),
        pool_size=len(snapshot),
        llm_returned=len(raw),
        kept_relevant=len(seen),
        dropped_below_floor=dropped_below_floor,
        synth_filled=synth_filled,
        min_relevance_score=min_relevance_score,
    )
    return picked[:question_count]
