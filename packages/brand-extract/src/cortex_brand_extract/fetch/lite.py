"""Static fetch. No browser. Adds scheme if missing, follows redirects,
records non-2xx without raising so the pipeline can degrade per-page.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

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


def _canonicalize_url(url: httpx.URL) -> str:
    """Ensure bare-hostname URLs always include a trailing '/' on the path."""
    if url.path in ("", "/") and not url.query and not url.fragment:
        return str(url.copy_with(path="/"))
    return str(url)


async def fetch_lite(url: str, *, timeout: float = 15.0) -> FetchedPage:
    target = _normalize(url)
    async with httpx.AsyncClient(
        timeout=timeout, follow_redirects=True, headers={"User-Agent": _UA}
    ) as client:
        try:
            resp = await client.get(target)
        except httpx.HTTPError as exc:
            logging.getLogger(__name__).warning(
                "fetch_lite request failed; degrading to empty page",
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
    html = resp.text if resp.status_code == 200 else ""
    final_url = _canonicalize_url(resp.url)
    return FetchedPage(
        requested_url=target,
        final_url=final_url,
        status=resp.status_code,
        html=html,
        fetched_at=datetime.now(UTC),
    )
