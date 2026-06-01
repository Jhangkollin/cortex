# Brand Extraction Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `cortex-brand-extract`, a standalone Python package that turns a brand URL into a structured `BrandProfile`, with a tiered fetcher, a pluggable BYO-key LLM, a staged extraction pipeline, and an MCP server façade.

**Architecture:** A pure library (no auth, no DB, no cortex imports). Deterministic fetch/crawl/parse builds a token-bounded site corpus; one structured-output LLM call synthesizes the profile; competitor and media match rank caller-supplied candidates. An MCP server wraps the same functions for external AI tools.

**Tech Stack:** Python 3.12, uv, pytest + pytest-asyncio, ruff, mypy, httpx, selectolax, pydantic v2, anthropic SDK, the `mcp` SDK (FastMCP); Playwright behind a `[render]` extra.

**Spec:** `docs/superpowers/specs/2026-05-18-brand-extraction-engine-design.md`

**Scope note:** This plan delivers SP-2 only — the standalone package. cortex-api wiring, persistence, GTM mode, and the one-pager are SP-1/SP-3/SP-4 and are out of scope. The package is built and tested standalone (`cd packages/brand-extract`), so the uv-workspace question does not block this plan.

---

## File Structure

All paths are under `packages/brand-extract/`.

| File | Responsibility |
|---|---|
| `pyproject.toml` | Package metadata, deps, extras (`render`, `mcp`), dev tooling |
| `src/cortex_brand_extract/__init__.py` | Public API surface + `__version__` |
| `src/cortex_brand_extract/types.py` | Frozen pydantic VOs incl. `BrandProfile` |
| `src/cortex_brand_extract/errors.py` | Typed errors (`ExtractError`, `UpstreamError`, `UpstreamTimeoutError`) |
| `src/cortex_brand_extract/progress.py` | `ProgressEvent`, `ProgressSink`, `ListSink` |
| `src/cortex_brand_extract/llm/base.py` | `LLMProvider` protocol + `FakeProvider` |
| `src/cortex_brand_extract/llm/claude.py` | Anthropic adapter (prompt-cached, tool-forced JSON) |
| `src/cortex_brand_extract/llm/openai_compat.py` | OpenAI-compatible adapter |
| `src/cortex_brand_extract/fetch/lite.py` | Static httpx fetch → `FetchedPage` |
| `src/cortex_brand_extract/fetch/detect.py` | JS-render heuristic |
| `src/cortex_brand_extract/fetch/deep.py` | Playwright render (guarded behind `[render]`) |
| `src/cortex_brand_extract/parse.py` | HTML → `SiteMetadata` |
| `src/cortex_brand_extract/crawl.py` | Link discovery + page selection |
| `src/cortex_brand_extract/corpus.py` | Token-bounded `SiteCorpus` assembly |
| `src/cortex_brand_extract/synthesize.py` | Corpus → profile core via `LLMProvider` |
| `src/cortex_brand_extract/match/competitors.py` | Rank caller-supplied competitor candidates |
| `src/cortex_brand_extract/match/media.py` | Rank caller-supplied media catalog |
| `src/cortex_brand_extract/pipeline.py` | `extract_brand_profile` orchestrator |
| `src/cortex_brand_extract/mcp/server.py` | FastMCP tools |
| `src/cortex_brand_extract/mcp/__main__.py` | `python -m cortex_brand_extract.mcp` entrypoint |
| `tests/...` | Mirrors `src/` |
| `tests/fixtures/` | Saved HTML for offline deterministic tests |
| `eval/run_eval.py` + `eval/README.md` | Manual eval harness + rubric |
| `README.md` | Install, usage, MCP, BYO-key, tiers |

---

## Task 0: Package scaffold

**Files:**
- Create: `packages/brand-extract/pyproject.toml`
- Create: `packages/brand-extract/src/cortex_brand_extract/__init__.py`
- Create: `packages/brand-extract/tests/test_smoke.py`

- [ ] **Step 1: Write the failing test**

Create `packages/brand-extract/tests/test_smoke.py`:

```python
import cortex_brand_extract


def test_package_exposes_version():
    assert isinstance(cortex_brand_extract.__version__, str)
    assert cortex_brand_extract.__version__
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/brand-extract && uv run pytest tests/test_smoke.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cortex_brand_extract'`

- [ ] **Step 3: Write minimal implementation**

Create `packages/brand-extract/pyproject.toml`:

```toml
[project]
name = "cortex-brand-extract"
version = "0.1.0"
description = "Turn a brand URL into a structured BrandProfile."
requires-python = ">=3.12"
dependencies = [
    "httpx>=0.27.0",
    "selectolax>=0.3.21",
    "pydantic>=2.7.0",
    "anthropic>=0.39.0",
]

[project.optional-dependencies]
render = ["playwright>=1.47.0"]
mcp = ["mcp>=1.2.0"]

[project.scripts]
cortex-brand-extract-mcp = "cortex_brand_extract.mcp.__main__:main"

[dependency-groups]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "respx>=0.21.0",
    "ruff>=0.6.0",
    "mypy>=1.11.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/cortex_brand_extract"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.mypy]
python_version = "3.12"
strict = true
```

Create `packages/brand-extract/src/cortex_brand_extract/__init__.py`:

```python
"""cortex-brand-extract — URL → structured BrandProfile.

Public API is re-exported here so callers and the MCP server import from
the package root. Stage functions are public for granular MCP tools/tests.
"""

from __future__ import annotations

__version__ = "0.1.0"

__all__ = ["__version__"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd packages/brand-extract && uv run pytest tests/test_smoke.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add packages/brand-extract/pyproject.toml packages/brand-extract/src/cortex_brand_extract/__init__.py packages/brand-extract/tests/test_smoke.py
git commit -m "feat(brand-extract): package scaffold"
```

---

## Task 1: Core types

**Files:**
- Create: `packages/brand-extract/src/cortex_brand_extract/types.py`
- Create: `packages/brand-extract/tests/test_types.py`

- [ ] **Step 1: Write the failing test**

Create `packages/brand-extract/tests/test_types.py`:

```python
import pytest
from pydantic import ValidationError

from cortex_brand_extract.types import (
    BrandProfile,
    Category,
    Competitor,
    ExtractionMeta,
    MediaMatch,
    MediaOutlet,
    Product,
    ProviderConfig,
    VoiceSample,
)


def _profile() -> BrandProfile:
    return BrandProfile(
        url="acmebank.asia",
        name="Acme Bank Asia",
        legal_name="Acme Bank Asia Holdings, Ltd.",
        tagline="Banking, redesigned for Asia.",
        monogram="A",
        brand_color="#225D59",
        category=Category(value="Retail banking", confidence=96, alternatives=["FinTech"]),
        region=["Taiwan"],
        founded="1998",
        about="27 years serving Asia.",
        voice_samples=[VoiceSample(src="/about", text="Banking should work for people.")],
        products=[Product(name="Smart Account", category="Deposits", url="/smart", confidence=97)],
        competitors=[Competitor(name="Cathay United", domain="cathaybk.com.tw", match_score=94)],
        media_matches=[MediaMatch(outlet_id="moneydj", name="MoneyDJ", relevance=94)],
        extraction_meta=ExtractionMeta(tier="lite", model="claude", cost_usd=0.03),
    )


def test_brand_profile_round_trips_to_dict():
    p = _profile()
    d = p.model_dump()
    assert d["name"] == "Acme Bank Asia"
    assert d["category"]["confidence"] == 96
    assert d["extraction_meta"]["tier"] == "lite"


def test_brand_profile_is_frozen():
    p = _profile()
    with pytest.raises(ValidationError):
        p.name = "Changed"


def test_provider_config_requires_kind_and_key():
    cfg = ProviderConfig(kind="claude", api_key="sk-x", model="claude-opus-4-7")
    assert cfg.kind == "claude"
    with pytest.raises(ValidationError):
        ProviderConfig(kind="bogus", api_key="x", model="m")  # type: ignore[arg-type]


def test_media_outlet_is_caller_input_shape():
    o = MediaOutlet(outlet_id="moneydj", name="MoneyDJ", audience="Investors", topics=["ETF"])
    assert o.outlet_id == "moneydj"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/brand-extract && uv run pytest tests/test_types.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cortex_brand_extract.types'`

- [ ] **Step 3: Write minimal implementation**

Create `packages/brand-extract/src/cortex_brand_extract/types.py`:

