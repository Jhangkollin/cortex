from typing import Any

from cortex_brand_extract.llm.claude import (
    _PRICE_CACHE_WRITE,
    ClaudeProvider,
)
from cortex_brand_extract.types import ProviderConfig


def _usage(**fields: int) -> type:
    """Build a usage stub. Anthropic omits buckets that are zero, so the
    adapter must getattr-default them; we mirror that by only setting the
    fields a test cares about.
    """
    return type("_Usage", (), fields)


class _FakeMessages:
    def __init__(self, recorder: dict[str, Any], usage: type) -> None:
        self._rec = recorder
        self._usage = usage

    async def create(self, **kwargs: Any) -> Any:
        self._rec.update(kwargs)

        class _Block:
            type = "tool_use"
            input = {"name": "Acme Bank"}

        msg_usage = self._usage

        class _Msg:
            content = [_Block()]
            usage = msg_usage()

        return _Msg()


class _FakeAsyncAnthropic:
    def __init__(self, recorder: dict[str, Any], usage: type | None = None) -> None:
        self.messages = _FakeMessages(
            recorder,
            usage or _usage(input_tokens=1000, output_tokens=200, cache_read_input_tokens=0),
        )


async def test_claude_forces_tool_and_caches_system() -> None:
    rec: dict[str, Any] = {}
    prov = ClaudeProvider(
        ProviderConfig(kind="claude", api_key="sk-x", model="claude-opus-4-7"),
        client=_FakeAsyncAnthropic(rec),
    )
    res = await prov.complete_json(
        system="extract brand", user="<corpus>", schema={"type": "object"}
    )
    assert res.data == {"name": "Acme Bank"}
    assert res.cost_usd > 0.0
    assert rec["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert rec["tool_choice"]["type"] == "tool"
    assert rec["model"] == "claude-opus-4-7"
    assert res.cache_creation_input_tokens == 0


async def test_claude_cost_includes_cache_creation_input_tokens() -> None:
    """A first/uncached extraction marks the system prompt as a cache write.
    Those tokens bill at ~1.25x the base input rate and must not be free.
    """
    base = _usage(input_tokens=1000, output_tokens=200, cache_read_input_tokens=0)
    with_write = _usage(
        input_tokens=1000,
        output_tokens=200,
        cache_read_input_tokens=0,
        cache_creation_input_tokens=800,
    )
    prov_base = ClaudeProvider(
        ProviderConfig(kind="claude", api_key="sk-x", model="claude-opus-4-7"),
        client=_FakeAsyncAnthropic({}, base),
    )
    prov_write = ClaudeProvider(
        ProviderConfig(kind="claude", api_key="sk-x", model="claude-opus-4-7"),
        client=_FakeAsyncAnthropic({}, with_write),
    )
    res_base = await prov_base.complete_json(system="s", user="u", schema={"type": "object"})
    res_write = await prov_write.complete_json(system="s", user="u", schema={"type": "object"})

    expected_delta = round(800 * _PRICE_CACHE_WRITE, 6)
    assert res_write.cache_creation_input_tokens == 800
    assert res_base.cache_creation_input_tokens == 0
    assert round(res_write.cost_usd - res_base.cost_usd, 6) == expected_delta
