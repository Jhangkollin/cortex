"""Weekly-questions DTOs — API projection layer over BrandWeeklyQuestions."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel

from cortex_api.service.questions.model.job import BrandWeeklyQuestions


class WeeklyQuestionsResponse(BaseModel):
    """Response shape for both POST (start) and GET (poll) weekly-questions endpoints."""

    brand_id: UUID
    status: str
    questions: list[dict[str, Any]]
    error: str | None = None

    @classmethod
    def from_model(cls, m: BrandWeeklyQuestions) -> WeeklyQuestionsResponse:
        # QuestionJobStatus is a StrEnum: m.status.value yields the bare value
        # e.g. "succeeded", not "QuestionJobStatus.SUCCEEDED".
        return cls(
            brand_id=m.brand_id,
            status=m.status.value,
            questions=m.questions,
            error=m.error,
        )
