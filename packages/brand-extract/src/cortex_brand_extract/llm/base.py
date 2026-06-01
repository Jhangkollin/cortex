"""Pluggable LLM provider. Adapters return parsed JSON conforming to a
caller-supplied JSON schema, plus a cost estimate. BYO-key: the caller
constructs the adapter from a ProviderConfig.
"""

from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel


class LLMResult(BaseModel):
    data: dict[str, Any]
    cost_usd: float = 0.0
    # Disjoint Anthropic-style token buckets, surfaced so the pipeline / eval
    # can attribute cost per stage. Adapters that have no notion of caching
    # (e.g. FakeProvider, OpenAI-compat) simply leave the cache buckets at 0.
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0


class LLMProvider(Protocol):
    @property
    def model(self) -> str: ...

    async def complete_json(
        self, *, system: str, user: str, schema: dict[str, Any]
    ) -> LLMResult: ...


class FakeProvider:
    """Deterministic test provider. `responses` are returned in order; an
    Exception entry is raised instead of returned.
    """

    def __init__(self, responses: list[dict[str, Any] | Exception]) -> None:
        self._responses = list(responses)
        self._i = 0
        self.model = "fake"

    async def complete_json(self, *, system: str, user: str, schema: dict[str, Any]) -> LLMResult:
        assert self._i < len(self._responses), "FakeProvider exhausted"
        item = self._responses[self._i]
        self._i += 1
        if isinstance(item, Exception):
            raise item
        return LLMResult(data=item, cost_usd=0.001)
