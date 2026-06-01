# api/src/cortex_api/service/media_network/matcher.py
from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any

from cortex_brand_extract.llm.base import LLMProvider

from cortex_api.service.media_network.model.member import MediaNetworkMember

_SYSTEM = (
    "You rank a fixed catalog of real media publishers for a brand's audience. "
    "You MUST only use hostnames from the provided catalog. Never invent outlets. "
    'Return JSON {"outlets":[{hostname, relevance(0-100), why, topics[], '
    "context_agent_label, audience_descriptor}]} ordered best-first."
)
_SCHEMA = {
    "type": "object",
    "properties": {
        "outlets": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "hostname": {"type": "string"},
                    "relevance": {"type": "integer"},
                    "why": {"type": "string"},
                    "topics": {"type": "array", "items": {"type": "string"}},
                    "context_agent_label": {"type": "string"},
                    "audience_descriptor": {"type": "string"},
                },
                "required": ["hostname", "relevance", "why", "topics", "context_agent_label", "audience_descriptor"],
            },
        }
    },
    "required": ["outlets"],
}


def _fallback(member: MediaNetworkMember) -> dict[str, Any]:
    return {
        "hostname": member.hostname,
        "member_name": member.member_name,
        "wau": member.wau,
        "relevance": 50,
        "why": f"{member.member_name} reaches an audience relevant to this brand's category.",
        "topics": [member.category_hint] if member.category_hint else [],
        "context_agent_label": "Context Agent",
        "audience_descriptor": member.member_name,
    }


async def match_outlets(
    profile: dict[str, Any],
    catalog: Sequence[MediaNetworkMember],
    provider: LLMProvider,
    outlet_count: int,
) -> list[dict[str, Any]]:
    """Rank/frame the brand against the REAL catalog. Output is always a subset of catalog."""
    by_host = {m.hostname: m for m in catalog}
    user = json.dumps(
        {
            "brand": profile,
            "catalog": [
                {"hostname": m.hostname, "name": m.member_name, "wau": m.wau, "category_hint": m.category_hint}
                for m in catalog
            ],
        },
        ensure_ascii=False,
    )
    try:
        result = await provider.complete_json(system=_SYSTEM, user=user, schema=_SCHEMA)
        raw = result.data.get("outlets", [])
        if not isinstance(raw, list):
            raw = []
    except Exception:  # noqa: BLE001 — degrade to deterministic fallback, never fail closed
        raw = []

    picked: list[dict[str, Any]] = []
    seen: set[str] = set()
    for o in raw:
        if not isinstance(o, dict):
            continue
        try:
            host = o.get("hostname")
            if host in by_host and host not in seen:
                seen.add(host)
                member = by_host[host]
                picked.append(
                    {
                        "hostname": host,
                        "member_name": member.member_name,
                        "wau": member.wau,
                        "relevance": int(o.get("relevance", 0)),
                        "why": str(o.get("why", "")) or _fallback(member)["why"],
                        "topics": [str(t) for t in o.get("topics", [])],
                        "context_agent_label": str(o.get("context_agent_label", "Context Agent")),
                        "audience_descriptor": str(o.get("audience_descriptor", member.member_name)),
                    }
                )
        except (TypeError, ValueError, AttributeError):
            continue

    if len(picked) < outlet_count:
        brand_cat = str(profile.get("category", "")).lower()
        rest = sorted(
            (m for m in catalog if m.hostname not in seen),
            key=lambda m: ((m.category_hint or "").lower() != brand_cat, -(m.wau or 0)),
        )
        for m in rest:
            picked.append(_fallback(m))

    return picked[:outlet_count]
