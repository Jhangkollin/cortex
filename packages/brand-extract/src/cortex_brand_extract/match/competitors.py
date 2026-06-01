from __future__ import annotations

from cortex_brand_extract.llm.base import LLMProvider
from cortex_brand_extract.types import Competitor, CompetitorCandidate

_SYSTEM = (
    "Rank how directly each candidate competes with the brand. "
    "Only use the supplied candidates. Score 0-100."
)
_SCHEMA = {
    "type": "object",
    "required": ["ranked"],
    "properties": {
        "ranked": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "domain": {"type": "string"},
                    "match_score": {"type": "integer"},
                },
            },
        }
    },
}


async def rank_competitors(
    provider: LLMProvider,
    *,
    brand_name: str,
    category: str,
    candidates: list[CompetitorCandidate],
) -> tuple[list[Competitor], str | None, float]:
    if not candidates:
        return [], "no competitor candidates supplied; competitor match skipped", 0.0
    listing = "\n".join(f"- {c.name} ({c.domain or 'no domain'})" for c in candidates)
    result = await provider.complete_json(
        system=_SYSTEM,
        user=f"BRAND: {brand_name}\nCATEGORY: {category}\nCANDIDATES:\n{listing}",
        schema=_SCHEMA,
    )
    allowed = {c.name for c in candidates}
    comps = [
        Competitor(
            name=r["name"],
            domain=r.get("domain"),
            match_score=int(r.get("match_score", 0)),
        )
        for r in result.data.get("ranked", [])
        if r.get("name") in allowed
    ]
    return comps, None, result.cost_usd
