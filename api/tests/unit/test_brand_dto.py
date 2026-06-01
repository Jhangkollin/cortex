from cortex_api.app.api.brand.dto import BrandProfileResponse, UpsertProfileRequest
from cortex_api.core.identifiers import uuid7
from cortex_api.service.brand.model.profile import BrandProfile


def test_upsert_request_minimal_requires_only_name() -> None:
    req = UpsertProfileRequest(name="Acme")
    assert req.name == "Acme"
    assert req.products == []
    assert req.legal_name is None


def test_upsert_request_typed_nested_and_to_model() -> None:
    bid = uuid7()
    req = UpsertProfileRequest(
        name="Acme",
        products=[{"name": "Card", "category": "Credit", "url": "/c", "confidence": 98}],
        category={"value": "Banking", "confidence": 95, "alternatives": ["FinTech"]},
    )
    assert req.products[0].confidence == 98
    assert req.category.alternatives == ["FinTech"]
    m = req.to_model(bid)
    assert m.brand_id == bid
    assert m.category_value == "Banking"
    assert m.category_confidence == 95
    assert m.category_alternatives == ["FinTech"]
    assert m.products == [{"name": "Card", "category": "Credit", "url": "/c", "confidence": 98}]


def test_response_from_model() -> None:
    bid = uuid7()
    model = BrandProfile(brand_id=bid, name="Acme", region=["TW"])
    resp = BrandProfileResponse.from_model(model)
    assert resp.brand_id == bid
    assert resp.name == "Acme"
    assert resp.region == ["TW"]