```python
"""Frozen value objects. Field names mirror the web `ExtractedBrand` TS type
(web/src/components/onboarding-v2/data.ts) so the wizard consumes results with
no translation layer. These are NOT SQLModel — persistence mapping is SP-1.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ExtractTier = Literal["lite", "deep"]
ProviderKind = Literal["claude", "openai_compat"]


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True)


class ProviderConfig(_Frozen):
    kind: ProviderKind
    api_key: str
    model: str
    base_url: str | None = None


class MediaOutlet(_Frozen):
    """Caller-supplied media catalog entry (input to media match)."""

    outlet_id: str
    name: str
    audience: str | None = None
    topics: list[str] = Field(default_factory=list)


class CompetitorCandidate(_Frozen):
    """Caller-supplied competitor candidate (input to competitor match)."""

    name: str
    domain: str | None = None


class Category(_Frozen):
    value: str
    confidence: int = Field(ge=0, le=100)
    alternatives: list[str] = Field(default_factory=list)


class VoiceSample(_Frozen):
    src: str
    text: str


class Product(_Frozen):
    name: str
    category: str
    url: str | None = None
    confidence: int = Field(default=0, ge=0, le=100)


class Competitor(_Frozen):
    name: str
    domain: str | None = None
    match_score: int = Field(default=0, ge=0, le=100)


class MediaMatch(_Frozen):
    outlet_id: str
    name: str
    relevance: int = Field(default=0, ge=0, le=100)


class ExtractionMeta(_Frozen):
    tier: ExtractTier
    model: str
    cost_usd: float = 0.0
    js_detected: bool = False
    warnings: list[str] = Field(default_factory=list)
    extracted_at: datetime = Field(default_factory=datetime.utcnow)


class BrandProfile(_Frozen):
    url: str
    name: str
    legal_name: str | None = None
    tagline: str | None = None
    monogram: str | None = None
    brand_color: str | None = None
    category: Category
    region: list[str] = Field(default_factory=list)
    founded: str | None = None
    about: str | None = None
    voice_samples: list[VoiceSample] = Field(default_factory=list)
    products: list[Product] = Field(default_factory=list)
    competitors: list[Competitor] = Field(default_factory=list)
    media_matches: list[MediaMatch] = Field(default_factory=list)
    extraction_meta: ExtractionMeta
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd packages/brand-extract && uv run pytest tests/test_types.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add packages/brand-extract/src/cortex_brand_extract/types.py packages/brand-extract/tests/test_types.py
git commit -m "feat(brand-extract): core frozen value objects"
```

---

## Task 2: Typed errors

**Files:**
- Create: `packages/brand-extract/src/cortex_brand_extract/errors.py`
- Create: `packages/brand-extract/tests/test_errors.py`

- [ ] **Step 1: Write the failing test**

Create `packages/brand-extract/tests/test_errors.py`:

```python
from cortex_brand_extract.errors import (
    ExtractError,
    UpstreamError,
    UpstreamTimeoutError,
)


def test_hierarchy():
    assert issubclass(UpstreamError, ExtractError)
    assert issubclass(UpstreamTimeoutError, UpstreamError)


def test_carries_message_and_chains():
    cause = ValueError("boom")
    err = UpstreamError("llm failed", stage="synthesize")
    err.__cause__ = cause
    assert err.stage == "synthesize"
    assert "llm failed" in str(err)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/brand-extract && uv run pytest tests/test_errors.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cortex_brand_extract.errors'`

- [ ] **Step 3: Write minimal implementation**

Create `packages/brand-extract/src/cortex_brand_extract/errors.py`:

```python
"""Typed errors. Mirrors agent-will-smith's UpstreamError/UpstreamTimeoutError
naming so cortex-api error handling stays consistent when it consumes the lib.
"""

from __future__ import annotations


class ExtractError(Exception):
    """Base for all extraction failures."""

    def __init__(self, message: str, *, stage: str | None = None) -> None:
        super().__init__(message)
        self.stage = stage


class UpstreamError(ExtractError):
    """An upstream dependency (LLM, network) failed."""


class UpstreamTimeoutError(UpstreamError):
    """An upstream dependency timed out."""
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd packages/brand-extract && uv run pytest tests/test_errors.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add packages/brand-extract/src/cortex_brand_extract/errors.py packages/brand-extract/tests/test_errors.py
git commit -m "feat(brand-extract): typed errors"
```

---

## Task 3: Progress events

**Files:**
- Create: `packages/brand-extract/src/cortex_brand_extract/progress.py`
- Create: `packages/brand-extract/tests/test_progress.py`

- [ ] **Step 1: Write the failing test**

Create `packages/brand-extract/tests/test_progress.py`:

```python
from cortex_brand_extract.progress import ListSink, ProgressEvent


async def test_list_sink_collects_events():
    sink = ListSink()
    await sink.emit(ProgressEvent(stage="fetch", status="running", detail="acme.com"))
    await sink.emit(ProgressEvent(stage="fetch", status="ok", detail="200"))
    assert [e.status for e in sink.events] == ["running", "ok"]
    assert sink.events[0].stage == "fetch"


async def test_none_safe_emit_helper():
    from cortex_brand_extract.progress import emit

    await emit(None, ProgressEvent(stage="parse", status="ok"))  # no raise
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/brand-extract && uv run pytest tests/test_progress.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cortex_brand_extract.progress'`

- [ ] **Step 3: Write minimal implementation**

Create `packages/brand-extract/src/cortex_brand_extract/progress.py`:

```python
"""Progress reporting. A ProgressSink is any object with `async emit(event)`.
The pipeline emits one or more events per stage; the MCP server maps them to
MCP progress notifications.
"""

from __future__ import annotations

from typing import Literal, Protocol

from pydantic import BaseModel

StageStatus = Literal["running", "ok", "warn", "error"]


class ProgressEvent(BaseModel):
    stage: str
    status: StageStatus
    detail: str = ""


class ProgressSink(Protocol):
    async def emit(self, event: ProgressEvent) -> None: ...


class ListSink:
    """Test/in-memory sink."""

    def __init__(self) -> None:
        self.events: list[ProgressEvent] = []

    async def emit(self, event: ProgressEvent) -> None:
        self.events.append(event)


async def emit(sink: ProgressSink | None, event: ProgressEvent) -> None:
    """None-safe emit so call sites stay terse."""
    if sink is not None:
        await sink.emit(event)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd packages/brand-extract && uv run pytest tests/test_progress.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add packages/brand-extract/src/cortex_brand_extract/progress.py packages/brand-extract/tests/test_progress.py
git commit -m "feat(brand-extract): progress events + sink"
```

---

## Task 4: LLM provider protocol + fake

**Files:**
- Create: `packages/brand-extract/src/cortex_brand_extract/llm/__init__.py`
- Create: `packages/brand-extract/src/cortex_brand_extract/llm/base.py`
- Create: `packages/brand-extract/tests/test_llm_base.py`

- [ ] **Step 1: Write the failing test**

Create `packages/brand-extract/tests/test_llm_base.py`:

```python
import pytest

from cortex_brand_extract.errors import UpstreamError
from cortex_brand_extract.llm.base import FakeProvider, LLMResult


async def test_fake_provider_returns_scripted_json():
    fake = FakeProvider(responses=[{"name": "Acme"}])
    res = await fake.complete_json(system="s", user="u", schema={"type": "object"})
    assert isinstance(res, LLMResult)
    assert res.data == {"name": "Acme"}
    assert res.cost_usd >= 0.0


async def test_fake_provider_raises_when_scripted():
    fake = FakeProvider(responses=[UpstreamError("forced")])
    with pytest.raises(UpstreamError):
        await fake.complete_json(system="s", user="u", schema={"type": "object"})


async def test_fake_provider_exhaustion_raises():
    fake = FakeProvider(responses=[{"a": 1}])
    await fake.complete_json(system="s", user="u", schema={})
    with pytest.raises(AssertionError):
        await fake.complete_json(system="s", user="u", schema={})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/brand-extract && uv run pytest tests/test_llm_base.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cortex_brand_extract.llm'`

- [ ] **Step 3: Write minimal implementation**

Create `packages/brand-extract/src/cortex_brand_extract/llm/__init__.py`:

```python
"""LLM provider protocol and adapters."""
```

Create `packages/brand-extract/src/cortex_brand_extract/llm/base.py`:

```python
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


class LLMProvider(Protocol):
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

    async def complete_json(
        self, *, system: str, user: str, schema: dict[str, Any]
    ) -> LLMResult:
        assert self._i < len(self._responses), "FakeProvider exhausted"
        item = self._responses[self._i]
        self._i += 1
        if isinstance(item, Exception):
            raise item
        return LLMResult(data=item, cost_usd=0.001)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd packages/brand-extract && uv run pytest tests/test_llm_base.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add packages/brand-extract/src/cortex_brand_extract/llm/ packages/brand-extract/tests/test_llm_base.py
git commit -m "feat(brand-extract): LLM provider protocol + fake"
```

---

## Task 5: Claude adapter

**Files:**
- Create: `packages/brand-extract/src/cortex_brand_extract/llm/claude.py`
- Create: `packages/brand-extract/tests/test_llm_claude.py`

- [ ] **Step 1: Write the failing test**

Create `packages/brand-extract/tests/test_llm_claude.py`:

```python
from typing import Any

from cortex_brand_extract.llm.claude import ClaudeProvider
from cortex_brand_extract.types import ProviderConfig


class _FakeMessages:
    def __init__(self, recorder: dict[str, Any]) -> None:
        self._rec = recorder

    async def create(self, **kwargs: Any) -> Any:
        self._rec.update(kwargs)

        class _Block:
            type = "tool_use"
            input = {"name": "Acme Bank"}

        class _Usage:
            input_tokens = 1000
            output_tokens = 200
            cache_read_input_tokens = 0

        class _Msg:
            content = [_Block()]
            usage = _Usage()

        return _Msg()


class _FakeAsyncAnthropic:
    def __init__(self, recorder: dict[str, Any]) -> None:
        self.messages = _FakeMessages(recorder)


async def test_claude_forces_tool_and_caches_system():
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
    # system prompt is sent as a cached block
    assert rec["system"][0]["cache_control"] == {"type": "ephemeral"}
    # structured output is forced via a single tool
    assert rec["tool_choice"]["type"] == "tool"
    assert rec["model"] == "claude-opus-4-7"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/brand-extract && uv run pytest tests/test_llm_claude.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cortex_brand_extract.llm.claude'`

