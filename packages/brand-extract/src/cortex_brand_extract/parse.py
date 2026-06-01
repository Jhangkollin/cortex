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
