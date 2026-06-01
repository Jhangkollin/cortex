"""DTO for the F2 eligible-brands API.

14 fields per AD3 (placement-runtime-design.md v5).
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class EligibleBrandDTO(BaseModel):
    brand_uuid: UUID
    brand_name: str
    brand_description: str | None
    brand_topics: list[str]
    matching_keywords: list[str]
    matching_categories: list[str]
    matching_rules: str | None
    ad_ratio: float
    question_position: int = Field(ge=1)
    mode: str
    brand_answer_prompt: str | None
    brand_question_prompt: str | None
    brand_cta_text: str | None
    brand_cta_url: str | None