- [ ] **Step 3: Write minimal implementation**

Create `packages/brand-extract/src/cortex_brand_extract/llm/claude.py`:

```python
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


class ClaudeProvider:
    def __init__(self, config: ProviderConfig, *, client: Any | None = None) -> None:
        self._model = config.model
        if client is not None:
            self._client = client
        else:  # pragma: no cover - exercised only with the real SDK installed
            from anthropic import AsyncAnthropic

            self._client = AsyncAnthropic(api_key=config.api_key)

    async def complete_json(
        self, *, system: str, user: str, schema: dict[str, Any]
    ) -> LLMResult:
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
        cost = (
            getattr(u, "input_tokens", 0) * _PRICE_IN
            + getattr(u, "output_tokens", 0) * _PRICE_OUT
            + getattr(u, "cache_read_input_tokens", 0) * _PRICE_CACHE_READ
        )
        return LLMResult(data=data, cost_usd=round(cost, 6))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd packages/brand-extract && uv run pytest tests/test_llm_claude.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add packages/brand-extract/src/cortex_brand_extract/llm/claude.py packages/brand-extract/tests/test_llm_claude.py
git commit -m "feat(brand-extract): Claude adapter (cached system, forced tool)"
```

---

## Task 6: OpenAI-compatible adapter

**Files:**
- Create: `packages/brand-extract/src/cortex_brand_extract/llm/openai_compat.py`
- Create: `packages/brand-extract/tests/test_llm_openai_compat.py`

- [ ] **Step 1: Write the failing test**

Create `packages/brand-extract/tests/test_llm_openai_compat.py`:

```python
import json

import httpx
import respx

from cortex_brand_extract.llm.openai_compat import OpenAICompatProvider
from cortex_brand_extract.types import ProviderConfig


@respx.mock
async def test_openai_compat_posts_json_schema_and_parses():
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/brand-extract && uv run pytest tests/test_llm_openai_compat.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cortex_brand_extract.llm.openai_compat'`

- [ ] **Step 3: Write minimal implementation**

Create `packages/brand-extract/src/cortex_brand_extract/llm/openai_compat.py`:

```python
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

    async def complete_json(
        self, *, system: str, user: str, schema: dict[str, Any]
    ) -> LLMResult:
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

        doc = resp.json()
        try:
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd packages/brand-extract && uv run pytest tests/test_llm_openai_compat.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add packages/brand-extract/src/cortex_brand_extract/llm/openai_compat.py packages/brand-extract/tests/test_llm_openai_compat.py
git commit -m "feat(brand-extract): OpenAI-compatible adapter"
```

---

## Task 7: Static fetch (lite tier)

**Files:**
- Create: `packages/brand-extract/src/cortex_brand_extract/fetch/__init__.py`
- Create: `packages/brand-extract/src/cortex_brand_extract/fetch/lite.py`
- Create: `packages/brand-extract/tests/test_fetch_lite.py`

- [ ] **Step 1: Write the failing test**

Create `packages/brand-extract/tests/test_fetch_lite.py`:

```python
import httpx
import respx

from cortex_brand_extract.fetch.lite import FetchedPage, fetch_lite


@respx.mock
async def test_fetch_lite_normalizes_url_and_returns_page():
    respx.get("https://acmebank.asia/").mock(
        return_value=httpx.Response(200, html="<html><body>hi</body></html>")
    )
    page = await fetch_lite("acmebank.asia")
    assert isinstance(page, FetchedPage)
    assert page.status == 200
    assert page.final_url == "https://acmebank.asia/"
    assert "hi" in page.html


@respx.mock
async def test_fetch_lite_records_non_200_without_raising():
    respx.get("https://acmebank.asia/missing").mock(return_value=httpx.Response(404))
    page = await fetch_lite("https://acmebank.asia/missing")
    assert page.status == 404
    assert page.html == ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/brand-extract && uv run pytest tests/test_fetch_lite.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cortex_brand_extract.fetch'`

- [ ] **Step 3: Write minimal implementation**

Create `packages/brand-extract/src/cortex_brand_extract/fetch/__init__.py`:

```python
"""Tiered fetch: lite (static) and deep (rendered)."""
```

Create `packages/brand-extract/src/cortex_brand_extract/fetch/lite.py`:

```python
"""Static fetch. No browser. Adds scheme if missing, follows redirects,
records non-2xx without raising so the pipeline can degrade per-page.
"""

from __future__ import annotations

from datetime import datetime

import httpx
from pydantic import BaseModel

_UA = "cortex-brand-extract/0.1 (+https://github.com/mlytics/cortex)"


class FetchedPage(BaseModel):
    requested_url: str
    final_url: str
    status: int
    html: str
    fetched_at: datetime


def _normalize(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        return "https://" + url
    return url


async def fetch_lite(url: str, *, timeout: float = 15.0) -> FetchedPage:
    target = _normalize(url)
    async with httpx.AsyncClient(
        timeout=timeout, follow_redirects=True, headers={"User-Agent": _UA}
    ) as client:
        try:
            resp = await client.get(target)
        except httpx.HTTPError:
            return FetchedPage(
                requested_url=target,
                final_url=target,
                status=0,
                html="",
                fetched_at=datetime.utcnow(),
            )
    html = resp.text if resp.status_code == 200 else ""
    return FetchedPage(
        requested_url=target,
        final_url=str(resp.url),
        status=resp.status_code,
        html=html,
        fetched_at=datetime.utcnow(),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd packages/brand-extract && uv run pytest tests/test_fetch_lite.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add packages/brand-extract/src/cortex_brand_extract/fetch/ packages/brand-extract/tests/test_fetch_lite.py
git commit -m "feat(brand-extract): lite static fetch"
```

---

## Task 8: JS-render detection

**Files:**
- Create: `packages/brand-extract/src/cortex_brand_extract/fetch/detect.py`
- Create: `packages/brand-extract/tests/test_fetch_detect.py`

- [ ] **Step 1: Write the failing test**

Create `packages/brand-extract/tests/test_fetch_detect.py`:

```python
from cortex_brand_extract.fetch.detect import looks_js_rendered

_RICH = "<html><body>" + "<p>Acme Bank serves millions across Asia.</p>" * 40 + "</body></html>"
_SPA = '<html><body><div id="root"></div><script src="/app.js"></script></body></html>'


def test_rich_static_page_is_not_flagged():
    flagged, _ = looks_js_rendered(_RICH)
    assert flagged is False


def test_spa_shell_is_flagged():
    flagged, reason = looks_js_rendered(_SPA)
    assert flagged is True
    assert reason
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/brand-extract && uv run pytest tests/test_fetch_detect.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cortex_brand_extract.fetch.detect'`

- [ ] **Step 3: Write minimal implementation**

Create `packages/brand-extract/src/cortex_brand_extract/fetch/detect.py`:

```python
"""Heuristic: does this HTML look like an unrendered SPA shell? Used to set
`js_detected` and recommend the deep tier — never to silently return garbage.
"""

from __future__ import annotations

from selectolax.parser import HTMLParser

_MIN_VISIBLE_CHARS = 200


def looks_js_rendered(html: str) -> tuple[bool, str]:
    if not html.strip():
        return True, "empty response body"
    tree = HTMLParser(html)
    body = tree.body
    text = (body.text(separator=" ", strip=True) if body else "").strip()
    if len(text) < _MIN_VISIBLE_CHARS:
        scripts = len(tree.css("script"))
        return True, f"only {len(text)} visible chars with {scripts} script tags"
    return False, ""
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd packages/brand-extract && uv run pytest tests/test_fetch_detect.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add packages/brand-extract/src/cortex_brand_extract/fetch/detect.py packages/brand-extract/tests/test_fetch_detect.py
git commit -m "feat(brand-extract): JS-render heuristic"
```

---

## Task 9: Deep fetch (render tier, guarded)

**Files:**
- Create: `packages/brand-extract/src/cortex_brand_extract/fetch/deep.py`
- Create: `packages/brand-extract/tests/test_fetch_deep.py`

- [ ] **Step 1: Write the failing test**

Create `packages/brand-extract/tests/test_fetch_deep.py`:

```python
import builtins

import pytest

from cortex_brand_extract.fetch.deep import fetch_deep


async def test_fetch_deep_raises_clear_error_when_render_extra_missing(monkeypatch):
    real_import = builtins.__import__

    def _block(name, *args, **kwargs):
        if name.startswith("playwright"):
            raise ModuleNotFoundError("No module named 'playwright'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _block)
    with pytest.raises(RuntimeError, match=r"pip install .*\[render\]"):
        await fetch_deep("https://acmebank.asia")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/brand-extract && uv run pytest tests/test_fetch_deep.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cortex_brand_extract.fetch.deep'`

- [ ] **Step 3: Write minimal implementation**

Create `packages/brand-extract/src/cortex_brand_extract/fetch/deep.py`:

