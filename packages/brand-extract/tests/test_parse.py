from pathlib import Path

from cortex_brand_extract.parse import SiteMetadata, parse_site

_HTML = (Path(__file__).parent / "fixtures" / "acme_home.html").read_text()


def test_parse_extracts_core_metadata() -> None:
    md = parse_site("https://acmebank.asia/", _HTML)
    assert isinstance(md, SiteMetadata)
    assert md.title.startswith("Acme Bank Asia")
    assert md.description and "3.2M households" in md.description
    assert md.og_image == "https://acmebank.asia/logo.png"
    assert md.theme_color == "#225D59"
    assert md.favicon == "https://acmebank.asia/favicon.ico"
    assert md.jsonld_org_name == "Acme Bank Asia Holdings, Ltd."
    assert md.founded == "1998"


def test_parse_collects_internal_links_only() -> None:
    md = parse_site("https://acmebank.asia/", _HTML)
    assert "https://acmebank.asia/about" in md.internal_links
    assert "https://acmebank.asia/credit-cards/world-elite" in md.internal_links
    assert all("twitter.com" not in link for link in md.internal_links)
