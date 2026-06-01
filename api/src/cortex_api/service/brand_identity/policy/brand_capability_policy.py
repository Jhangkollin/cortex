"""BrandCapabilityPolicy — pure function mapping BrandRole to BrandCapability set.

Called at login / context switch to bake capabilities into JWT claims.
Per-request capability check is `cap in tenant.capabilities`, not a call here.

Single source of truth for the brand-side (role → capabilities) matrix.
Frontend reads the resolved capability list from JWT; backend re-validates
per route. Two consumers, one truth.
"""

from __future__ import annotations

from cortex_api.service.brand_identity.model.brand_capability import BrandCapability
from cortex_api.service.brand_identity.model.brand_role import BrandRole

_MATRIX: dict[BrandRole, frozenset[BrandCapability]] = {
    BrandRole.VIEWER: frozenset(
        {
            BrandCapability.VIEW_BRAND_DASHBOARD,
            BrandCapability.VIEW_BRAND_KNOWLEDGE,
            BrandCapability.VIEW_BRAND_CONNECTORS,
        }
    ),
    BrandRole.EDITOR: frozenset(
        {
            BrandCapability.VIEW_BRAND_DASHBOARD,
            BrandCapability.VIEW_BRAND_KNOWLEDGE,
            BrandCapability.MANAGE_BRAND_KNOWLEDGE,
            BrandCapability.VIEW_BRAND_CONNECTORS,
            BrandCapability.MANAGE_BRAND_CONNECTORS,
            BrandCapability.EDIT_BRAND_SETTINGS,
        }
    ),
    BrandRole.ADMIN: frozenset(BrandCapability),  # everything
}


class BrandCapabilityPolicy:
    """Brand role → capability resolution. Pure, stateless."""

    @staticmethod
    def resolve(role: BrandRole) -> tuple[BrandCapability, ...]:
        """Return the full capability tuple for a role.

        Called at login. Sorted for stable JWT claim ordering (caches better).
        """
        return tuple(sorted(_MATRIX[role], key=lambda c: c.value))

    @staticmethod
    def allows(role: BrandRole, capability: BrandCapability) -> bool:
        """Pure check — only used in tests / admin endpoints. Hot path
        consults `tenant.capabilities` directly."""
        return capability in _MATRIX[role]
