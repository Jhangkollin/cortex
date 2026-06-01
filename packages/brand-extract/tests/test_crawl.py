from cortex_brand_extract.crawl import select_pages


def test_select_prioritizes_high_signal_paths_and_bounds_count() -> None:
    links = [
        "https://acme.com/about",
        "https://acme.com/products/card",
        "https://acme.com/press/2025",
        "https://acme.com/careers/intern",
        "https://acme.com/legal/cookies",
        "https://acme.com/pricing",
        "https://acme.com/blog/post-1",
    ]
    chosen = select_pages("https://acme.com/", links, max_pages=4)
    assert "https://acme.com/about" in chosen
    assert "https://acme.com/products/card" in chosen
    assert "https://acme.com/pricing" in chosen
    assert len(chosen) == 4
    assert "https://acme.com/legal/cookies" not in chosen


def test_homepage_always_first() -> None:
    chosen = select_pages("https://acme.com/", ["https://acme.com/about"], max_pages=3)
    assert chosen[0] == "https://acme.com/"
