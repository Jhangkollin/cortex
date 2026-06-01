from __future__ import annotations

from uuid import UUID

from cortex_brand_extract.types import BrandProfile as SP2Profile
from cortex_brand_extract.types import (
    Category,
    Competitor,
    ExtractionMeta,
    Product,
    VoiceSample,
)

from cortex_api.service.brand.analyze_mapping import sp2_to_sp1_profile

BRAND_ID = UUID("00000000-0000-0000-0000-000000000009")


def _sp2() -> SP2Profile:
    return SP2Profile(
        url="acmebank.asia",
        name="Acme Bank",
        legal_name=None,
        tagline="Bank better",
        monogram="AB",
        brand_color="#0af",
        category=Category(value="Banking", confidence=88, alternatives=["Fintech"]),
        region=["APAC"],
        founded="2009",
        about="A bank.",
        voice_samples=[VoiceSample(src="home", text="Hello")],
        products=[Product(name="Save", category="Deposit", url=None, confidence=70)],
        competitors=[Competitor(name="C1", domain="c1.com", match_score=42)],
        media_matches=[],
        extraction_meta=ExtractionMeta(tier="lite", model="claude-opus-4-7", cost_usd=0.6),
    )


def test_maps_scalars_and_url_to_source_url() -> None:
    m = sp2_to_sp1_profile(BRAND_ID, _sp2())
    assert m.brand_id == BRAND_ID
    assert m.name == "Acme Bank"
    assert m.legal_name is None
    assert m.source_url == "acmebank.asia"
    assert m.category_value == "Banking"
    assert m.category_confidence == 88
    assert m.category_alternatives == ["Fintech"]


def test_maps_nested_lists_as_dicts() -> None:
    m = sp2_to_sp1_profile(BRAND_ID, _sp2())
    assert m.products == [{"name": "Save", "category": "Deposit", "url": None, "confidence": 70}]
    assert m.competitors[0]["match_score"] == 42
    assert m.voice_samples[0]["text"] == "Hello"
    assert m.extraction_meta["cost_usd"] == 0.6
    assert m.extraction_meta["model"] == "claude-opus-4-7"
