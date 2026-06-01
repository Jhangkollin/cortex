from cortex_brand_extract.llm.base import FakeProvider
from cortex_brand_extract.match.competitors import rank_competitors
from cortex_brand_extract.types import CompetitorCandidate


async def test_returns_empty_with_warning_when_no_candidates() -> None:
    comps, warning, cost = await rank_competitors(
        FakeProvider(responses=[]), brand_name="Acme", category="Retail banking", candidates=[]
    )
    assert comps == []
    assert warning and "no competitor candidates" in warning
    assert cost == 0.0


async def test_ranks_caller_supplied_candidates_only() -> None:
    fake = FakeProvider(
        responses=[
            {"ranked": [{"name": "Cathay United", "domain": "cathaybk.com.tw", "match_score": 93}]}
        ]
    )
    comps, warning, cost = await rank_competitors(
        fake,
        brand_name="Acme",
        category="Retail banking",
        candidates=[CompetitorCandidate(name="Cathay United", domain="cathaybk.com.tw")],
    )
    assert warning is None
    assert comps[0].name == "Cathay United"
    assert comps[0].match_score == 93
    assert cost > 0.0