```python
"""Deep fetch via Playwright. Import-guarded: Playwright ships only with the
`[render]` extra, so a missing import yields an actionable error rather than a
bare ModuleNotFoundError.
"""

from __future__ import annotations

from datetime import datetime

from cortex_brand_extract.fetch.lite import FetchedPage

_UA = "cortex-brand-extract/0.1 (+https://github.com/mlytics/cortex)"


async def fetch_deep(url: str, *, timeout: float = 30.0) -> FetchedPage:
    try:
        from playwright.async_api import async_playwright
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "deep tier needs Playwright. Install with: "
            "pip install 'cortex-brand-extract[render]' && playwright install chromium"
        ) from exc

    target = url if url.startswith(("http://", "https://")) else "https://" + url
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            page = await browser.new_page(user_agent=_UA)
            resp = await page.goto(target, wait_until="networkidle", timeout=timeout * 1000)
            html = await page.content()
            status = resp.status if resp else 0
            final_url = page.url
        finally:
            await browser.close()
    return FetchedPage(
        requested_url=target,
        final_url=final_url,
        status=status,
        html=html if status == 200 else "",
        fetched_at=datetime.utcnow(),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd packages/brand-extract && uv run pytest tests/test_fetch_deep.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add packages/brand-extract/src/cortex_brand_extract/fetch/deep.py packages/brand-extract/tests/test_fetch_deep.py
git commit -m "feat(brand-extract): deep render fetch (guarded)"
```

---

## Task 10: Parse metadata

**Files:**
- Create: `packages/brand-extract/src/cortex_brand_extract/parse.py`
- Create: `packages/brand-extract/tests/fixtures/acme_home.html`
- Create: `packages/brand-extract/tests/test_parse.py`

- [ ] **Step 1: Write the failing test**

Create `packages/brand-extract/tests/fixtures/acme_home.html`:

```html
<!DOCTYPE html>
<html>
<head>
  <title>Acme Bank Asia — Banking, redesigned for Asia.</title>
  <meta name="description" content="27 years serving 3.2M households across Asia." />
  <meta property="og:title" content="Acme Bank Asia" />
  <meta property="og:image" content="https://acmebank.asia/logo.png" />
  <meta name="theme-color" content="#225D59" />
  <link rel="icon" href="/favicon.ico" />
  <script type="application/ld+json">
  {"@type":"Organization","name":"Acme Bank Asia Holdings, Ltd.","foundingDate":"1998"}
  </script>
</head>
<body>
  <a href="/about">About</a>
  <a href="/credit-cards/world-elite">World Elite Card</a>
  <a href="https://twitter.com/acme">Twitter</a>
  <p>Banking should work for people, not the other way around.</p>
</body>
</html>
```

Create `packages/brand-extract/tests/test_parse.py`:

```python
from pathlib import Path

from cortex_brand_extract.parse import SiteMetadata, parse_site

_HTML = (Path(__file__).parent / "fixtures" / "acme_home.html").read_text()


def test_parse_extracts_core_metadata():
    md = parse_site("https://acmebank.asia/", _HTML)
    assert isinstance(md, SiteMetadata)
    assert md.title.startswith("Acme Bank Asia")
    assert md.description and "3.2M households" in md.description
    assert md.og_image == "https://acmebank.asia/logo.png"
    assert md.theme_color == "#225D59"
    assert md.favicon == "https://acmebank.asia/favicon.ico"
    assert md.jsonld_org_name == "Acme Bank Asia Holdings, Ltd."
    assert md.founded == "1998"


def test_parse_collects_internal_links_only():
    md = parse_site("https://acmebank.asia/", _HTML)
    assert "https://acmebank.asia/about" in md.internal_links
    assert "https://acmebank.asia/credit-cards/world-elite" in md.internal_links
    assert all("twitter.com" not in link for link in md.internal_links)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/brand-extract && uv run pytest tests/test_parse.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cortex_brand_extract.parse'`

- [ ] **Step 3: Write minimal implementation**

Create `packages/brand-extract/src/cortex_brand_extract/parse.py`:

```python
"""HTML → SiteMetadata. Pure: takes the base URL and HTML string, returns
structured metadata plus same-host internal links for the crawler.
"""

from __future__ import annotations

import json
from urllib.parse import urljoin, urlparse

from pydantic import BaseModel
from selectolax.parser import HTMLParser


class SiteMetadata(BaseModel):
    base_url: str
    title: str = ""
    description: str | None = None
    og_title: str | None = None
    og_image: str | None = None
    theme_color: str | None = None
    favicon: str | None = None
    jsonld_org_name: str | None = None
    founded: str | None = None
    internal_links: list[str] = []
    visible_text: str = ""


def _meta(tree: HTMLParser, *, name: str | None = None, prop: str | None = None) -> str | None:
    sel = f'meta[name="{name}"]' if name else f'meta[property="{prop}"]'
    node = tree.css_first(sel)
    return node.attributes.get("content") if node else None


def parse_site(base_url: str, html: str) -> SiteMetadata:
    tree = HTMLParser(html or "")
    host = urlparse(base_url).netloc

    title_node = tree.css_first("title")
    title = title_node.text(strip=True) if title_node else ""

    favicon = None
    icon = tree.css_first('link[rel~="icon"]')
    if icon and icon.attributes.get("href"):
        favicon = urljoin(base_url, icon.attributes["href"])

    org_name = None
    founded = None
    for node in tree.css('script[type="application/ld+json"]'):
        try:
            doc = json.loads(node.text() or "{}")
        except json.JSONDecodeError:
            continue
        entries = doc if isinstance(doc, list) else [doc]
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            if entry.get("name") and org_name is None:
                org_name = entry["name"]
            if entry.get("foundingDate") and founded is None:
                founded = str(entry["foundingDate"])[:4]

    links: list[str] = []
    seen: set[str] = set()
    for a in tree.css("a[href]"):
        href = a.attributes.get("href") or ""
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        absolute = urljoin(base_url, href)
        if urlparse(absolute).netloc != host:
            continue
        clean = absolute.split("#")[0]
        if clean not in seen:
            seen.add(clean)
            links.append(clean)

    body = tree.body
    visible = body.text(separator=" ", strip=True) if body else ""

    return SiteMetadata(
        base_url=base_url,
        title=title,
        description=_meta(tree, name="description"),
        og_title=_meta(tree, prop="og:title"),
        og_image=_meta(tree, prop="og:image"),
        theme_color=_meta(tree, name="theme-color"),
        favicon=favicon,
        jsonld_org_name=org_name,
        founded=founded,
        internal_links=links,
        visible_text=visible,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd packages/brand-extract && uv run pytest tests/test_parse.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add packages/brand-extract/src/cortex_brand_extract/parse.py packages/brand-extract/tests/fixtures/acme_home.html packages/brand-extract/tests/test_parse.py
git commit -m "feat(brand-extract): HTML metadata parser"
```

---

## Task 11: Crawl / page selection

**Files:**
- Create: `packages/brand-extract/src/cortex_brand_extract/crawl.py`
- Create: `packages/brand-extract/tests/test_crawl.py`

- [ ] **Step 1: Write the failing test**

Create `packages/brand-extract/tests/test_crawl.py`:

```python
from cortex_brand_extract.crawl import select_pages


def test_select_prioritizes_high_signal_paths_and_bounds_count():
    links = [
        "https://acme.com/about",
        "https://acme.com/products/card",
        "https://acme.com/press/2025",
        "https://acme.com/careers/intern",
        "https://acme.com/legal/cookies",
        "https://acme.com/pricing",
        "https://acme.com/blog/post-1",
    ]
    chosen = select_pages("https://acme.com/", links, max_pages=4)
    assert "https://acme.com/about" in chosen
    assert "https://acme.com/products/card" in chosen
    assert "https://acme.com/pricing" in chosen
    assert len(chosen) == 4
    assert "https://acme.com/legal/cookies" not in chosen


def test_homepage_always_first():
    chosen = select_pages("https://acme.com/", ["https://acme.com/about"], max_pages=3)
    assert chosen[0] == "https://acme.com/"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/brand-extract && uv run pytest tests/test_crawl.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cortex_brand_extract.crawl'`

- [ ] **Step 3: Write minimal implementation**

Create `packages/brand-extract/src/cortex_brand_extract/crawl.py`:

```python
"""Deterministic page selection. Scores internal links by path keywords and
returns the homepage plus the top-scoring pages, bounded by max_pages.
"""

from __future__ import annotations

from urllib.parse import urlparse

_HIGH = ("about", "product", "products", "pricing", "press", "solutions", "company")
_MED = ("blog", "news", "investor", "services")
_SKIP = ("careers", "legal", "privacy", "cookie", "terms", "login", "signin")


def _score(url: str) -> int:
    path = urlparse(url).path.lower()
    if any(s in path for s in _SKIP):
        return -1
    if any(h in path for h in _HIGH):
        return 3
    if any(m in path for m in _MED):
        return 2
    depth = path.strip("/").count("/")
    return 1 if depth <= 1 else 0


def select_pages(homepage: str, internal_links: list[str], *, max_pages: int) -> list[str]:
    ranked = sorted(
        (u for u in internal_links if u.rstrip("/") != homepage.rstrip("/")),
        key=_score,
        reverse=True,
    )
    keep = [u for u in ranked if _score(u) >= 0][: max(0, max_pages - 1)]
    return [homepage, *keep]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd packages/brand-extract && uv run pytest tests/test_crawl.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add packages/brand-extract/src/cortex_brand_extract/crawl.py packages/brand-extract/tests/test_crawl.py
git commit -m "feat(brand-extract): deterministic page selection"
```

---

## Task 12: Corpus assembly

**Files:**
- Create: `packages/brand-extract/src/cortex_brand_extract/corpus.py`
- Create: `packages/brand-extract/tests/test_corpus.py`

- [ ] **Step 1: Write the failing test**

Create `packages/brand-extract/tests/test_corpus.py`:

