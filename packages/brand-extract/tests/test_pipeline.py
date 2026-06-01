import httpx
import respx

from cortex_brand_extract import extract_brand_profile
from cortex_brand_extract.llm.base import FakeProvider
from cortex_brand_extract.progress import ListSink
from cortex_brand_extract.types import CompetitorCandidate, MediaOutlet

_HOME = (
    """<html><head><title>Acme Bank Asia</title>
<meta name="description" content="27 years across Asia." />
<meta name="theme-color" content="#225D59" /></head>
<body><p>Acme Bank Asia serves millions. Banking should work for people. """
    + ("text " * 80)
    + """</p>
<a href="/about">About</a></body></html>"""
)

_ABOUT = "<html><body><p>" + ("About Acme. " * 80) + "</p></body></html>"

_SYNTH = {
    "name": "Acme Bank Asia",
    "tagline": "Banking, redesigned for Asia.",
    "about": "27 years across Asia.",
    "region": ["Taiwan"],
    "category": {"value": "Retail banking", "confidence": 95, "alternatives": []},
    "voice_samples": [{"src": "/about", "text": "Banking should work for people."}],
    "products": [
        {"name": "Smart Account", "category": "Deposits", "url": "/smart", "confidence": 96}
    ],
}
_COMP = {"ranked": [{"name": "Cathay United", "domain": "cathaybk.com.tw", "match_score": 92}]}
_MEDIA = {"ranked": [{"outlet_id": "moneydj", "name": "MoneyDJ", "relevance": 90}]}


@respx.mock
async def test_pipeline_end_to_end_lite_with_fakes() -> None:
    respx.get("https://acmebank.asia/").mock(return_value=httpx.Response(200, html=_HOME))
    respx.get("https://acmebank.asia/about").mock(return_value=httpx.Response(200, html=_ABOUT))
    sink = ListSink()
    provider = FakeProvider(responses=[_SYNTH, _COMP, _MEDIA])

    profile = await extract_brand_profile(
        "acmebank.asia",
        tier="lite",
        provider=provider,
        max_pages=2,
        competitor_candidates=[CompetitorCandidate(name="Cathay United", domain="cathaybk.com.tw")],
        seed_media_catalog=[MediaOutlet(outlet_id="moneydj", name="MoneyDJ", topics=["ETF"])],
        progress=sink,
    )

    assert profile.name == "Acme Bank Asia"
    assert profile.competitors[0].name == "Cathay United"
    assert profile.media_matches[0].outlet_id == "moneydj"
    assert profile.extraction_meta.tier == "lite"
    assert profile.extraction_meta.cost_usd > 0.0
    stages = {e.stage for e in sink.events}
    assert {"fetch", "parse", "synthesize", "done"}.issubset(stages)


@respx.mock
async def test_pipeline_degrades_when_a_match_has_no_candidates() -> None:
    respx.get("https://acmebank.asia/").mock(return_value=httpx.Response(200, html=_HOME))
    respx.get("https://acmebank.asia/about").mock(return_value=httpx.Response(200, html=_ABOUT))
    provider = FakeProvider(responses=[_SYNTH])  # only synthesis is called

    profile = await extract_brand_profile(
        "acmebank.asia",
        tier="lite",
        provider=provider,
        max_pages=2,
    )
    assert profile.competitors == []
    assert profile.media_matches == []
    assert any("competitor" in w for w in profile.extraction_meta.warnings)
    assert any("media" in w for w in profile.extraction_meta.warnings)
