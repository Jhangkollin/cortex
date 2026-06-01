"""OpenAI-compatible adapter. Covers BytePlus, Databricks-served, and any
chat-completions endpoint. Uses json_schema response_format for structured
output and validates by parsing the returned content.
"""

from __future__ import annotations

import json
from typing import Any

import httpx

from cortex_brand_extract.errors import UpstreamError, UpstreamTimeoutError
from cortex_brand_extract.llm.base import LLMResult
from cortex_brand_extract.types import ProviderConfig

_PRICE_IN = 0.5 / 1_000_000
_PRICE_OUT = 1.5 / 1_000_000


class OpenAICompatProvider:
    def __init__(self, config: ProviderConfig, *, timeout: float = 60.0) -> None:
        if not config.base_url:
            raise ValueError("openai_compat provider requires base_url")
        self._url = config.base_url.rstrip("/") + "/chat/completions"
        self._key = config.api_key
        self._model = config.model
        self._timeout = timeout

    @property
    def model(self) -> str:
        return self._model

    async def complete_json(self, *, system: str, user: str, schema: dict[str, Any]) -> LLMResult:
        body = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "brand_profile", "schema": schema or {"type": "object"}},
            },
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(
                    self._url,
                    headers={"Authorization": f"Bearer {self._key}"},
                    json=body,
                )
                resp.raise_for_status()
        except httpx.TimeoutException as exc:
            raise UpstreamTimeoutError(str(exc), stage="llm") from exc
        except httpx.HTTPError as exc:
            raise UpstreamError(str(exc), stage="llm") from exc

        try:
            doc = resp.json()
            content = doc["choices"][0]["message"]["content"]
            data = json.loads(content)
        except (KeyError, IndexError, json.JSONDecodeError) as exc:
            raise UpstreamError(f"bad LLM response: {exc}", stage="llm") from exc

        usage = doc.get("usage", {})
        cost = (
            usage.get("prompt_tokens", 0) * _PRICE_IN
            + usage.get("completion_tokens", 0) * _PRICE_OUT
        )
        return LLMResult(data=data, cost_usd=round(cost, 6))