```python
from cortex_brand_extract.corpus import SiteCorpus, build_corpus


def test_corpus_concatenates_pages_and_bounds_chars():
    pages = [
        ("https://acme.com/", "Acme home " * 50),
        ("https://acme.com/about", "About Acme " * 50),
    ]
    corpus = build_corpus(pages, max_chars=120)
    assert isinstance(corpus, SiteCorpus)
    assert len(corpus.text) <= 120 + 80  # bound + per-page header allowance
    assert "https://acme.com/" in corpus.text
    assert corpus.page_count == 2
    assert corpus.truncated is True


def test_corpus_not_truncated_when_small():
    corpus = build_corpus([("https://acme.com/", "short")], max_chars=10_000)
    assert corpus.truncated is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/brand-extract && uv run pytest tests/test_corpus.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cortex_brand_extract.corpus'`

- [ ] **Step 3: Write minimal implementation**

Create `packages/brand-extract/src/cortex_brand_extract/corpus.py`:

```python
"""Token-bounded corpus. The spike uses a char budget (≈ chars/4 tokens) to
stay pip-light — no tiktoken. The eval harness records real token usage.
"""

from __future__ import annotations

from pydantic import BaseModel


class SiteCorpus(BaseModel):
    text: str
    page_count: int
    truncated: bool


def build_corpus(pages: list[tuple[str, str]], *, max_chars: int = 60_000) -> SiteCorpus:
    chunks: list[str] = []
    total = 0
    truncated = False
    for url, body in pages:
        header = f"\n\n=== PAGE: {url} ===\n"
        remaining = max_chars - total
        if remaining <= 0:
            truncated = True
            break
        piece = (header + body)[:remaining]
        if len(header + body) > remaining:
            truncated = True
        chunks.append(piece)
        total += len(piece)
    return SiteCorpus(
        text="".join(chunks).strip(),
        page_count=len(pages),
        truncated=truncated,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd packages/brand-extract && uv run pytest tests/test_corpus.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add packages/brand-extract/src/cortex_brand_extract/corpus.py packages/brand-extract/tests/test_corpus.py
git commit -m "feat(brand-extract): token-bounded corpus assembly"
```

---

## Task 13: Synthesis

**Files:**
- Create: `packages/brand-extract/src/cortex_brand_extract/synthesize.py`
- Create: `packages/brand-extract/tests/test_synthesize.py`

- [ ] **Step 1: Write the failing test**

Create `packages/brand-extract/tests/test_synthesize.py`:

```python
import pytest

from cortex_brand_extract.corpus import SiteCorpus
from cortex_brand_extract.errors import UpstreamError
from cortex_brand_extract.llm.base import FakeProvider
from cortex_brand_extract.parse import SiteMetadata
from cortex_brand_extract.synthesize import synthesize_profile

_GOOD = {
    "name": "Acme Bank Asia",
    "tagline": "Banking, redesigned for Asia.",
    "category": {"value": "Retail banking", "confidence": 95, "alternatives": ["FinTech"]},
    "about": "27 years across Asia.",
    "region": ["Taiwan"],
    "voice_samples": [{"src": "/about", "text": "Banking should work for people."}],
    "products": [{"name": "Smart Account", "category": "Deposits", "url": "/smart", "confidence": 96}],
}

_META = SiteMetadata(base_url="https://acmebank.asia/", title="Acme Bank Asia")
_CORPUS = SiteCorpus(text="Acme Bank Asia ...", page_count=1, truncated=False)


async def test_synthesis_maps_llm_output_into_profile_core():
    prov = FakeProvider(responses=[_GOOD])
    core = await synthesize_profile(prov, _META, _CORPUS)
    assert core.name == "Acme Bank Asia"
    assert core.category.confidence == 95
    assert core.products[0].name == "Smart Account"
    assert core.cost_usd > 0.0


async def test_synthesis_repairs_once_then_succeeds():
    prov = FakeProvider(responses=[{"bogus": True}, _GOOD])
    core = await synthesize_profile(prov, _META, _CORPUS)
    assert core.name == "Acme Bank Asia"


async def test_synthesis_raises_after_failed_repair():
    prov = FakeProvider(responses=[{"bogus": True}, {"still": "bad"}])
    with pytest.raises(UpstreamError):
        await synthesize_profile(prov, _META, _CORPUS)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/brand-extract && uv run pytest tests/test_synthesize.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cortex_brand_extract.synthesize'`

- [ ] **Step 3: Write minimal implementation**

Create `packages/brand-extract/src/cortex_brand_extract/synthesize.py`:

```python
"""One structured-output call: SiteCorpus + SiteMetadata → profile core
(name/tagline/category/about/voice/products). One repair retry on invalid
output, then a typed error.
"""

from __future__ import annotations

from pydantic import BaseModel, ValidationError

from cortex_brand_extract.corpus import SiteCorpus
from cortex_brand_extract.errors import UpstreamError
from cortex_brand_extract.llm.base import LLMProvider
from cortex_brand_extract.parse import SiteMetadata
from cortex_brand_extract.types import Category, Product, VoiceSample

_SYSTEM = (
    "You extract a brand profile from a company's own website text. "
    "Return only facts grounded in the provided pages. Do not invent "
    "competitors or products. If unsure, lower the confidence."
)

_SCHEMA = {
    "type": "object",
    "required": ["name", "category", "about"],
    "properties": {
        "name": {"type": "string"},
        "legal_name": {"type": "string"},
        "tagline": {"type": "string"},
        "monogram": {"type": "string"},
        "brand_color": {"type": "string"},
        "founded": {"type": "string"},
        "about": {"type": "string"},
        "region": {"type": "array", "items": {"type": "string"}},
        "category": {
            "type": "object",
            "required": ["value", "confidence"],
            "properties": {
                "value": {"type": "string"},
                "confidence": {"type": "integer"},
                "alternatives": {"type": "array", "items": {"type": "string"}},
            },
        },
        "voice_samples": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"src": {"type": "string"}, "text": {"type": "string"}},
            },
        },
        "products": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "category": {"type": "string"},
                    "url": {"type": "string"},
                    "confidence": {"type": "integer"},
                },
            },
        },
    },
}


class ProfileCore(BaseModel):
    name: str
    legal_name: str | None = None
    tagline: str | None = None
    monogram: str | None = None
    brand_color: str | None = None
    founded: str | None = None
    about: str
    region: list[str] = []
    category: Category
    voice_samples: list[VoiceSample] = []
    products: list[Product] = []
    cost_usd: float = 0.0


def _user_prompt(meta: SiteMetadata, corpus: SiteCorpus) -> str:
    return (
        f"SITE TITLE: {meta.title}\n"
        f"META DESCRIPTION: {meta.description or ''}\n"
        f"JSON-LD ORG: {meta.jsonld_org_name or ''}\n"
        f"FOUNDED HINT: {meta.founded or ''}\n"
        f"THEME COLOR HINT: {meta.theme_color or ''}\n\n"
        f"PAGE CORPUS:\n{corpus.text}"
    )


async def synthesize_profile(
    provider: LLMProvider, meta: SiteMetadata, corpus: SiteCorpus
) -> ProfileCore:
    user = _user_prompt(meta, corpus)
    last_err: Exception | None = None
    cost = 0.0
    for attempt in range(2):
        result = await provider.complete_json(system=_SYSTEM, user=user, schema=_SCHEMA)
        cost += result.cost_usd
        try:
            core = ProfileCore(**result.data)
            return core.model_copy(update={"cost_usd": cost})
        except ValidationError as exc:
            last_err = exc
            user = (
                _user_prompt(meta, corpus)
                + f"\n\nYour previous output was invalid: {exc}. "
                "Return JSON that matches the schema exactly."
            )
    raise UpstreamError(
        f"synthesis failed schema validation after repair: {last_err}", stage="synthesize"
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd packages/brand-extract && uv run pytest tests/test_synthesize.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add packages/brand-extract/src/cortex_brand_extract/synthesize.py packages/brand-extract/tests/test_synthesize.py
git commit -m "feat(brand-extract): structured synthesis with one repair retry"
```

---

## Task 14: Competitor match

**Files:**
- Create: `packages/brand-extract/src/cortex_brand_extract/match/__init__.py`
- Create: `packages/brand-extract/src/cortex_brand_extract/match/competitors.py`
- Create: `packages/brand-extract/tests/test_match_competitors.py`

- [ ] **Step 1: Write the failing test**

Create `packages/brand-extract/tests/test_match_competitors.py`:

```python
from cortex_brand_extract.llm.base import FakeProvider
from cortex_brand_extract.match.competitors import rank_competitors
from cortex_brand_extract.types import CompetitorCandidate


async def test_returns_empty_with_warning_when_no_candidates():
    comps, warning = await rank_competitors(
        FakeProvider(responses=[]), brand_name="Acme", category="Retail banking", candidates=[]
    )
    assert comps == []
    assert warning and "no competitor candidates" in warning


async def test_ranks_caller_supplied_candidates_only():
    fake = FakeProvider(
        responses=[{"ranked": [{"name": "Cathay United", "domain": "cathaybk.com.tw", "match_score": 93}]}]
    )
    comps, warning = await rank_competitors(
        fake,
        brand_name="Acme",
        category="Retail banking",
        candidates=[CompetitorCandidate(name="Cathay United", domain="cathaybk.com.tw")],
    )
    assert warning is None
    assert comps[0].name == "Cathay United"
    assert comps[0].match_score == 93
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/brand-extract && uv run pytest tests/test_match_competitors.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cortex_brand_extract.match'`

