"""Tests for DatabaseConfig component-based URL assembly + URL-encoding."""

from __future__ import annotations

import pytest

from cortex_api.core.config.database_config import DatabaseConfig


def _clear_db_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Strip CORE_DB_* env vars so tests see clean defaults / set ones explicitly."""
    for key in (
        "CORE_DB_HOST",
        "CORE_DB_PORT",
        "CORE_DB_USERNAME",
        "CORE_DB_PASSWORD",
        "CORE_DB_NAME",
        "CORE_DB_POOL_SIZE",
        "CORE_DB_POOL_PRE_PING",
        "CORE_DB_ECHO",
    ):
        monkeypatch.delenv(key, raising=False)


def test_defaults_assemble_local_dev_dsn(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_db_env(monkeypatch)
    cfg = DatabaseConfig()
    assert cfg.url == "postgresql+asyncpg://cortex:cortex@localhost:5433/cortex"


def test_components_assemble_rds_dsn(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_db_env(monkeypatch)
    monkeypatch.setenv("CORE_DB_HOST", "rds.example.com")
    monkeypatch.setenv("CORE_DB_PORT", "5432")
    monkeypatch.setenv("CORE_DB_USERNAME", "admin")
    monkeypatch.setenv("CORE_DB_PASSWORD", "simple")
    monkeypatch.setenv("CORE_DB_NAME", "mydb")

    cfg = DatabaseConfig()
    assert cfg.url == "postgresql+asyncpg://admin:simple@rds.example.com:5432/mydb"


def test_password_with_percent_is_url_encoded(monkeypatch: pytest.MonkeyPatch) -> None:
    """% in password must be URL-encoded — bare % corrupts the DSN AND would
    trigger configparser InterpolationSyntaxError if the URL were ever written
    to alembic.ini. quote_plus encodes % as %25."""
    _clear_db_env(monkeypatch)
    monkeypatch.setenv("CORE_DB_PASSWORD", "p%ss")

    cfg = DatabaseConfig()
    assert "p%25ss" in cfg.url
    assert "p%ss" not in cfg.url.replace("p%25ss", "")


def test_password_with_special_chars_is_url_encoded(monkeypatch: pytest.MonkeyPatch) -> None:
    """Real-world Terraform random_password produces all of these. The DSN
    must remain unambiguous after assembly."""
    _clear_db_env(monkeypatch)
    monkeypatch.setenv("CORE_DB_PASSWORD", "[qDY=1J1(0e/SG7WG@Ii>ee($Hj{!Y$")

    cfg = DatabaseConfig()
    # Each metacharacter that has DSN meaning must be percent-encoded.
    # quote_plus encodes: @ -> %40, / -> %2F, [ -> %5B, etc.
    assert "%40" in cfg.url  # @
    assert "%2F" in cfg.url  # /
    assert "%5B" in cfg.url  # [
    # The raw form must NOT appear (otherwise DSN parser would misread).
    raw = "[qDY=1J1(0e/SG7WG@Ii>ee($Hj{!Y$"
    assert raw not in cfg.url


def test_username_with_special_chars_is_url_encoded(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_db_env(monkeypatch)
    monkeypatch.setenv("CORE_DB_USERNAME", "user@host")

    cfg = DatabaseConfig()
    assert "user%40host" in cfg.url


def test_pool_fields_use_defaults_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_db_env(monkeypatch)
    cfg = DatabaseConfig()
    assert cfg.pool_size == 10
    assert cfg.pool_pre_ping is True
    assert cfg.echo is False


def test_secretstr_password_does_not_appear_in_repr(monkeypatch: pytest.MonkeyPatch) -> None:
    """SecretStr's repr redacts — accidental logging of the config object
    won't leak the password."""
    _clear_db_env(monkeypatch)
    monkeypatch.setenv("CORE_DB_PASSWORD", "topsecret")

    cfg = DatabaseConfig()
    assert "topsecret" not in repr(cfg)
    assert "topsecret" not in repr(cfg.password)
    # But the assembled URL DOES contain it (deliberate — caller's job to not log it)
    assert "topsecret" in cfg.url
