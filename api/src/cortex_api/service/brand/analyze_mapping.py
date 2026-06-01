"""Map a cortex_brand_extract.BrandProfile onto SP-1's BrandProfile SQLModel.

SP-2's type is UI-agnostic, snake_case; SP-1's table is the persistable shape.
SP-2 has no source_url/industry_vertical/primary_jurisdiction — `url` maps to
`source_url`; the other two stay None (other flows fill them).
"""

from __future__ import annotations

from uuid import UUID

from cortex_brand_extract.types import BrandProfile as SP2Profile

from cortex_api.service.brand.model.profile import BrandProfile


def sp2_to_sp1_profile(brand_id: UUID, src: SP2Profile) -> BrandProfile:
    return BrandProfile(
        brand_id=brand_id,
        name=src.name,
        legal_name=src.legal_name,
        tagline=src.tagline,
        monogram=src.monogram,
        brand_color=src.brand_color,
        founded=src.founded,
        about=src.about,
        source_url=src.url,
        industry_vertical=None,
        primary_jurisdiction=None,
        category_value=src.category.value,
        category_confidence=src.category.confidence,
        category_alternatives=list(src.category.alternatives),
        region=list(src.region),
        voice_samples=[vs.model_dump() for vs in src.voice_samples],
        products=[p.model_dump() for p in src.products],
        competitors=[c.model_dump() for c in src.competitors],
        media_matches=[m.model_dump() for m in src.media_matches],
        extraction_meta=src.extraction_meta.model_dump(mode="json"),
    )