- [ ] **Step 3: Write minimal implementation**

Create `packages/brand-extract/src/cortex_brand_extract/match/__init__.py`:

```python
"""Candidate ranking. Per spec, the LLM ranks caller-supplied candidates; it
never invents them. No candidates → empty result + warning.
"""
```

Create `packages/brand-extract/src/cortex_brand_extract/match/competitors.py`:

```python
from __future__ import annotations

from cortex_brand_extract.llm.base import LLMProvider
from cortex_brand_extract.types import Competitor, CompetitorCandidate

_SYSTEM = (
    "Rank how directly each candidate competes with the brand. "
    "Only use the supplied candidates. Score 0-100."
)
_SCHEMA = {
    "type": "object",
    "required": ["ranked"],
    "properties": {
        "ranked": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "domain": {"type": "string"},
                    "match_score": {"type": "integer"},
                },
            },
        }
    },
}


async def rank_competitors(
    provider: LLMProvider,
    *,
    brand_name: str,
    category: str,
    candidates: list[CompetitorCandidate],
) -> tuple[list[Competitor], str | None]:
    if not candidates:
        return [], "no competitor candidates supplied; competitor match skipped"
    listing = "\n".join(f"- {c.name} ({c.domain or 'no domain'})" for c in candidates)
    result = await provider.complete_json(
        system=_SYSTEM,
        user=f"BRAND: {brand_name}\nCATEGORY: {category}\nCANDIDATES:\n{listing}",
        schema=_SCHEMA,
    )
    allowed = {c.name for c in candidates}
    comps = [
        Competitor(
            name=r["name"],
            domain=r.get("domain"),
            match_score=int(r.get("match_score", 0)),
        )
        for r in result.data.get("ranked", [])
        if r.get("name") in allowed
    ]
    return comps, None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd packages/brand-extract && uv run pytest tests/test_match_competitors.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add packages/brand-extract/src/cortex_brand_extract/match/ packages/brand-extract/tests/test_match_competitors.py
git commit -m "feat(brand-extract): competitor ranking (caller candidates only)"
```

---

## Task 15: Media match

**Files:**
- Create: `packages/brand-extract/src/cortex_brand_extract/match/media.py`
- Create: `packages/brand-extract/tests/test_match_media.py`

- [ ] **Step 1: Write the failing test**

Create `packages/brand-extract/tests/test_match_media.py`:

```python
from cortex_brand_extract.llm.base import FakeProvider
from cortex_brand_extract.match.media import rank_media
from cortex_brand_extract.types import MediaOutlet


async def test_empty_catalog_skips_with_warning():
    matches, warning = await rank_media(
        FakeProvider(responses=[]), brand_name="Acme", category="Banking", catalog=[]
    )
    assert matches == []
    assert warning and "no media catalog" in warning


async def test_ranks_supplied_catalog():
    fake = FakeProvider(
        responses=[{"ranked": [{"outlet_id": "moneydj", "name": "MoneyDJ", "relevance": 94}]}]
    )
    matches, warning = await rank_media(
        fake,
        brand_name="Acme",
        category="Banking",
        catalog=[MediaOutlet(outlet_id="moneydj", name="MoneyDJ", topics=["ETF"])],
    )
    assert warning is None
    assert matches[0].outlet_id == "moneydj"
    assert matches[0].relevance == 94
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/brand-extract && uv run pytest tests/test_match_media.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cortex_brand_extract.match.media'`

- [ ] **Step 3: Write minimal implementation**

Create `packages/brand-extract/src/cortex_brand_extract/match/media.py`:

```python
from __future__ import annotations

from cortex_brand_extract.llm.base import LLMProvider
from cortex_brand_extract.types import MediaMatch, MediaOutlet

_SYSTEM = (
    "Rank how relevant each media outlet's audience is to the brand. "
    "Only use the supplied catalog. Score 0-100."
)
_SCHEMA = {
    "type": "object",
    "required": ["ranked"],
    "properties": {
        "ranked": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "outlet_id": {"type": "string"},
                    "name": {"type": "string"},
                    "relevance": {"type": "integer"},
                },
            },
        }
    },
}


async def rank_media(
    provider: LLMProvider,
    *,
    brand_name: str,
    category: str,
    catalog: list[MediaOutlet],
) -> tuple[list[MediaMatch], str | None]:
    if not catalog:
        return [], "no media catalog supplied; media match skipped"
    listing = "\n".join(
        f"- [{o.outlet_id}] {o.name} — {o.audience or ''} topics={o.topics}" for o in catalog
    )
    result = await provider.complete_json(
        system=_SYSTEM,
        user=f"BRAND: {brand_name}\nCATEGORY: {category}\nCATALOG:\n{listing}",
        schema=_SCHEMA,
    )
    allowed = {o.outlet_id for o in catalog}
    matches = [
        MediaMatch(
            outlet_id=r["outlet_id"],
            name=r.get("name", ""),
            relevance=int(r.get("relevance", 0)),
        )
        for r in result.data.get("ranked", [])
        if r.get("outlet_id") in allowed
    ]
    return matches, None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd packages/brand-extract && uv run pytest tests/test_match_media.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add packages/brand-extract/src/cortex_brand_extract/match/media.py packages/brand-extract/tests/test_match_media.py
git commit -m "feat(brand-extract): media ranking (caller catalog only)"
```

---

## Task 16: Pipeline orchestrator + public API

**Files:**
- Create: `packages/brand-extract/src/cortex_brand_extract/pipeline.py`
- Modify: `packages/brand-extract/src/cortex_brand_extract/__init__.py`
- Create: `packages/brand-extract/tests/test_pipeline.py`

- [ ] **Step 1: Write the failing test**

Create `packages/brand-extract/tests/test_pipeline.py`:

```python
import httpx
import respx

from cortex_brand_extract import extract_brand_profile
from cortex_brand_extract.llm.base import FakeProvider
from cortex_brand_extract.progress import ListSink
from cortex_brand_extract.types import CompetitorCandidate, MediaOutlet

_HOME = """<html><head><title>Acme Bank Asia</title>
<meta name="description" content="27 years across Asia." />
<meta name="theme-color" content="#225D59" /></head>
<body><p>Acme Bank Asia serves millions. Banking should work for people. """ + ("text " * 80) + """</p>
<a href="/about">About</a></body></html>"""

_ABOUT = "<html><body><p>" + ("About Acme. " * 80) + "</p></body></html>"

_SYNTH = {
    "name": "Acme Bank Asia",
    "tagline": "Banking, redesigned for Asia.",
    "about": "27 years across Asia.",
    "region": ["Taiwan"],
    "category": {"value": "Retail banking", "confidence": 95, "alternatives": []},
    "voice_samples": [{"src": "/about", "text": "Banking should work for people."}],
    "products": [{"name": "Smart Account", "category": "Deposits", "url": "/smart", "confidence": 96}],
}
_COMP = {"ranked": [{"name": "Cathay United", "domain": "cathaybk.com.tw", "match_score": 92}]}
_MEDIA = {"ranked": [{"outlet_id": "moneydj", "name": "MoneyDJ", "relevance": 90}]}


@respx.mock
async def test_pipeline_end_to_end_lite_with_fakes():
    respx.get("https://acmebank.asia/").mock(return_value=httpx.Response(200, html=_HOME))
    respx.get("https://acmebank.asia/about").mock(return_value=httpx.Response(200, html=_ABOUT))
    sink = ListSink()
    provider = FakeProvider(responses=[_SYNTH, _COMP, _MEDIA])

    profile = await extract_brand_profile(
        "acmebank.asia",
        tier="lite",
        provider=provider,
        max_pages=2,
        competitor_candidates=[CompetitorCandidate(name="Cathay United", domain="cathaybk.com.tw")],
        seed_media_catalog=[MediaOutlet(outlet_id="moneydj", name="MoneyDJ", topics=["ETF"])],
        progress=sink,
    )

    assert profile.name == "Acme Bank Asia"
    assert profile.competitors[0].name == "Cathay United"
    assert profile.media_matches[0].outlet_id == "moneydj"
    assert profile.extraction_meta.tier == "lite"
    assert profile.extraction_meta.cost_usd > 0.0
    stages = {e.stage for e in sink.events}
    assert {"fetch", "parse", "synthesize", "done"}.issubset(stages)


@respx.mock
async def test_pipeline_degrades_when_a_match_has_no_candidates():
    respx.get("https://acmebank.asia/").mock(return_value=httpx.Response(200, html=_HOME))
    respx.get("https://acmebank.asia/about").mock(return_value=httpx.Response(200, html=_ABOUT))
    provider = FakeProvider(responses=[_SYNTH])  # only synthesis is called

    profile = await extract_brand_profile(
        "acmebank.asia",
        tier="lite",
        provider=provider,
        max_pages=2,
    )
    assert profile.competitors == []
    assert profile.media_matches == []
    assert any("competitor" in w for w in profile.extraction_meta.warnings)
    assert any("media" in w for w in profile.extraction_meta.warnings)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/brand-extract && uv run pytest tests/test_pipeline.py -v`
Expected: FAIL — `ImportError: cannot import name 'extract_brand_profile'`

- [ ] **Step 3: Write minimal implementation**

Create `packages/brand-extract/src/cortex_brand_extract/pipeline.py`:

