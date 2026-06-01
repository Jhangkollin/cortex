"""Deep fetch via Playwright. Import-guarded: Playwright ships only with the
`[render]` extra, so a missing import yields an actionable error rather than a
bare ModuleNotFoundError.

Mirrors ``fetch_lite``'s contract: transient navigation / network / timeout
failures degrade to ``FetchedPage(status=0, html="")`` so the pipeline can
drop a single bad page and continue. Only the missing-extra ``RuntimeError``
(a config/programming error, not a per-page transient) is allowed to bubble.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from cortex_brand_extract.fetch.lite import FetchedPage

_UA = "cortex-brand-extract/0.1 (+https://github.com/mlytics/cortex)"


async def fetch_deep(url: str, *, timeout: float = 30.0) -> FetchedPage:
    try:
        from playwright.async_api import (  # type: ignore[import-not-found]
            Error as PlaywrightError,
        )
        from playwright.async_api import (
            async_playwright,
        )
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "deep tier needs Playwright. Install with: "
            "pip install 'cortex-brand-extract[render]' && playwright install chromium"
        ) from exc

    # playwright.async_api.TimeoutError subclasses Error, so catching
    # PlaywrightError covers navigation, network, and timeout failures.
    target = url if url.startswith(("http://", "https://")) else "https://" + url
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            page = await browser.new_page(user_agent=_UA)
            try:
                resp = await page.goto(target, wait_until="networkidle", timeout=timeout * 1000)
                html = await page.content()
                status = resp.status if resp else 0
                final_url = page.url
            except PlaywrightError as exc:
                logging.getLogger(__name__).warning(
                    "fetch_deep navigation failed; degrading to empty page",
                    extra={
                        "url": target,
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    },
                )
                return FetchedPage(
                    requested_url=target,
                    final_url=target,
                    status=0,
                    html="",
                    fetched_at=datetime.now(UTC),
                )
        finally:
            await browser.close()
    return FetchedPage(
        requested_url=target,
        final_url=final_url,
        status=status,
        html=html if status == 200 else "",
        fetched_at=datetime.now(UTC),
    )
