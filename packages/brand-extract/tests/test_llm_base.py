import pytest

from cortex_brand_extract.errors import UpstreamError
from cortex_brand_extract.llm.base import FakeProvider, LLMResult


async def test_fake_provider_returns_scripted_json() -> None:
    fake = FakeProvider(responses=[{"name": "Acme"}])
    res = await fake.complete_json(system="s", user="u", schema={"type": "object"})
    assert isinstance(res, LLMResult)
    assert res.data == {"name": "Acme"}
    assert res.cost_usd >= 0.0


async def test_fake_provider_raises_when_scripted() -> None:
    fake = FakeProvider(responses=[UpstreamError("forced")])
    with pytest.raises(UpstreamError):
        await fake.complete_json(system="s", user="u", schema={"type": "object"})


async def test_fake_provider_exhaustion_raises() -> None:
    fake = FakeProvider(responses=[{"a": 1}])
    await fake.complete_json(system="s", user="u", schema={})
    with pytest.raises(AssertionError):
        await fake.complete_json(system="s", user="u", schema={})
