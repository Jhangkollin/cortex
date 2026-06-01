from __future__ import annotations

from cortex_brand_extract.llm.base import LLMProvider
from cortex_brand_extract.types import MediaMatch, MediaOutlet

_SYSTEM = (
    "Rank how relevant each media outlet's audience is to the brand. "
    "Only use the supplied catalog. Score 0-100."
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
                    "outlet_id": {"type": "string"},
                    "name": {"type": "string"},
                    "relevance": {"type": "integer"},
                },
            },
        }
    },
}


async def rank_media(
    provider: LLMProvider,
    *,
    brand_name: str,
    category: str,
    catalog: list[MediaOutlet],
) -> tuple[list[MediaMatch], str | None, float]:
    if not catalog:
        return [], "no media catalog supplied; media match skipped", 0.0
    listing = "\n".join(
        f"- [{o.outlet_id}] {o.name} — {o.audience or ''} topics={o.topics}" for o in catalog
    )
    result = await provider.complete_json(
        system=_SYSTEM,
        user=f"BRAND: {brand_name}\nCATEGORY: {category}\nCATALOG:\n{listing}",
        schema=_SCHEMA,
    )
    allowed = {o.outlet_id for o in catalog}
    matches = [
        MediaMatch(
            outlet_id=r["outlet_id"],
            name=r.get("name", ""),
            relevance=int(r.get("relevance", 0)),
        )
        for r in result.data.get("ranked", [])
        if r.get("outlet_id") in allowed
    ]
    return matches, None, result.cost_usd
