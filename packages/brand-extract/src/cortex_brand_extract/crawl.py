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


def _depth(url: str) -> int:
    return urlparse(url).path.strip("/").count("/")


def select_pages(homepage: str, internal_links: list[str], *, max_pages: int) -> list[str]:
    ranked = sorted(
        (u for u in internal_links if u.rstrip("/") != homepage.rstrip("/")),
        key=lambda u: (-_score(u), _depth(u)),
    )
    keep = [u for u in ranked if _score(u) >= 0][: max(0, max_pages - 1)]
    return [homepage, *keep]
