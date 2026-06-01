from __future__ import annotations

import pytest

from cortex_api.service.brand.analyze_config import AnalyzeConfig
from cortex_api.service.brand.analyze_provider import build_provider


def _cfg(**kw: object) -> AnalyzeConfig:
    base: dict[str, object] = {
        "provider_kind": "claude",
        "api_key": "sk-test",
        "model": "claude-opus-4-7",
        "base_url": None,
        "tier": "lite",
        "stale_job_seconds": 900,
    }
    base.update(kw)
    return AnalyzeConfig(**base)  # type: ignore[arg-type]


def test_build_claude_provider() -> None:
    prov = build_provider(_cfg())
    assert prov.model == "claude-opus-4-7"


def test_build_openai_compat_requires_base_url() -> None:
    with pytest.raises(ValueError):
        build_provider(_cfg(provider_kind="openai_compat", base_url=None))


def test_build_openai_compat_ok() -> None:
    prov = build_provider(_cfg(provider_kind="openai_compat", base_url="https://llm.example/v1"))
    assert prov.model == "claude-opus-4-7"
