"""Read-only repo backing the F2 eligible-brands API.

Joins ``brand_placement_settings`` with ``brand_publisher_scope`` AND
``brand_profile`` (for brand_name/description/topics) and filters to active
rows with a non-NULL ``composed_at`` (placement-ready per COR-56's quality
gate). Lang scoping comes from ``brand_publisher_scope.lang`` (added in
Task 1.5).
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from cortex_api.service.brand.model.profile import BrandProfile
from cortex_api.service.placement.model.scope import BrandPublisherScope
from cortex_api.service.placement.model.settings import BrandPlacementSettings
from cortex_api.service.placement.model.status import PlacementRowStatus

# Hard cap on rows returned per (publisher, lang). Forces caller to paginate
# before a runaway publisher's eligible set grows the cached blob or response
# payload unboundedly. Chosen well above realistic MVP volume ("single-digit
# per scope" per the AD3 spec); pagination — when needed — is a separate API
# evolution (cursor + total) coordinated with agent-ws.
_MAX_ROWS_PER_QUERY = 500


@dataclass(frozen=True, slots=True)
class EligibleBrandRow:
    """Flat row shape the service layer maps to DTO."""

    brand_uuid: UUID
    brand_name: str
    brand_description: str | None
    brand_topics: list[str]
    matching_keywords: list[str]
    matching_categories: list[str]
    matching_rules: str | None
    ad_ratio: float
    question_position: int
    mode: str
    brand_answer_prompt: str | None
    brand_question_prompt: str | None
    brand_cta_text: str | None
    brand_cta_url: str | None


class EligibleBrandsRepo:
    """Stateless: caller passes AsyncSession per call."""

    async def find_for_publisher(
        self,
        session: AsyncSession,
        publisher_uuid: UUID,
        lang: str,
    ) -> list[EligibleBrandRow]:
        """Return placement-ready brands scoped to (publisher_uuid, lang)."""
        stmt = (
            select(BrandPlacementSettings, BrandProfile)
            .join(
                BrandPublisherScope,
                BrandPublisherScope.brand_id == BrandPlacementSettings.brand_id,  # type: ignore[arg-type]
            )
            .join(
                BrandProfile,
                BrandProfile.brand_id == BrandPlacementSettings.brand_id,  # type: ignore[arg-type]
            )
            .where(BrandPublisherScope.publisher_id == publisher_uuid)
            .where(BrandPublisherScope.lang == lang)
            .where(BrandPublisherScope.status == PlacementRowStatus.ACTIVE)
            .where(BrandPlacementSettings.status == PlacementRowStatus.ACTIVE)
            .where(BrandPlacementSettings.composed_at.is_not(None))  # type: ignore[union-attr]
            .order_by(BrandPlacementSettings.composed_at.desc())  # type: ignore[union-attr]
            .limit(_MAX_ROWS_PER_QUERY)
        )
        result = await session.execute(stmt)
        # Each row is a tuple (BrandPlacementSettings, BrandProfile)
        rows: list[EligibleBrandRow] = []
        for settings_row, profile_row in result.all():
            rows.append(
                EligibleBrandRow(
                    brand_uuid=settings_row.brand_id,
                    brand_name=profile_row.name,
                    brand_description=profile_row.about,
                    brand_topics=list(profile_row.topics or []),
                    matching_keywords=list(settings_row.matching_keywords or []),
                    matching_categories=list(settings_row.matching_categories or []),
                    matching_rules=settings_row.matching_rules,
                    ad_ratio=float(settings_row.ad_ratio) if settings_row.ad_ratio is not None else 0.0,
                    question_position=settings_row.question_position or 1,
                    mode=settings_row.mode.value if settings_row.mode is not None else "question_replacement",
                    brand_answer_prompt=settings_row.brand_answer_prompt,
                    brand_question_prompt=settings_row.brand_question_prompt,
                    brand_cta_text=settings_row.brand_cta_text,
                    brand_cta_url=settings_row.brand_cta_url,
                )
            )
        return rows
