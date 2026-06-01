"""Unit tests for ServiceTokenConfig."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from cortex_api.core.config.service_token_config import ServiceTokenConfig


class TestServiceTokenConfig:
    def test_reads_agent_ws_token_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CORE_SERVICE_TOKEN_AGENT_WS", "abc123")
        cfg = ServiceTokenConfig()
        assert cfg.agent_ws == "abc123"

    def test_defaults_to_empty_string_when_unset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("CORE_SERVICE_TOKEN_AGENT_WS", raising=False)
        cfg = ServiceTokenConfig()
        assert cfg.agent_ws == ""

    def test_rejects_unknown_field_when_passed_directly(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # extra="forbid" raises when unknown fields are passed as kwargs directly
        monkeypatch.setenv("CORE_SERVICE_TOKEN_AGENT_WS", "x")
        with pytest.raises(ValidationError):
            ServiceTokenConfig(bogus="y")  # type: ignore[call-arg]
