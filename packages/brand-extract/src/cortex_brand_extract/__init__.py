"""cortex-brand-extract — URL → structured BrandProfile.

Public API. Stage functions are exported for granular MCP tools and tests.
"""

from __future__ import annotations

from cortex_brand_extract.corpus import build_corpus
from cortex_brand_extract.crawl import select_pages
from cortex_brand_extract.parse import parse_site
from cortex_brand_extract.pipeline import extract_brand_profile
from cortex_brand_extract.synthesize import synthesize_profile
from cortex_brand_extract.types import BrandProfile, ProviderConfig

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "extract_brand_profile",
    "BrandProfile",
    "ProviderConfig",
    "parse_site",
    "select_pages",
    "build_corpus",
    "synthesize_profile",
]
