"""BrandIdentityService — brand-side use cases.

Called at login / context switch (DB hits here) and from admin endpoints.
Hot-path requests don't call this; they read `BrandTenantCtx` from JWT.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

import structlog

from cortex_api.core.exceptions import (
    ConflictError,
    ForbiddenError,
    MembershipError,
    NotFoundError,
)
from cortex_api.infra.database_client import DatabaseClient
from cortex_api.service.brand_identity.config import Config
from cortex_api.service.brand_identity.model.brand import Brand
from cortex_api.service.brand_identity.model.brand_capability import BrandCapability
from cortex_api.service.brand_identity.model.brand_membership import BrandMembership
from cortex_api.service.brand_identity.model.brand_role import BrandRole
from cortex_api.service.brand_identity.model.brand_tenant_ctx import BrandTenantCtx
from cortex_api.service.brand_identity.policy.brand_capability_policy import (
    BrandCapabilityPolicy,
)
from cortex_api.service.brand_identity.repo.brand_membership_repo import BrandMembershipRepo
from cortex_api.service.brand_identity.repo.brand_repo import BrandRepo


class BrandIdentityService:
    """Brand-side identity operations."""

    def __init__(
        self,
        database_client: DatabaseClient,
        brand_repo: BrandRepo,
        membership_repo: BrandMembershipRepo,
        config: Config,
    ) -> None:
        self._logger = structlog.get_logger(__name__)
        self._db = database_client
        self._brand_repo = brand_repo
        self._membership_repo = membership_repo
        self._config = config

    # -- onboarding (self-serve brand creation) ------------------------------

    async def create_brand_with_admin(
        self,
        user_id: UUID,
        display_name: str,
    ) -> tuple[Brand, BrandMembership]:
        """Create a new, independent brand + ADMIN founder membership for the caller.

        Multi-brand: every call creates a fresh brand (its own `brand_id`,
        profile, and derived data) and never overrides an existing one — so a
        user can found more than one brand. Onboarding always lands here to
        create-new; editing an existing brand is a separate flow. (The old
        one-founder-per-user partial UNIQUE index was dropped in migration
        7ab199ba95a2.) The `UniqueConstraint(user_id, brand_id)` still prevents
        a duplicate membership in the *same* brand.
        """
        async with self._db.session() as session:
            brand = Brand(display_name=display_name)
            brand = await self._brand_repo.create(session, brand)

            membership = BrandMembership(
                user_id=user_id,
                brand_id=brand.id,
                role=BrandRole.ADMIN,
                invited_by=None,
            )
            membership = await self._membership_repo.create(session, membership)

        self._logger.info(
            "brand_created_with_admin",
            user_id=str(user_id),
            brand_id=str(brand.id),
        )
        return brand, membership

    async def list_my_brands(self, user_id: UUID) -> list[tuple[Brand, BrandRole]]:
        """List the caller's own brands. Pure read; no capability gate needed —
        by definition the user can see brands they have membership in.

        The router projects (Brand, BrandRole) rows into BrandListItem DTOs.
        """
        async with self._db.session() as session:
            return await self._brand_repo.list_for_user_id(session, user_id)

    # -- read ----------------------------------------------------------------

    async def get_brand(self, brand_id: UUID) -> Brand:
        async with self._db.session() as session:
            brand = await self._brand_repo.get_by_id(session, brand_id)
            if brand is None:
                raise NotFoundError(f"brand {brand_id} not found")
            return brand

    # -- update (settings page / wizard) -------------------------------------

    async def update_brand(
        self,
        actor: BrandTenantCtx,
        display_name: str | None = None,
        industry: str | None = None,
        domain: str | None = None,
    ) -> Brand:
        """Update brand attributes. Requires `EDIT_BRAND_SETTINGS` capability.

        Only fields explicitly passed (not None) are written — partial PATCH
        semantics.
        """
        if BrandCapability.EDIT_BRAND_SETTINGS not in actor.capabilities:
            raise ForbiddenError("edit_brand_settings capability required")

        fields: dict[str, object] = {}
        if display_name is not None:
            fields["display_name"] = display_name
        if industry is not None:
            fields["industry"] = industry
        if domain is not None:
            fields["domain"] = domain
        if not fields:
            return await self.get_brand(actor.brand_id)

        async with self._db.session() as session:
            brand = await self._brand_repo.get_by_id(session, actor.brand_id)
            if brand is None:
                raise NotFoundError(f"brand {actor.brand_id} not found")
            brand = await self._brand_repo.update_fields(session, brand, **fields)
            self._logger.info(
                "brand_updated",
                brand_id=str(actor.brand_id),
                user_id=str(actor.user_id),
                fields=list(fields.keys()),
            )
            return brand

    # -- onboarding completion stamp ----------------------------------------

    async def mark_onboarded(self, actor: BrandTenantCtx) -> Brand:
        """Stamp `brand.onboarded_at` once. Idempotent: a second call is a
        no-op and returns the brand unchanged. Requires `EDIT_BRAND_SETTINGS`.
        """
        if BrandCapability.EDIT_BRAND_SETTINGS not in actor.capabilities:
            raise ForbiddenError("edit_brand_settings capability required")

        async with self._db.session() as session:
            brand = await self._brand_repo.get_by_id(session, actor.brand_id)
            if brand is None:
                raise NotFoundError(f"brand {actor.brand_id} not found")
            if brand.onboarded_at is None:
                brand = await self._brand_repo.update_fields(session, brand, onboarded_at=datetime.utcnow())
                self._logger.info(
                    "brand_onboarded",
                    brand_id=str(actor.brand_id),
                    user_id=str(actor.user_id),
                )
            return brand

    # -- login / context-switch path ----------------------------------------

    async def enter_brand(self, user_id: UUID, brand_id: UUID) -> BrandTenantCtx:
        """Verify membership and produce a BrandTenantCtx ready to bake into JWT.

        Called at login (per membership) and at context switch. Raises
        `MembershipError` if the user has no membership. The brand row
        itself is not fetched — the FK constraint on `brand_membership.brand_id`
        guarantees the brand exists whenever a membership row exists, so a
        defensive `get_by_id` would just be a redundant DB roundtrip.
        """
        async with self._db.session() as session:
            membership = await self._membership_repo.get(session, user_id, brand_id)
            if membership is None:
                raise MembershipError(f"user {user_id} has no membership in brand {brand_id}")

        capabilities = BrandCapabilityPolicy.resolve(membership.role)
        return BrandTenantCtx(
            user_id=user_id,
            brand_id=brand_id,
            role=membership.role,
            capabilities=capabilities,
        )

    async def list_user_brands(self, user_id: UUID) -> list[tuple[Brand, BrandTenantCtx]]:
        """List every (brand, resolved-context) pair the user can enter.

        Used at login to populate the workspace picker / determine default
        active context. Filters out archived brands.
        """
        async with self._db.session() as session:
            memberships = await self._membership_repo.list_for_user(session, user_id)
            if not memberships:
                return []
            results: list[tuple[Brand, BrandTenantCtx]] = []
            for membership in memberships:
                brand = await self._brand_repo.get_by_id(session, membership.brand_id)
                if brand is None or brand.archived_at is not None:
                    continue
                capabilities = BrandCapabilityPolicy.resolve(membership.role)
                ctx = BrandTenantCtx(
                    user_id=user_id,
                    brand_id=brand.id,
                    role=membership.role,
                    capabilities=capabilities,
                )
                results.append((brand, ctx))
            return results

    # -- admin operations ---------------------------------------------------

    async def grant_brand_membership(
        self,
        actor: BrandTenantCtx,
        invitee_user_id: UUID,
        role: BrandRole,
    ) -> BrandMembership:
        """Add a user to the actor's brand at the given role.

        Requires `MANAGE_BRAND_USERS` capability on the actor.
        """
        if BrandCapability.MANAGE_BRAND_USERS not in actor.capabilities:
            raise ForbiddenError("manage_brand_users capability required")
        async with self._db.session() as session:
            existing = await self._membership_repo.get(session, invitee_user_id, actor.brand_id)
            if existing is not None:
                raise ConflictError(f"user {invitee_user_id} already has a membership in brand {actor.brand_id}")
            membership = BrandMembership(
                user_id=invitee_user_id,
                brand_id=actor.brand_id,
                role=role,
                invited_by=actor.user_id,
            )
            return await self._membership_repo.create(session, membership)

    async def revoke_brand_membership(
        self,
        actor: BrandTenantCtx,
        membership_id: UUID,
    ) -> None:
        """Remove a membership row. Requires `MANAGE_BRAND_USERS` capability."""
        if BrandCapability.MANAGE_BRAND_USERS not in actor.capabilities:
            raise ForbiddenError("manage_brand_users capability required")
        async with self._db.session() as session:
            await self._membership_repo.delete(session, membership_id)
