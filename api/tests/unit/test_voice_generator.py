from cortex_api.service.voice.generator import generate_voice


class FakeProvider:
    model = "fake"

    def __init__(self, payload):
        self._payload = payload

    async def complete_json(self, *, system, user, schema):
        from cortex_brand_extract.llm.base import LLMResult

        return LLMResult(data=self._payload)


PROFILE = {
    "name": "Acme Bank",
    "about": "Taiwan digital bank for young investors.",
    "tagline": "Bank smarter",
    "category": "Banking",
    "products": [],
    "competitors": [],
    "voice_samples": [{"text": "We keep banking simple and honest."}],
}


async def test_subset_enforced_all_three_present():
    prov = FakeProvider({"samples": {"expert": "E copy", "warm": "W copy", "playful": "P copy", "BOGUS": "drop me"}})
    out = await generate_voice(PROFILE, prov)
    assert set(out.keys()) == {"expert", "warm", "playful"}
    assert out["expert"] == "E copy" and out["warm"] == "W copy" and out["playful"] == "P copy"


async def test_missing_style_grounded_fallback_never_empty():
    prov = FakeProvider({"samples": {"expert": "only expert"}})
    out = await generate_voice(PROFILE, prov)
    assert out["expert"] == "only expert"
    assert out["warm"] and out["playful"]


async def test_malformed_payload_never_raises():
    for bad in ({"samples": 42}, {"samples": {"expert": 123}}, {"x": 1}, {"samples": {"expert": None}}):
        out = await generate_voice(PROFILE, FakeProvider(bad))
        assert set(out.keys()) == {"expert", "warm", "playful"}
        assert all(isinstance(v, str) and v for v in out.values())
