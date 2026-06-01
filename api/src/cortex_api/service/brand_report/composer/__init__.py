"""Brand report composer package.

Public API re-exports — existing imports are unchanged:

    from cortex_api.service.brand_report.composer import compose, compose_live, ReportSources, code
"""

from cortex_api.service.brand_report.composer.sections import (
    ReportSources,
    code,
    compose_live,
)
from cortex_api.service.brand_report.composer.synthesis import compose

__all__ = [
    "ReportSources",
    "code",
    "compose",
    "compose_live",
]
