"""Capability gates — `Depends(requires_brand_capability(...))` per route.

Pure Python set check against `tenant.capabilities` — zero DB. Capability list
is resolved at login by BrandCapabilityPolicy / PublisherCapabilityPolicy and
baked into JWT claims; this dep just verifies presence.
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends

from cortex_api.app.dependencies.brand import active_brand
from cortex_api.app.dependencies.publisher import active_publisher
from cortex_api.core.exceptions import ForbiddenError
from cortex_api.service.brand_identity.model.brand_capability import BrandCapability
from cortex_api.service.brand_identity.model.brand_tenant_ctx import BrandTenantCtx
from cortex_api.service.publisher_identity.model.publisher_capability import PublisherCapability
from cortex_api.service.publisher_identity.model.publisher_tenant_ctx import PublisherTenantCtx


def requires_brand_capability(cap: BrandCapability) -> Callable[..., None]:
    """Build a Depends that checks the brand tenant has `cap`."""

    def _check(tenant: BrandTenantCtx = Depends(active_brand)) -> None:
        if cap not in tenant.capabilities:
            raise ForbiddenError(f"missing brand capability: {cap.value}")

    return _check


def requires_publisher_capability(cap: PublisherCapability) -> Callable[..., None]:
    """Build a Depends that checks the publisher tenant has `cap`."""

    def _check(tenant: PublisherTenantCtx = Depends(active_publisher)) -> None:
        if cap not in tenant.capabilities:
            raise ForbiddenError(f"missing publisher capability: {cap.value}")

    return _check
