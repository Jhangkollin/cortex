import logging

import httpx
import pytest
import respx

from cortex_brand_extract.fetch.lite import FetchedPage, fetch_lite


@respx.mock
async def test_fetch_lite_normalizes_url_and_returns_page() -> None:
    respx.get("https://acmebank.asia/").mock(
        return_value=httpx.Response(200, html="<html><body>hi</body></html>")
    )
    page = await fetch_lite("acmebank.asia")
    assert isinstance(page, FetchedPage)
    assert page.status == 200
    assert page.final_url == "https://acmebank.asia/"
    assert "hi" in page.html


@respx.mock
async def test_fetch_lite_records_non_200_without_raising() -> None:
    respx.get("https://acmebank.asia/missing").mock(return_value=httpx.Response(404))
    page = await fetch_lite("https://acmebank.asia/missing")
    assert page.status == 404
    assert page.html == ""


@respx.mock
async def test_fetch_lite_http_error_degrades_and_warns(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The silent-degrade path must be observable: a single WARNING that
    references the target URL is emitted before returning status=0.
    """
    respx.get("https://acmebank.asia/").mock(side_effect=httpx.ConnectError("boom"))
    with caplog.at_level(logging.WARNING, logger="cortex_brand_extract.fetch.lite"):
        page = await fetch_lite("acmebank.asia")
    assert page.status == 0
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1
    assert getattr(warnings[0], "url", None) == "https://acmebank.asia"
