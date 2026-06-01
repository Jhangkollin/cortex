"""Anthropic adapter. Forces structured output through a single tool call and
marks the system prompt as a cached (ephemeral) block so repeated extractions
re-use the prompt prefix cheaply.
"""

from __future__ import annotations

from typing import Any

from cortex_brand_extract.errors import UpstreamError, UpstreamTimeoutError
from cortex_brand_extract.llm.base import LLMResult
from cortex_brand_extract.types import ProviderConfig

# Rough public list-price blend (USD per token). Good enough for spike cost
# bounding; the eval harness records the real number.
_PRICE_IN = 15.0 / 1_000_000
_PRICE_OUT = 75.0 / 1_000_000
_PRICE_CACHE_READ = 1.5 / 1_000_000
# Anthropic bills 5-minute (ephemeral) cache *writes* at 1.25x base input.
# Derived from _PRICE_IN so the two stay consistent if the blend changes.
_PRICE_CACHE_WRITE = _PRICE_IN * 1.25


class ClaudeProvider:
    def __init__(self, config: ProviderConfig, *, client: Any | None = None) -> None:
        self._model = config.model
        if client is not None:
            self._client = client
        else:  # pragma: no cover - exercised only with the real SDK installed
            from anthropic import AsyncAnthropic

            self._client = AsyncAnthropic(api_key=config.api_key)

    @property
    def model(self) -> str:
        return self._model

    async def complete_json(self, *, system: str, user: str, schema: dict[str, Any]) -> LLMResult:
        tool = {
            "name": "emit_profile",
            "description": "Return the extracted structured data.",
            "input_schema": schema or {"type": "object"},
        }
        try:
            msg = await self._client.messages.create(
                model=self._model,
                max_tokens=4096,
                system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
                tools=[tool],
                tool_choice={"type": "tool", "name": "emit_profile"},
                messages=[{"role": "user", "content": user}],
            )
        except Exception as exc:  # noqa: BLE001 - normalize to typed errors
            name = type(exc).__name__.lower()
            if "timeout" in name:
                raise UpstreamTimeoutError(str(exc), stage="llm") from exc
            raise UpstreamError(str(exc), stage="llm") from exc

        data: dict[str, Any] | None = None
        for block in msg.content:
            if getattr(block, "type", None) == "tool_use":
                data = dict(block.input)
                break
        if data is None:
            raise UpstreamError("no tool_use block in response", stage="llm")

        u = msg.usage
        in_tok = getattr(u, "input_tokens", 0) or 0
        out_tok = getattr(u, "output_tokens", 0) or 0
        cache_read_tok = getattr(u, "cache_read_input_tokens", 0) or 0
        cache_write_tok = getattr(u, "cache_creation_input_tokens", 0) or 0
        cost = (
            in_tok * _PRICE_IN
            + out_tok * _PRICE_OUT
            + cache_read_tok * _PRICE_CACHE_READ
            + cache_write_tok * _PRICE_CACHE_WRITE
        )
        return LLMResult(
            data=data,
            cost_usd=round(cost, 6),
            input_tokens=in_tok,
            output_tokens=out_tok,
            cache_read_input_tokens=cache_read_tok,
            cache_creation_input_tokens=cache_write_tok,
        )
