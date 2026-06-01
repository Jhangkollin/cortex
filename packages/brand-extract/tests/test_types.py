import pytest
from pydantic import ValidationError

from cortex_brand_extract.types import (
    BrandProfile,
    Category,
    Competitor,
    CompetitorCandidate,
    ExtractionMeta,
    MediaMatch,
    MediaOutlet,
    Product,
    ProviderConfig,
    VoiceSample,
)


def _profile() -> BrandProfile:
    return BrandProfile(
        url="acmebank.asia",
        name="Acme Bank Asia",
        legal_name="Acme Bank Asia Holdings, Ltd.",
        tagline="Banking, redesigned for Asia.",
        monogram="A",
        brand_color="#225D59",
        category=Category(value="Retail banking", confidence=96, alternatives=["FinTech"]),
        region=["Taiwan"],
        founded="1998",
        about="27 years serving Asia.",
        voice_samples=[VoiceSample(src="/about", text="Banking should work for people.")],
        products=[Product(name="Smart Account", category="Deposits", url="/smart", confidence=97)],
        competitors=[Competitor(name="Cathay United", domain="cathaybk.com.tw", match_score=94)],
        media_matches=[MediaMatch(outlet_id="moneydj", name="MoneyDJ", relevance=94)],
        extraction_meta=ExtractionMeta(tier="lite", model="claude", cost_usd=0.03),
    )


def test_brand_profile_round_trips_to_dict() -> None:
    p = _profile()
    d = p.model_dump()
    assert d["name"] == "Acme Bank Asia"
    assert d["category"]["confidence"] == 96
    assert d["extraction_meta"]["tier"] == "lite"


def test_brand_profile_is_frozen() -> None:
    p = _profile()
    with pytest.raises(ValidationError):
        p.name = "Changed"


def test_provider_config_requires_kind_and_key() -> None:
    cfg = ProviderConfig(kind="claude", api_key="sk-x", model="claude-opus-4-7")
    assert cfg.kind == "claude"
    with pytest.raises(ValidationError):
        ProviderConfig(kind="bogus", api_key="x", model="m")  # type: ignore[arg-type]


def test_media_outlet_is_caller_input_shape() -> None:
    o = MediaOutlet(outlet_id="moneydj", name="MoneyDJ", audience="Investors", topics=["ETF"])
    assert o.outlet_id == "moneydj"


def test_competitor_candidate_input_shape() -> None:
    c = CompetitorCandidate(name="Cathay United")
    assert c.domain is None
    c2 = CompetitorCandidate(name="E.Sun", domain="esunbank.com.tw")
    assert c2.domain == "esunbank.com.tw"
