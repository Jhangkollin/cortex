"""PublisherTenantCtx — keystone value object for publisher routes.

Mirror of BrandTenantCtx. Construction by `app/dependencies/publisher.py
::active_publisher` is the act of authorizing.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict

from cortex_api.service.publisher_identity.model.publisher_capability import PublisherCapability
from cortex_api.service.publisher_identity.model.publisher_role import PublisherRole


class PublisherTenantCtx(BaseModel):
    """Per-request publisher tenant context."""

    model_config = ConfigDict(frozen=True)

    user_id: UUID
    publisher_id: UUID
    role: PublisherRole
    capabilities: tuple[PublisherCapability, ...]
