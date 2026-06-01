import json

import httpx
import pytest
import respx

from cortex_brand_extract.errors import UpstreamError
from cortex_brand_extract.llm.openai_compat import OpenAICompatProvider
from cortex_brand_extract.types import ProviderConfig


@respx.mock
async def test_openai_compat_posts_json_schema_and_parses() -> None:
    payload = {
        "choices": [{"message": {"content": json.dumps({"name": "Acme"})}}],
        "usage": {"prompt_tokens": 800, "completion_tokens": 100},
    }
    route = respx.post("https://llm.example/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=payload)
    )
    prov = OpenAICompatProvider(
        ProviderConfig(
            kind="openai_compat",
            api_key="k",
            model="gpt-x",
            base_url="https://llm.example/v1",
        )
    )
    res = await prov.complete_json(system="s", user="u", schema={"type": "object"})
    assert res.data == {"name": "Acme"}
    assert res.cost_usd >= 0.0
    sent = json.loads(route.calls.last.request.content)
    assert sent["model"] == "gpt-x"
    assert sent["response_format"]["type"] == "json_schema"


@respx.mock
async def test_openai_compat_wraps_non_json_2xx_as_upstream_error() -> None:
    respx.post("https://llm.example/v1/chat/completions").mock(
        return_value=httpx.Response(200, text="<html>not json</html>")
    )
    prov = OpenAICompatProvider(
        ProviderConfig(
            kind="openai_compat", api_key="k", model="gpt-x", base_url="https://llm.example/v1"
        )
    )
    with pytest.raises(UpstreamError):
        await prov.complete_json(system="s", user="u", schema={"type": "object"})
