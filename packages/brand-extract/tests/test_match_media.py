from cortex_brand_extract.llm.base import FakeProvider
from cortex_brand_extract.match.media import rank_media
from cortex_brand_extract.types import MediaOutlet


async def test_empty_catalog_skips_with_warning() -> None:
    matches, warning, cost = await rank_media(
        FakeProvider(responses=[]), brand_name="Acme", category="Banking", catalog=[]
    )
    assert matches == []
    assert warning and "no media catalog" in warning
    assert cost == 0.0


async def test_ranks_supplied_catalog() -> None:
    fake = FakeProvider(
        responses=[{"ranked": [{"outlet_id": "moneydj", "name": "MoneyDJ", "relevance": 94}]}]
    )
    matches, warning, cost = await rank_media(
        fake,
        brand_name="Acme",
        category="Banking",
        catalog=[MediaOutlet(outlet_id="moneydj", name="MoneyDJ", topics=["ETF"])],
    )
    assert warning is None
    assert matches[0].outlet_id == "moneydj"
    assert matches[0].relevance == 94
    assert cost > 0.0
