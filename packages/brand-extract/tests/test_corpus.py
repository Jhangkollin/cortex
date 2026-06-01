from cortex_brand_extract.corpus import SiteCorpus, build_corpus


def test_corpus_concatenates_pages_and_bounds_chars() -> None:
    pages = [
        ("https://acme.com/", "Acme home " * 50),
        ("https://acme.com/about", "About Acme " * 50),
    ]
    corpus = build_corpus(pages, max_chars=120)
    assert isinstance(corpus, SiteCorpus)
    assert len(corpus.text) <= 120 + 80  # bound + per-page header allowance
    assert "https://acme.com/" in corpus.text
    assert corpus.page_count == 2
    assert corpus.truncated is True


def test_corpus_not_truncated_when_small() -> None:
    corpus = build_corpus([("https://acme.com/", "short")], max_chars=10_000)
    assert corpus.truncated is False