```python
"""Orchestrator. Wires the stages, emits progress, isolates per-stage
failures into warnings, and accumulates cost into extraction_meta.
"""

from __future__ import annotations

from cortex_brand_extract.corpus import build_corpus
from cortex_brand_extract.crawl import select_pages
from cortex_brand_extract.fetch.deep import fetch_deep
from cortex_brand_extract.fetch.detect import looks_js_rendered
from cortex_brand_extract.fetch.lite import fetch_lite
from cortex_brand_extract.llm.base import LLMProvider
from cortex_brand_extract.match.competitors import rank_competitors
from cortex_brand_extract.match.media import rank_media
from cortex_brand_extract.parse import parse_site
from cortex_brand_extract.progress import ProgressEvent, ProgressSink, emit
from cortex_brand_extract.synthesize import synthesize_profile
from cortex_brand_extract.types import (
    BrandProfile,
    CompetitorCandidate,
    ExtractionMeta,
    ExtractTier,
    MediaOutlet,
)


async def _fetch(url: str, tier: ExtractTier) -> tuple[str, str, str]:
    page = await fetch_deep(url) if tier == "deep" else await fetch_lite(url)
    return page.final_url, page.html, ("" if page.status == 200 else f"status {page.status}")


async def extract_brand_profile(
    url: str,
    *,
    tier: ExtractTier = "lite",
    provider: LLMProvider,
    max_pages: int = 12,
    competitor_candidates: list[CompetitorCandidate] | None = None,
    seed_media_catalog: list[MediaOutlet] | None = None,
    progress: ProgressSink | None = None,
    max_corpus_chars: int = 60_000,
) -> BrandProfile:
    warnings: list[str] = []
    cost = 0.0

    await emit(progress, ProgressEvent(stage="fetch", status="running", detail=url))
    home_url, home_html, fetch_warn = await _fetch(url, tier)
    if fetch_warn:
        warnings.append(f"homepage fetch: {fetch_warn}")
    js_detected, why = looks_js_rendered(home_html)
    if js_detected and tier == "lite":
        warnings.append(f"site looks JS-rendered ({why}); deep tier recommended")
    await emit(progress, ProgressEvent(stage="fetch", status="ok", detail=home_url))

    await emit(progress, ProgressEvent(stage="parse", status="running"))
    meta = parse_site(home_url, home_html)
    await emit(progress, ProgressEvent(stage="parse", status="ok", detail=meta.title))

    await emit(progress, ProgressEvent(stage="crawl", status="running"))
    chosen = select_pages(home_url, meta.internal_links, max_pages=max_pages)
    pages: list[tuple[str, str]] = [(home_url, meta.visible_text)]
    for link in chosen[1:]:
        _, html, warn = await _fetch(link, tier)
        if warn:
            warnings.append(f"{link}: {warn}")
            continue
        pages.append((link, parse_site(link, html).visible_text))
    await emit(progress, ProgressEvent(stage="crawl", status="ok", detail=f"{len(pages)} pages"))

    await emit(progress, ProgressEvent(stage="corpus", status="running"))
    corpus = build_corpus(pages, max_chars=max_corpus_chars)
    if corpus.truncated:
        warnings.append("corpus truncated to char budget")
    await emit(progress, ProgressEvent(stage="corpus", status="ok"))

    await emit(progress, ProgressEvent(stage="synthesize", status="running"))
    core = await synthesize_profile(provider, meta, corpus)
    cost += core.cost_usd
    await emit(progress, ProgressEvent(stage="synthesize", status="ok", detail=core.name))

    await emit(progress, ProgressEvent(stage="competitors", status="running"))
    competitors, comp_warn = await rank_competitors(
        provider,
        brand_name=core.name,
        category=core.category.value,
        candidates=competitor_candidates or [],
    )
    if comp_warn:
        warnings.append(comp_warn)
    await emit(progress, ProgressEvent(stage="competitors", status="ok"))

    await emit(progress, ProgressEvent(stage="media", status="running"))
    media, media_warn = await rank_media(
        provider,
        brand_name=core.name,
        category=core.category.value,
        catalog=seed_media_catalog or [],
    )
    if media_warn:
        warnings.append(media_warn)
    await emit(progress, ProgressEvent(stage="media", status="ok"))

    await emit(progress, ProgressEvent(stage="done", status="ok"))
    return BrandProfile(
        url=home_url,
        name=core.name,
        legal_name=core.legal_name or meta.jsonld_org_name,
        tagline=core.tagline,
        monogram=core.monogram,
        brand_color=core.brand_color or meta.theme_color,
        category=core.category,
        region=core.region,
        founded=core.founded or meta.founded,
        about=core.about,
        voice_samples=core.voice_samples,
        products=core.products,
        competitors=competitors,
        media_matches=media,
        extraction_meta=ExtractionMeta(
            tier=tier,
            model=type(provider).__name__,
            cost_usd=round(cost, 6),
            js_detected=js_detected,
            warnings=warnings,
        ),
    )
```

Replace `packages/brand-extract/src/cortex_brand_extract/__init__.py` with:

```python
"""cortex-brand-extract — URL → structured BrandProfile.

Public API. Stage functions are exported for granular MCP tools and tests.
"""

from __future__ import annotations

from cortex_brand_extract.corpus import build_corpus
from cortex_brand_extract.crawl import select_pages
from cortex_brand_extract.parse import parse_site
from cortex_brand_extract.pipeline import extract_brand_profile
from cortex_brand_extract.synthesize import synthesize_profile
from cortex_brand_extract.types import BrandProfile, ProviderConfig

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "extract_brand_profile",
    "BrandProfile",
    "ProviderConfig",
    "parse_site",
    "select_pages",
    "build_corpus",
    "synthesize_profile",
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd packages/brand-extract && uv run pytest tests/test_pipeline.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add packages/brand-extract/src/cortex_brand_extract/pipeline.py packages/brand-extract/src/cortex_brand_extract/__init__.py packages/brand-extract/tests/test_pipeline.py
git commit -m "feat(brand-extract): pipeline orchestrator + public API"
```

---

## Task 17: MCP server façade

**Files:**
- Create: `packages/brand-extract/src/cortex_brand_extract/mcp/__init__.py`
- Create: `packages/brand-extract/src/cortex_brand_extract/mcp/server.py`
- Create: `packages/brand-extract/src/cortex_brand_extract/mcp/__main__.py`
- Create: `packages/brand-extract/tests/test_mcp_server.py`

- [ ] **Step 1: Write the failing test**

Create `packages/brand-extract/tests/test_mcp_server.py`:

```python
import pytest

mcp = pytest.importorskip("mcp")  # skip if [mcp] extra not installed

from cortex_brand_extract.mcp.server import build_server


async def test_server_registers_extract_tool():
    server = build_server()
    tools = await server.list_tools()
    names = {t.name for t in tools}
    assert "extract_brand_profile" in names
    assert "fetch_site" in names
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/brand-extract && uv run --extra mcp pytest tests/test_mcp_server.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cortex_brand_extract.mcp'`

- [ ] **Step 3: Write minimal implementation**

Create `packages/brand-extract/src/cortex_brand_extract/mcp/__init__.py`:

```python
"""MCP façade. Exposes the orchestrator and stage functions as MCP tools."""
```

Create `packages/brand-extract/src/cortex_brand_extract/mcp/server.py`:

```python
"""FastMCP server. BYO-key: callers pass provider kind/key/model as tool
arguments (or set CORTEX_EXTRACT_API_KEY in the server env).
"""

from __future__ import annotations

import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from cortex_brand_extract.fetch.lite import fetch_lite
from cortex_brand_extract.llm.claude import ClaudeProvider
from cortex_brand_extract.llm.openai_compat import OpenAICompatProvider
from cortex_brand_extract.pipeline import extract_brand_profile
from cortex_brand_extract.types import ProviderConfig, ProviderKind


def _provider(kind: ProviderKind, model: str, api_key: str | None, base_url: str | None):
    key = api_key or os.environ.get("CORTEX_EXTRACT_API_KEY", "")
    cfg = ProviderConfig(kind=kind, api_key=key, model=model, base_url=base_url)
    return ClaudeProvider(cfg) if kind == "claude" else OpenAICompatProvider(cfg)


def build_server() -> FastMCP:
    mcp = FastMCP("cortex-brand-extract")

    @mcp.tool()
    async def fetch_site(url: str) -> dict[str, Any]:
        """Fetch a single page (lite/static). Returns status + html length."""
        page = await fetch_lite(url)
        return {"final_url": page.final_url, "status": page.status, "chars": len(page.html)}

    @mcp.tool()
    async def extract_brand_profile_tool(
        url: str,
        tier: str = "lite",
        provider_kind: str = "claude",
        model: str = "claude-opus-4-7",
        api_key: str | None = None,
        base_url: str | None = None,
        max_pages: int = 12,
    ) -> dict[str, Any]:
        """Extract a full BrandProfile from a brand URL."""
        prov = _provider(provider_kind, model, api_key, base_url)  # type: ignore[arg-type]
        profile = await extract_brand_profile(
            url, tier=tier, provider=prov, max_pages=max_pages  # type: ignore[arg-type]
        )
        return profile.model_dump(mode="json")

    # Register the orchestrator under the spec's canonical name too.
    mcp._tool_manager._tools["extract_brand_profile"] = mcp._tool_manager._tools.pop(
        "extract_brand_profile_tool"
    )
    mcp._tool_manager._tools["extract_brand_profile"].name = "extract_brand_profile"
    return mcp
```

