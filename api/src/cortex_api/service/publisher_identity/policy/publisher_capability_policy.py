"""PublisherCapabilityPolicy — pure function mapping PublisherRole to capabilities.

Called at login / context switch to bake capabilities into JWT claims.
Per-request capability check is `cap in tenant.capabilities`, not a call here.
"""

from __future__ import annotations

from cortex_api.service.publisher_identity.model.publisher_capability import PublisherCapability
from cortex_api.service.publisher_identity.model.publisher_role import PublisherRole

_MATRIX: dict[PublisherRole, frozenset[PublisherCapability]] = {
    PublisherRole.VIEWER: frozenset(
        {
            PublisherCapability.VIEW_PUBLISHER_DASHBOARD,
            PublisherCapability.VIEW_PUBLISHER_KNOWLEDGE,
        }
    ),
    PublisherRole.EDITOR: frozenset(
        {
            PublisherCapability.VIEW_PUBLISHER_DASHBOARD,
            PublisherCapability.VIEW_PUBLISHER_KNOWLEDGE,
            PublisherCapability.MANAGE_PUBLISHER_KNOWLEDGE,
            PublisherCapability.MANAGE_PUBLISHER_PLACEMENTS,
            PublisherCapability.EDIT_PUBLISHER_SETTINGS,
        }
    ),
    PublisherRole.ADMIN: frozenset(PublisherCapability),  # everything
}


class PublisherCapabilityPolicy:
    """Publisher role → capability resolution. Pure, stateless."""

    @staticmethod
    def resolve(role: PublisherRole) -> tuple[PublisherCapability, ...]:
        """Return the full capability tuple for a role. Called at login."""
        return tuple(sorted(_MATRIX[role], key=lambda c: c.value))

    @staticmethod
    def allows(role: PublisherRole, capability: PublisherCapability) -> bool:
        """Pure check — only tests / admin endpoints use this."""
        return capability in _MATRIX[role]
