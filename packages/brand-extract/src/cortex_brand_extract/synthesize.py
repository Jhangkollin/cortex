"""One structured-output call: SiteCorpus + SiteMetadata → profile core
(name/tagline/category/about/voice/products). One repair retry on invalid
output, then a typed error.
"""

from __future__ import annotations

from pydantic import BaseModel, ValidationError

from cortex_brand_extract.corpus import SiteCorpus
from cortex_brand_extract.errors import UpstreamError
from cortex_brand_extract.llm.base import LLMProvider
from cortex_brand_extract.parse import SiteMetadata
from cortex_brand_extract.types import Category, Product, VoiceSample

_SYSTEM = (
    "You extract a brand profile from a company's own website text. "
    "Return only facts grounded in the provided pages. Do not invent "
    "competitors or products. If unsure, lower the confidence."
)

_SCHEMA = {
    "type": "object",
    "required": ["name", "category", "about"],
    "properties": {
        "name": {"type": "string"},
        "legal_name": {"type": "string"},
        "tagline": {"type": "string"},
        "monogram": {"type": "string"},
        "brand_color": {"type": "string"},
        "founded": {"type": "string"},
        "about": {"type": "string"},
        "region": {"type": "array", "items": {"type": "string"}},
        "category": {
            "type": "object",
            "required": ["value", "confidence"],
            "properties": {
                "value": {"type": "string"},
                "confidence": {"type": "integer"},
                "alternatives": {"type": "array", "items": {"type": "string"}},
            },
        },
        "voice_samples": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"src": {"type": "string"}, "text": {"type": "string"}},
            },
        },
        "products": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "category": {"type": "string"},
                    "url": {"type": "string"},
                    "confidence": {"type": "integer"},
                },
            },
        },
    },
}


class ProfileCore(BaseModel):
    name: str
    legal_name: str | None = None
    tagline: str | None = None
    monogram: str | None = None
    brand_color: str | None = None
    founded: str | None = None
    about: str
    region: list[str] = []
    category: Category
    voice_samples: list[VoiceSample] = []
    products: list[Product] = []
    cost_usd: float = 0.0


def _user_prompt(meta: SiteMetadata, corpus: SiteCorpus) -> str:
    return (
        f"SITE TITLE: {meta.title}\n"
        f"META DESCRIPTION: {meta.description or ''}\n"
        f"JSON-LD ORG: {meta.jsonld_org_name or ''}\n"
        f"FOUNDED HINT: {meta.founded or ''}\n"
        f"THEME COLOR HINT: {meta.theme_color or ''}\n\n"
        f"PAGE CORPUS:\n{corpus.text}"
    )


async def synthesize_profile(
    provider: LLMProvider, meta: SiteMetadata, corpus: SiteCorpus
) -> ProfileCore:
    user = _user_prompt(meta, corpus)
    last_err: Exception | None = None
    cost = 0.0
    for _attempt in range(2):
        result = await provider.complete_json(system=_SYSTEM, user=user, schema=_SCHEMA)
        cost += result.cost_usd
        try:
            core = ProfileCore(**result.data)
            return core.model_copy(update={"cost_usd": cost})
        except ValidationError as exc:
            last_err = exc
            user = (
                _user_prompt(meta, corpus) + f"\n\nYour previous output was invalid: {exc}. "
                "Return JSON that matches the schema exactly."
            )
    raise UpstreamError(
        f"synthesis failed schema validation after repair: {last_err}", stage="synthesize"
    ) from last_err
