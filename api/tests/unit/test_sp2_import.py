"""SP-2 (cortex-brand-extract) must be importable from cortex-api."""


def test_cortex_brand_extract_importable() -> None:
    from cortex_brand_extract import BrandProfile, ProviderConfig, extract_brand_profile

    assert callable(extract_brand_profile)
    assert BrandProfile.__name__ == "BrandProfile"
    assert ProviderConfig.__name__ == "ProviderConfig"


def test_claude_provider_importable() -> None:
    from cortex_brand_extract.llm.claude import ClaudeProvider

    assert ClaudeProvider.__name__ == "ClaudeProvider"
