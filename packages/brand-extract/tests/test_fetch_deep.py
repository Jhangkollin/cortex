import builtins
import logging
import sys
import types

import pytest

from cortex_brand_extract.fetch.deep import fetch_deep


async def test_fetch_deep_raises_clear_error_when_render_extra_missing(monkeypatch) -> None:
    real_import = builtins.__import__

    def _block(name, *args, **kwargs):
        if name.startswith("playwright"):
            raise ModuleNotFoundError("No module named 'playwright'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _block)
    with pytest.raises(RuntimeError, match=r"pip install .*\[render\]"):
        await fetch_deep("https://acmebank.asia")


class _PWError(Exception):
    """Stand-in for playwright.async_api.Error (navigation / network)."""


class _PWTimeoutError(_PWError):
    """Stand-in for playwright.async_api.TimeoutError.

    Real Playwright's TimeoutError subclasses Error; mirror that so a single
    `except Error` covers both navigation and timeout failures.
    """


def _install_fake_playwright(monkeypatch, *, goto_exc: Exception) -> None:
    """Inject a minimal fake `playwright.async_api` whose page.goto raises,
    mirroring a transient navigation/timeout failure. Playwright is the
    optional [render] extra and is not installed in CI.
    """

    class _Page:
        async def goto(self, *a, **k):
            raise goto_exc

        async def content(self):  # pragma: no cover - not reached on failure
            return ""

        url = "https://acmebank.asia/"

    class _Browser:
        async def new_page(self, **k):
            return _Page()

        async def close(self):
            return None

    class _Chromium:
        async def launch(self, **k):
            return _Browser()

    class _PW:
        chromium = _Chromium()

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

    def _async_playwright():
        return _PW()

    mod = types.ModuleType("playwright.async_api")
    mod.async_playwright = _async_playwright  # type: ignore[attr-defined]
    mod.Error = _PWError  # type: ignore[attr-defined]
    mod.TimeoutError = _PWTimeoutError  # type: ignore[attr-defined]
    pkg = types.ModuleType("playwright")
    monkeypatch.setitem(sys.modules, "playwright", pkg)
    monkeypatch.setitem(sys.modules, "playwright.async_api", mod)


async def test_fetch_deep_timeout_yields_status_zero(monkeypatch) -> None:
    """A Playwright navigation timeout must degrade to FetchedPage(status=0)
    so the pipeline degrades per-page, matching fetch_lite's contract.
    """
    _install_fake_playwright(monkeypatch, goto_exc=_PWTimeoutError("Timeout 30000ms exceeded"))
    page = await fetch_deep("acmebank.asia")
    assert page.status == 0
    assert page.html == ""
    assert page.requested_url == "https://acmebank.asia"


async def test_fetch_deep_navigation_error_yields_status_zero(monkeypatch) -> None:
    """A Playwright network/navigation Error must also degrade, not raise."""
    _install_fake_playwright(monkeypatch, goto_exc=_PWError("net::ERR_NAME_NOT_RESOLVED"))
    page = await fetch_deep("https://acmebank.asia")
    assert page.status == 0
    assert page.html == ""


async def test_fetch_deep_navigation_error_degrades_and_warns(
    monkeypatch, caplog: pytest.LogCaptureFixture
) -> None:
    """The silent-degrade path must be observable: a single WARNING that
    references the target URL is emitted before returning status=0.
    """
    _install_fake_playwright(monkeypatch, goto_exc=_PWError("net::ERR_NAME_NOT_RESOLVED"))
    with caplog.at_level(logging.WARNING, logger="cortex_brand_extract.fetch.deep"):
        page = await fetch_deep("acmebank.asia")
    assert page.status == 0
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1
    assert getattr(warnings[0], "url", None) == "https://acmebank.asia"
