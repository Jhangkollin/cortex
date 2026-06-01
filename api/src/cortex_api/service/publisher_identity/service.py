"""PublisherIdentityService — publisher-side use cases. Mirror of BrandIdentityService."""

from __future__ import annotations

from uuid import UUID

import structlog

from cortex_api.core.exceptions import ForbiddenError
from cortex_api.service.publisher_identity.config import Config
from cortex_api.service.publisher_identity.model.publisher import Publisher
from cortex_api.service.publisher_identity.model.publisher_capability import PublisherCapability
from cortex_api.service.publisher_identity.model.publisher_membership import PublisherMembership
from cortex_api.service.publisher_identity.model.publisher_role import PublisherRole
from cortex_api.service.publisher_identity.model.publisher_tenant_ctx import PublisherTenantCtx
from cortex_api.service.publisher_identity.repo.publisher_membership_repo import PublisherMembershipRepo
from cortex_api.service.publisher_identity.repo.publisher_repo import PublisherRepo


class PublisherIdentityService:
    """Publisher-side identity operations."""

    def __init__(
        self,
        publisher_repo: PublisherRepo,
        membership_repo: PublisherMembershipRepo,
        config: Config,
    ) -> None:
        self._logger = structlog.get_logger(__name__)
        self._publisher_repo = publisher_repo
        self._membership_repo = membership_repo
        self._config = config

    # -- login / context-switch path ----------------------------------------

    async def enter_publisher(self, user_id: UUID, publisher_id: UUID) -> PublisherTenantCtx:
        """Verify membership and produce a PublisherTenantCtx ready to bake into JWT."""
        raise NotImplementedError("PublisherIdentityService.enter_publisher — implement in auth slice")

    async def list_user_publishers(self, user_id: UUID) -> list[tuple[Publisher, PublisherTenantCtx]]:
        """List every (publisher, resolved-context) pair the user can enter."""
        raise NotImplementedError("PublisherIdentityService.list_user_publishers — implement in auth slice")

    # -- admin operations ---------------------------------------------------

    async def grant_publisher_membership(
        self,
        actor: PublisherTenantCtx,
        invitee_user_id: UUID,
        role: PublisherRole,
    ) -> PublisherMembership:
        if PublisherCapability.MANAGE_PUBLISHER_USERS not in actor.capabilities:
            raise ForbiddenError("manage_publisher_users capability required")
        raise NotImplementedError("PublisherIdentityService.grant_publisher_membership — implement in admin slice")

    async def revoke_publisher_membership(
        self,
        actor: PublisherTenantCtx,
        membership_id: UUID,
    ) -> None:
        if PublisherCapability.MANAGE_PUBLISHER_USERS not in actor.capabilities:
            raise ForbiddenError("manage_publisher_users capability required")
        raise NotImplementedError("PublisherIdentityService.revoke_publisher_membership — implement in admin slice")
