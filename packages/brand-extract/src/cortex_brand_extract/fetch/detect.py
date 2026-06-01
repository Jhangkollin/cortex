"""Heuristic: does this HTML look like an unrendered SPA shell? Used to set
`js_detected` and recommend the deep tier — never to silently return garbage.
"""

from __future__ import annotations

from selectolax.parser import HTMLParser

_MIN_VISIBLE_CHARS = 200


def looks_js_rendered(html: str) -> tuple[bool, str]:
    if not html.strip():
        return True, "empty response body"
    tree = HTMLParser(html)
    body = tree.body
    text = (body.text(separator=" ", strip=True) if body else "").strip()
    if len(text) < _MIN_VISIBLE_CHARS:
        scripts = len(tree.css("script"))
        return True, f"only {len(text)} visible chars with {scripts} script tags"
    return False, ""
