"""Media-network DTOs — API projection layer over BrandMediaNetwork."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel

from cortex_api.service.media_network.model.job import BrandMediaNetwork


class MediaNetworkResponse(BaseModel):
    """Response shape for both POST (start) and GET (poll) media-network endpoints."""

    brand_id: UUID
    status: str
    outlets: list[dict[str, Any]]
    error: str | None = None

    @classmethod
    def from_model(cls, m: BrandMediaNetwork) -> MediaNetworkResponse:
        # MediaJobStatus is a StrEnum: str(m.status) yields the bare value
        # e.g. "succeeded", not "MediaJobStatus.SUCCEEDED".
        return cls(
            brand_id=m.brand_id,
            status=m.status.value,
            outlets=m.outlets,
            error=m.error,
        )
