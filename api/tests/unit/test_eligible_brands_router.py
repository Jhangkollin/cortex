"""Unit tests for the eligible-brands router (DTO validation only — full
stack including auth in integration suite)."""

from __future__ import annotations

from uuid import UUID

import pytest

from cortex_api.app.api.eligible_brands.dto import EligibleBrandDTO


def _valid_dto_kwargs() -> dict:
    return {
        "brand_uuid": UUID(int=1),
        "brand_name": "Acme",
        "brand_description": "desc",
        "brand_topics": ["t"],
        "matching_keywords": ["k"],
        "matching_categories": ["c"],
        "matching_rules": "rules",
        "ad_ratio": 0.5,
        "question_position": 2,
        "mode": "question_replacement",
        "brand_answer_prompt": "a",
        "brand_question_prompt": "q",
        "brand_cta_text": "cta",
        "brand_cta_url": "https://x",
    }


def test_dto_has_all_13_fields() -> None:
    dto = EligibleBrandDTO(
        brand_uuid=UUID(int=1),
        brand_name="Acme",
        brand_description="desc",
        brand_topics=["t"],
        matching_keywords=["k"],
        matching_categories=["c"],
        matching_rules="rules",
        ad_ratio=0.5,
        question_position=2,
        mode="question_replacement",
        brand_answer_prompt="a",
        brand_question_prompt="q",
        brand_cta_text="cta",
        brand_cta_url="https://x",
    )
    j = dto.model_dump()
    expected = {
        "brand_uuid",
        "brand_name",
        "brand_description",
        "brand_topics",
        "matching_keywords",
        "matching_categories",
        "matching_rules",
        "ad_ratio",
        "question_position",
        "mode",
        "brand_answer_prompt",
        "brand_question_prompt",
        "brand_cta_text",
        "brand_cta_url",
    }
    assert set(j.keys()) == expected


def test_dto_rejects_question_position_zero() -> None:
    """ge=1 constraint surfaces in API schema and rejects 0."""
    kwargs = _valid_dto_kwargs()
    kwargs["question_position"] = 0
    with pytest.raises(ValueError, match="greater than or equal to 1"):
        EligibleBrandDTO(**kwargs)


def test_dto_rejects_question_position_negative() -> None:
    kwargs = _valid_dto_kwargs()
    kwargs["question_position"] = -5
    with pytest.raises(ValueError, match="greater than or equal to 1"):
        EligibleBrandDTO(**kwargs)


def test_dto_accepts_question_position_one() -> None:
    kwargs = _valid_dto_kwargs()
    kwargs["question_position"] = 1
    dto = EligibleBrandDTO(**kwargs)
    assert dto.question_position == 1
