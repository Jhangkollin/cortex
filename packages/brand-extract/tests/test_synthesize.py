import pytest

from cortex_brand_extract.corpus import SiteCorpus
from cortex_brand_extract.errors import UpstreamError
from cortex_brand_extract.llm.base import FakeProvider
from cortex_brand_extract.parse import SiteMetadata
from cortex_brand_extract.synthesize import synthesize_profile

_GOOD = {
    "name": "Acme Bank Asia",
    "tagline": "Banking, redesigned for Asia.",
    "category": {"value": "Retail banking", "confidence": 95, "alternatives": ["FinTech"]},
    "about": "27 years across Asia.",
    "region": ["Taiwan"],
    "voice_samples": [{"src": "/about", "text": "Banking should work for people."}],
    "products": [
        {"name": "Smart Account", "category": "Deposits", "url": "/smart", "confidence": 96}
    ],
}

_META = SiteMetadata(base_url="https://acmebank.asia/", title="Acme Bank Asia")
_CORPUS = SiteCorpus(text="Acme Bank Asia ...", page_count=1, truncated=False)


async def test_synthesis_maps_llm_output_into_profile_core() -> None:
    prov = FakeProvider(responses=[_GOOD])
    core = await synthesize_profile(prov, _META, _CORPUS)
    assert core.name == "Acme Bank Asia"
    assert core.category.confidence == 95
    assert core.products[0].name == "Smart Account"
    assert core.cost_usd > 0.0


async def test_synthesis_repairs_once_then_succeeds() -> None:
    prov = FakeProvider(responses=[{"bogus": True}, _GOOD])
    core = await synthesize_profile(prov, _META, _CORPUS)
    assert core.name == "Acme Bank Asia"


async def test_synthesis_raises_after_failed_repair() -> None:
    prov = FakeProvider(responses=[{"bogus": True}, {"still": "bad"}])
    with pytest.raises(UpstreamError):
        await synthesize_profile(prov, _META, _CORPUS)
