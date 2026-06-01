"""Brand-voice DTOs — API projection layer over BrandVoice."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel

from cortex_api.service.voice.model.job import BrandVoice


class BrandVoiceResponse(BaseModel):
    """Response shape for both POST (start) and GET (poll) brand-voice endpoints."""

    brand_id: UUID
    status: str
    samples: dict[str, str]
    error: str | None = None

    @classmethod
    def from_model(cls, m: BrandVoice) -> BrandVoiceResponse:
        # VoiceJobStatus is a StrEnum: m.status.value yields the bare value
        # e.g. "succeeded", not "VoiceJobStatus.SUCCEEDED".
        return cls(
            brand_id=m.brand_id,
            status=m.status.value,
            samples=m.samples,
            error=m.error,
        )