Create `packages/brand-extract/src/cortex_brand_extract/mcp/__main__.py`:

```python
"""Entrypoint: `python -m cortex_brand_extract.mcp` (stdio transport)."""

from __future__ import annotations

from cortex_brand_extract.mcp.server import build_server


def main() -> None:
    build_server().run()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd packages/brand-extract && uv run --extra mcp pytest tests/test_mcp_server.py -v`
Expected: PASS

> If `mcp`'s tool-manager internals differ in the installed version and the rename line raises, replace the two `mcp._tool_manager` lines by simply naming the function `extract_brand_profile` directly (rename `extract_brand_profile_tool` → `extract_brand_profile` and delete the two reassignment lines). Re-run; expected PASS.

- [ ] **Step 5: Commit**

```bash
git add packages/brand-extract/src/cortex_brand_extract/mcp/ packages/brand-extract/tests/test_mcp_server.py
git commit -m "feat(brand-extract): MCP server façade"
```

---

## Task 18: Eval harness + README + quality gate

**Files:**
- Create: `packages/brand-extract/eval/run_eval.py`
- Create: `packages/brand-extract/eval/README.md`
- Create: `packages/brand-extract/eval/urls.json`
- Create: `packages/brand-extract/README.md`

- [ ] **Step 1: Create the eval URL set**

Create `packages/brand-extract/eval/urls.json`:

```json
[
  {"url": "https://www.esunbank.com.tw", "vertical": "banking", "js": false},
  {"url": "https://www.cathaybk.com.tw", "vertical": "banking", "js": false},
  {"url": "https://www.notion.so", "vertical": "saas", "js": true},
  {"url": "https://www.figma.com", "vertical": "saas", "js": true},
  {"url": "https://www.allbirds.com", "vertical": "retail", "js": true},
  {"url": "https://www.patagonia.com", "vertical": "retail", "js": false},
  {"url": "https://stripe.com", "vertical": "fintech", "js": true},
  {"url": "https://www.hubspot.com", "vertical": "martech", "js": true}
]
```

- [ ] **Step 2: Create the eval harness**

Create `packages/brand-extract/eval/run_eval.py`:

```python
"""Manual eval harness. NOT a unit test — it makes real network + LLM calls.

Usage:
  CORTEX_EXTRACT_API_KEY=sk-... \
  uv run python eval/run_eval.py --tier lite --provider claude --model claude-opus-4-7

Writes eval/results-<tier>.json with one BrandProfile per URL plus cost.
Score each facet by hand 1-5 using eval/README.md, then check the
done-criteria thresholds in the spec.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path

from cortex_brand_extract import extract_brand_profile
from cortex_brand_extract.llm.claude import ClaudeProvider
from cortex_brand_extract.llm.openai_compat import OpenAICompatProvider
from cortex_brand_extract.types import ProviderConfig

HERE = Path(__file__).parent


async def _run(tier: str, kind: str, model: str, base_url: str | None) -> None:
    cfg = ProviderConfig(
        kind=kind,  # type: ignore[arg-type]
        api_key=os.environ["CORTEX_EXTRACT_API_KEY"],
        model=model,
        base_url=base_url,
    )
    provider = ClaudeProvider(cfg) if kind == "claude" else OpenAICompatProvider(cfg)
    targets = json.loads((HERE / "urls.json").read_text())
    out = []
    for t in targets:
        try:
            profile = await extract_brand_profile(t["url"], tier=tier, provider=provider)
            out.append({"target": t, "profile": profile.model_dump(mode="json")})
            print(f"OK  {t['url']}  ${profile.extraction_meta.cost_usd:.4f}")
        except Exception as exc:  # noqa: BLE001 - eval keeps going
            out.append({"target": t, "error": repr(exc)})
            print(f"ERR {t['url']}  {exc!r}")
    (HERE / f"results-{tier}.json").write_text(json.dumps(out, indent=2))
    total = sum(
        r["profile"]["extraction_meta"]["cost_usd"] for r in out if "profile" in r
    )
    print(f"\nTotal cost: ${total:.4f}  ({tier})")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", default="lite", choices=["lite", "deep"])
    ap.add_argument("--provider", default="claude", choices=["claude", "openai_compat"])
    ap.add_argument("--model", default="claude-opus-4-7")
    ap.add_argument("--base-url", default=None)
    args = ap.parse_args()
    asyncio.run(_run(args.tier, args.provider, args.model, args.base_url))


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Create the rubric**

Create `packages/brand-extract/eval/README.md`:

```markdown
# Eval harness & rubric

Run `run_eval.py` for `lite` and `deep`, then score each profile by hand.

## Rubric (1–5 per facet, per URL)

- **category** — is the inferred category correct and specific?
- **about** — is the summary accurate and grounded (no hallucination)?
- **products** — are the listed products real and correctly named?
- **voice** — do voice samples sound like the brand's actual copy?

## Done-criteria (from the spec)

- Median ≥ 4 for category, about, products.
- Median ≥ 3 for voice.
- `deep` ≥ `lite` on the URLs marked `"js": true`.
- Cost ≤ ~$0.10 (lite) / ~$0.30 (deep) per extraction with prompt caching.
- Library imports cleanly; MCP server callable from Claude / the `mcp` CLI.
```

- [ ] **Step 4: Create the package README**

Create `packages/brand-extract/README.md`:

```markdown
# cortex-brand-extract

URL → structured `BrandProfile`. Pure library (no auth, no DB). Used by
cortex-api directly and exposed to AI tools via an MCP server.

## Install

```bash
pip install cortex-brand-extract                 # lite tier only
pip install 'cortex-brand-extract[render]'       # + deep (Playwright) tier
pip install 'cortex-brand-extract[mcp]'          # + MCP server
playwright install chromium                      # once, for the deep tier
```

## Library use

```python
import asyncio
from cortex_brand_extract import extract_brand_profile
from cortex_brand_extract.llm.claude import ClaudeProvider
from cortex_brand_extract.types import ProviderConfig

provider = ClaudeProvider(
    ProviderConfig(kind="claude", api_key="sk-...", model="claude-opus-4-7")
)
profile = asyncio.run(extract_brand_profile("acmebank.asia", tier="lite", provider=provider))
print(profile.model_dump_json(indent=2))
```

## MCP server (BYO-key)

```bash
CORTEX_EXTRACT_API_KEY=sk-... python -m cortex_brand_extract.mcp
```

Tools: `extract_brand_profile`, `fetch_site`. Pass `provider_kind`,
`model`, and `api_key` per call, or set `CORTEX_EXTRACT_API_KEY`.

## Tiers

- `lite` — static fetch, no browser, pip-light.
- `deep` — headless render for JS-heavy SPA sites (needs `[render]`).

## Scope

This is SP-2 of the brand onboarding program. Persistence, GTM mode, and
the one-pager live in cortex-api / SP-1 / SP-3 / SP-4.
```

- [ ] **Step 5: Run the full quality gate**

Run: `cd packages/brand-extract && uv run ruff check . && uv run ruff format --check . && uv run mypy src && uv run pytest -v`
Expected: ruff clean, mypy clean, all tests PASS (the `[mcp]` test is skipped unless run with `--extra mcp`).

Fix any ruff/mypy findings, then re-run until clean.

- [ ] **Step 6: Commit**

```bash
git add packages/brand-extract/eval/ packages/brand-extract/README.md
git commit -m "feat(brand-extract): eval harness, rubric, README"
```

---

## Self-Review

**1. Spec coverage:**

| Spec section | Task(s) |
|---|---|
| Locked decision 3 — library-first pure package | 0, 16 |
| Locked decision 4 — tiered fetch (lite/deep) | 7, 9, 16 |
| Locked decision 5 — pluggable BYO-key LLM, Claude default | 4, 5, 6, 17 |
| Locked decision 6 — staged + structured synthesis | 10–16 |
| Public contract (`extract_brand_profile` + stage fns) | 16 |
| `BrandProfile` VO, field-aligned with `ExtractedBrand` | 1 |
| Pipeline & data flow | 16 |
| Progress events | 3, 16 |
| Error handling & degradation (JS-detect, per-stage isolation, typed errors, cost bound) | 2, 8, 13, 16 |
| Competitor/media = caller candidates + LLM rank | 14, 15 |
| MCP façade (orchestrator + stage tools, BYO-key) | 17 |
| Testing (offline deterministic + faked provider) | every task |
| Eval harness + spike done-criteria | 18 |
| Out of scope (no cortex-api/persistence/GTM/one-pager) | honored — no such tasks |

No gaps.

**2. Placeholder scan:** No "TBD"/"TODO"/"implement later". Every code step contains complete code. The one conditional instruction (Task 17 Step 4 fallback) gives the exact alternative edit, not a vague pointer.

**3. Type consistency:** `extract_brand_profile`, `LLMProvider.complete_json`, `LLMResult`, `FetchedPage`, `SiteMetadata`, `SiteCorpus`, `ProfileCore`, `ProgressEvent`, `BrandProfile` and its members are used consistently across Tasks 1–18. `ProviderConfig` fields (`kind`, `api_key`, `model`, `base_url`) match in Tasks 1, 5, 6, 17, 18. Competitor/media match return `tuple[list[...], str | None]` consistently and the pipeline consumes that shape in Task 16.

Plan is internally consistent and fully covers the spec.
