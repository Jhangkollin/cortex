from cortex_brand_extract.fetch.detect import looks_js_rendered

_RICH = "<html><body>" + "<p>Acme Bank serves millions across Asia.</p>" * 40 + "</body></html>"
_SPA = '<html><body><div id="root"></div><script src="/app.js"></script></body></html>'


def test_rich_static_page_is_not_flagged() -> None:
    flagged, _ = looks_js_rendered(_RICH)
    assert flagged is False


def test_spa_shell_is_flagged() -> None:
    flagged, reason = looks_js_rendered(_SPA)
    assert flagged is True
    assert reason
    assert "chars" in reason
