from __future__ import annotations

import json
from typing import Any

import structlog
from cortex_brand_extract.llm.base import LLMProvider

_STYLES: tuple[str, ...] = ("expert", "warm", "playful")
_STYLE_BRIEF = {
    "expert": "objective, data-led expert advisor",
    "warm": "warm, empathetic, human",
    "playful": "lively, direct, conversational",
}
_SYSTEM = (
    "You write a brand's representative answer copy in 3 named styles, grounded "
    "ONLY in the provided brand profile and its real voice samples. Invent no "
    "facts. Each style is one short paragraph. "
    'Return JSON {"samples":{"expert":str,"warm":str,"playful":str}}.'
)
_SCHEMA = {
    "type": "object",
    "properties": {
        "samples": {
            "type": "object",
            "properties": {s: {"type": "string"} for s in _STYLES},
            "required": list(_STYLES),
        }
    },
    "required": ["samples"],
}


def _fallback(style: str, profile: dict[str, Any]) -> str:
    vs = profile.get("voice_samples") or []
    base = ""
    if vs and isinstance(vs, list) and isinstance(vs[0], dict):
        base = str(vs[0].get("text") or "")
    base = base or str(profile.get("about") or "") or str(profile.get("name") or "the brand")
    return f"[{_STYLE_BRIEF[style]}] {base}"[:1200]


async def generate_voice(
    profile: dict[str, Any],
    provider: LLMProvider,
    styles: tuple[str, ...] = _STYLES,
) -> dict[str, str]:
    """Generate one real voice sample per fixed style. Keys == styles, never empty, never raises."""
    user = json.dumps({"brand": profile, "styles": _STYLE_BRIEF}, ensure_ascii=False)
    raw: dict[str, Any] = {}
    try:
        result = await provider.complete_json(system=_SYSTEM, user=user, schema=_SCHEMA)
        got = result.data.get("samples", {})
        if isinstance(got, dict):
            raw = got
    except Exception as e:  # noqa: BLE001 — degrade to grounded fallback, never fail closed
        # @owl Issue 5 — emit a structured telemetry signal so operators can
        # distinguish "real LLM output" from "fallback because the provider
        # was broken". Without this the job persists as SUCCEEDED carrying
        # grounded-fallback copy and no alert ever fires.
        structlog.get_logger(__name__).warning(
            "voice_generator_provider_failed",
            error=str(e),
            error_type=type(e).__name__,
        )
        raw = {}

    out: dict[str, str] = {}
    for style in styles:
        try:
            v = raw.get(style)
            out[style] = v if isinstance(v, str) and v.strip() else _fallback(style, profile)
        except (TypeError, ValueError, AttributeError):
            out[style] = _fallback(style, profile)
    return out
