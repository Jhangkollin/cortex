"""PublisherMembershipPolicy — pure function that gates publisher access."""

from __future__ import annotations

from cortex_api.service.publisher_identity.model.publisher_membership import PublisherMembership
from cortex_api.service.publisher_identity.model.publisher_role import PublisherRole


class PublisherMembershipPolicy:
    """Publisher membership / role admission rules. Pure, stateless."""

    @staticmethod
    def can_enter(membership: PublisherMembership | None) -> bool:
        return membership is not None

    @staticmethod
    def can_act_as(membership: PublisherMembership | None, required: PublisherRole) -> bool:
        if membership is None:
            return False
        hierarchy = {PublisherRole.VIEWER: 0, PublisherRole.EDITOR: 1, PublisherRole.ADMIN: 2}
        return hierarchy[membership.role] >= hierarchy[required]
