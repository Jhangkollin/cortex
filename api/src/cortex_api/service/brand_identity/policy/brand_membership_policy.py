"""BrandMembershipPolicy — pure function that gates access to a brand.

Called at login / context switch (once per session), not per request.
Result is captured in JWT claims; hot path never re-runs this.
"""

from __future__ import annotations

from cortex_api.service.brand_identity.model.brand_membership import BrandMembership
from cortex_api.service.brand_identity.model.brand_role import BrandRole


class BrandMembershipPolicy:
    """Brand membership / role admission rules. Pure, stateless."""

    @staticmethod
    def can_enter(membership: BrandMembership | None) -> bool:
        """A user can enter a brand iff they have a membership row.

        Returns False on `None` (no membership). Subclasses can extend this
        for additional constraints (e.g. archived brand, suspended user).
        """
        return membership is not None

    @staticmethod
    def can_act_as(membership: BrandMembership | None, required: BrandRole) -> bool:
        """Whether the user's role meets or exceeds the required role.

        Role hierarchy: viewer < editor < admin.
        """
        if membership is None:
            return False
        hierarchy = {BrandRole.VIEWER: 0, BrandRole.EDITOR: 1, BrandRole.ADMIN: 2}
        return hierarchy[membership.role] >= hierarchy[required]
