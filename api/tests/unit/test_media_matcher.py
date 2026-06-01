# api/tests/unit/test_media_matcher.py
from cortex_api.service.media_network.matcher import match_outlets
from cortex_api.service.media_network.model.member import MediaNetworkMember


class FakeProvider:
    model = "fake"

    def __init__(self, payload):
        self._payload = payload

    async def complete_json(self, *, system, user, schema):
        from cortex_brand_extract.llm.base import LLMResult

        return LLMResult(data=self._payload)


CATALOG = [
    MediaNetworkMember(hostname="a.tw", member_name="A", wau=300, category_hint="finance"),
    MediaNetworkMember(hostname="b.tw", member_name="B", wau=200, category_hint="tech"),
    MediaNetworkMember(hostname="c.tw", member_name="C", wau=100, category_hint="finance"),
]
PROFILE = {"name": "Brand", "category": "finance", "region": ["TW"], "products": [], "competitors": [], "about": ""}


async def test_hallucinated_names_dropped_and_subset_enforced():
    prov = FakeProvider(
        {
            "outlets": [
                {
                    "hostname": "a.tw",
                    "relevance": 90,
                    "why": "x",
                    "topics": ["t"],
                    "context_agent_label": "L",
                    "audience_descriptor": "D",
                },
                {
                    "hostname": "DOES-NOT-EXIST.tw",
                    "relevance": 88,
                    "why": "y",
                    "topics": [],
                    "context_agent_label": "L",
                    "audience_descriptor": "D",
                },
            ]
        }
    )
    out = await match_outlets(PROFILE, CATALOG, prov, outlet_count=8)
    hosts = [o["hostname"] for o in out]
    assert "DOES-NOT-EXIST.tw" not in hosts
    assert set(hosts).issubset({"a.tw", "b.tw", "c.tw"})
    assert hosts[0] == "a.tw"


async def test_backfill_is_deterministic_when_llm_returns_too_few():
    prov = FakeProvider({"outlets": []})
    out = await match_outlets(PROFILE, CATALOG, prov, outlet_count=8)
    assert [o["hostname"] for o in out] == ["a.tw", "c.tw", "b.tw"]
    assert all(o["why"] for o in out)


async def test_truncated_to_outlet_count():
    prov = FakeProvider(
        {
            "outlets": [
                {
                    "hostname": h,
                    "relevance": 50,
                    "why": "w",
                    "topics": [],
                    "context_agent_label": "L",
                    "audience_descriptor": "D",
                }
                for h in ("a.tw", "b.tw", "c.tw")
            ]
        }
    )
    out = await match_outlets(PROFILE, CATALOG, prov, outlet_count=2)
    assert len(out) == 2


async def test_outlets_carry_catalog_member_name_and_wau():
    prov = FakeProvider(
        {
            "outlets": [
                {
                    "hostname": "a.tw",
                    "relevance": 90,
                    "why": "x",
                    "topics": [],
                    "context_agent_label": "L",
                    "audience_descriptor": "D",
                },
            ]
        }
    )
    out = await match_outlets(PROFILE, CATALOG, prov, outlet_count=8)
    assert out[0]["member_name"] == "A" and out[0]["wau"] == 300


async def test_outlets_payload_is_dict_does_not_raise():
    prov = FakeProvider({"outlets": {"foo": "bar"}})
    out = await match_outlets(PROFILE, CATALOG, prov, outlet_count=3)
    assert {o["hostname"] for o in out}.issubset({"a.tw", "b.tw", "c.tw"})
    assert len(out) == 3  # degrades to deterministic backfill


async def test_outlets_payload_is_scalar_does_not_raise():
    prov = FakeProvider({"outlets": 42})
    out = await match_outlets(PROFILE, CATALOG, prov, outlet_count=3)
    assert [o["hostname"] for o in out] == ["a.tw", "c.tw", "b.tw"]  # full deterministic backfill


async def test_non_numeric_relevance_item_skipped_not_raised():
    prov = FakeProvider(
        {
            "outlets": [
                {
                    "hostname": "a.tw",
                    "relevance": "not-a-number",
                    "why": "x",
                    "topics": [],
                    "context_agent_label": "L",
                    "audience_descriptor": "D",
                },
                {
                    "hostname": "b.tw",
                    "relevance": 70,
                    "why": "y",
                    "topics": [],
                    "context_agent_label": "L",
                    "audience_descriptor": "D",
                },
            ]
        }
    )
    out = await match_outlets(PROFILE, CATALOG, prov, outlet_count=8)
    hosts = [o["hostname"] for o in out]
    assert "b.tw" in hosts  # the well-formed item is kept
    assert set(hosts).issubset({"a.tw", "b.tw", "c.tw"})  # never raises; subset holds
    assert len(out) <= 8
