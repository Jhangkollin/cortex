"""Playwright headless-Chromium PDF renderer.

``render_pdf(html, *, timeout_ms, max_concurrent)`` is an async callable that
launches a fresh Chromium instance, renders the HTML, and returns raw PDF bytes.

MVP: launch-per-render.  A pooled browser session is a later optimisation —
the pool would hold a single persistent browser and page per worker, with a
semaphore to prevent concurrent renders from clobbering each other's page state.

Concurrency bulkhead: a process-global ``asyncio.Semaphore`` caps the number of
simultaneous Chromium launches.  Each launch costs real memory; an unbounded
launch count risks OOM-killing the worker.  When the cap is saturated we fail
fast with ``RateLimitedError`` (→ HTTP 429) rather than queueing indefinitely.

End-to-end deadline: both ``set_content`` and ``page.pdf`` are bounded by
``timeout_ms``, and the whole launch+render is wrapped in ``asyncio.wait_for``
(``timeout_ms * 2``) so a stalled Chromium can never hang a worker forever.

Playwright errors are mapped to ``cortex_api.core.exceptions.UpstreamError``
so the exception handlers return HTTP 502 (not 500) — callers know the
renderer is the problem, not the API logic.
"""

from __future__ import annotations

import asyncio

import structlog
from playwright.async_api import Error as PlaywrightError
from playwright.async_api import async_playwright

from cortex_api.core.exceptions import RateLimitedError, UpstreamError

# Process-global concurrency bulkhead. Sized lazily on first render from the
# caller-supplied cap so it tracks Config.pdf_max_concurrent_renders without a
# module-import-time dependency on the container.
_render_semaphore: asyncio.Semaphore | None = None
_render_semaphore_cap: int | None = None

# Short timeout for *acquiring* the bulkhead slot. If we can't get a slot
# quickly the system is saturated — fail fast (429) instead of piling up.
_ACQUIRE_TIMEOUT_S = 0.5


def _get_semaphore(max_concurrent: int) -> asyncio.Semaphore:
    """Return the process-global render semaphore, sized to *max_concurrent*."""
    global _render_semaphore, _render_semaphore_cap
    if _render_semaphore is None or _render_semaphore_cap != max_concurrent:
        _render_semaphore = asyncio.Semaphore(max_concurrent)
        _render_semaphore_cap = max_concurrent
    return _render_semaphore


async def render_pdf(html: str, *, timeout_ms: int = 15_000, max_concurrent: int = 2) -> bytes:
    """Render *html* to PDF bytes using headless Chromium.

    Args:
        html: A complete self-contained HTML document string.
        timeout_ms: Per-step bound for ``set_content`` and ``page.pdf``; the
            whole render is additionally bounded by ``timeout_ms * 2``.
        max_concurrent: Max simultaneous Chromium launches (bulkhead cap).

    Returns:
        Raw PDF bytes.

    Raises:
        RateLimitedError: If the concurrency bulkhead is saturated.
        UpstreamError: If Playwright / Chromium raises or the deadline elapses.
    """
    logger = structlog.get_logger(__name__)
    semaphore = _get_semaphore(max_concurrent)

    # Fail fast if the bulkhead is saturated — don't launch unbounded Chromium.
    try:
        await asyncio.wait_for(semaphore.acquire(), timeout=_ACQUIRE_TIMEOUT_S)
    except TimeoutError as exc:
        logger.warning("pdf_render_rejected_at_capacity", max_concurrent=max_concurrent)
        raise RateLimitedError(f"PDF renderer at capacity ({max_concurrent} concurrent); retry shortly") from exc

    try:
        return await asyncio.wait_for(
            _render(html, timeout_ms=timeout_ms, logger=logger),
            timeout=(timeout_ms * 2) / 1000,
        )
    except TimeoutError as exc:
        logger.error("pdf_render_deadline_exceeded", timeout_ms=timeout_ms)
        raise UpstreamError("Chromium render exceeded deadline") from exc
    finally:
        semaphore.release()


async def _render(html: str, *, timeout_ms: int, logger: structlog.BoundLogger) -> bytes:
    """Launch Chromium, render the HTML, return PDF bytes (bulkhead held by caller)."""
    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                ]
            )
            try:
                page = await browser.new_page()
                # Bound every page operation. page.pdf() takes no `timeout` kwarg,
                # so we set the page-wide default which it respects; set_content
                # is bounded explicitly. The outer asyncio.wait_for is the
                # hard backstop against a wholly stalled Chromium.
                page.set_default_timeout(timeout_ms)
                # The template is self-contained (inline CSS, inline SVG, no
                # network fetches), so "load" is sufficient — "networkidle"
                # would just add its ~500ms idle wait for no benefit.
                await page.set_content(html, wait_until="load", timeout=timeout_ms)
                pdf_bytes: bytes = await page.pdf(
                    format="A4",
                    print_background=True,
                    margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
                )
                return pdf_bytes
            finally:
                await browser.close()
    except PlaywrightError as exc:
        logger.error("pdf_render_failed", error=str(exc))
        raise UpstreamError(f"Chromium render failed: {exc}") from exc
