"""BrandTenantCtx — the keystone value object passed through every brand route.

Constructed by `app/dependencies/brand.py::active_brand` from JWT claims.
Carries authorized identity + permission for one request, never persisted.

Construction = authorization. If you have a `BrandTenantCtx`, you have already
been verified as having a membership for that brand with the captured role
and capabilities.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict

from cortex_api.service.brand_identity.model.brand_capability import BrandCapability
from cortex_api.service.brand_identity.model.brand_role import BrandRole


class BrandTenantCtx(BaseModel):
    """Per-request brand tenant context. Frozen, value-equal, hashable-friendly."""

    model_config = ConfigDict(frozen=True)

    user_id: UUID
    brand_id: UUID
    role: BrandRole
    capabilities: tuple[BrandCapability, ...]
