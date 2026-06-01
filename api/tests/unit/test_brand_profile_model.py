from uuid import UUID

from cortex_api.core.identifiers import uuid7
from cortex_api.service.brand.model.profile import BrandProfile


def test_brand_profile_minimal_construct() -> None:
    bid = uuid7()
    p = BrandProfile(brand_id=bid, name="Acme")
    assert p.brand_id == bid
    assert p.name == "Acme"
    assert p.category_alternatives == []
    assert p.region == []
    assert p.voice_samples == []
    assert p.products == []
    assert p.competitors == []
    assert p.media_matches == []
    assert p.extraction_meta is None
    assert p.legal_name is None


def test_brand_profile_table_and_columns() -> None:
    assert BrandProfile.__tablename__ == "brand_profile"
    cols = set(BrandProfile.model_fields)
    assert {"brand_id", "name", "products", "extraction_meta", "created_at", "updated_at"} <= cols


def test_brand_profile_holds_rich_jsonb() -> None:
    p = BrandProfile(
        brand_id=uuid7(),
        name="Acme Bank",
        products=[{"name": "Card", "category": "Credit", "url": "/c", "confidence": 98}],
        competitors=[{"name": "Rival", "domain": "rival.com", "match_score": 90}],
        extraction_meta={"tier": "lite", "model": "claude-x", "cost_usd": 0.6},
    )
    assert p.products[0]["confidence"] == 98
    assert p.extraction_meta["tier"] == "lite"
    assert isinstance(p.brand_id, UUID)
