"""Unit tests for placement SQLModel definitions.

Smoke-level checks: enum value sets, instance defaults. Constraint
enforcement (FK, ENUM bounds at the DB level) lives in the integration
suite — Postgres is the SSOT for those.
"""

from __future__ import annotations

from uuid import uuid4

from cortex_api.service.placement.model.audit import PlacementAudit
from cortex_api.service.placement.model.publisher_config import (
    PublisherPlacementConfig,
)
from cortex_api.service.placement.model.scope import BrandPublisherScope
from cortex_api.service.placement.model.settings import (
    BrandPlacementSettings,
    PlacementMode,
)
from cortex_api.service.placement.model.status import PlacementRowStatus


def test_placement_mode_enum_values() -> None:
    assert {m.value for m in PlacementMode} == {
        "question_replacement",
        "answer_only",
        "both",
    }


def test_placement_row_status_enum_values() -> None:
    """Single shared enum across settings + scope (locked 2026-05-21)."""
    assert {s.value for s in PlacementRowStatus} == {"active", "inactive"}


def test_brand_placement_settings_defaults() -> None:
    """D1 (locked 2026-05-21): overrides_mask defaults to {} so a freshly
    composed row carries 'no user overrides yet'. status defaults to
    ACTIVE so the eligible-brands API treats a placement-ready row as
    eligible without an explicit field set. composed_at defaults to None
    until the composer (COR-56) writes it.
    """
    s = BrandPlacementSettings(brand_id=uuid4())
    assert s.overrides_mask == {}
    assert s.status == PlacementRowStatus.ACTIVE
    assert s.composed_at is None


def test_brand_placement_settings_pre_compose_columns_optional() -> None:
    """Per design § Schema changes, mid-compose nullable columns must be
    constructible as None so the composer can write a row in any order
    without per-field placeholders.
    """
    s = BrandPlacementSettings(brand_id=uuid4())
    assert s.use_dynamic_question is None
    assert s.question_position is None
    assert s.ad_ratio is None
    assert s.mode is None
    assert s.matching_rules is None
    assert s.matching_keywords is None
    assert s.matching_categories is None
    assert s.brand_answer_prompt is None
    assert s.brand_question_prompt is None
    assert s.brand_cta_text is None
    assert s.brand_cta_url is None


def test_brand_placement_settings_question_position_rejects_zero() -> None:
    """question_position is 1-indexed (downstream PHP burst endpoint rejects 0).
    The __init__ override must raise on 0 or negative values.
    """
    import pytest

    with pytest.raises(ValueError, match="question_position must be >= 1"):
        BrandPlacementSettings(brand_id=uuid4(), question_position=0)


def test_brand_placement_settings_question_position_rejects_negative() -> None:
    import pytest

    with pytest.raises(ValueError, match="question_position must be >= 1"):
        BrandPlacementSettings(brand_id=uuid4(), question_position=-1)


def test_brand_placement_settings_question_position_accepts_one() -> None:
    s = BrandPlacementSettings(brand_id=uuid4(), question_position=1)
    assert s.question_position == 1


def test_brand_placement_settings_question_position_accepts_none() -> None:
    """None is valid — pre-compose state where the field hasn't been set yet."""
    s = BrandPlacementSettings(brand_id=uuid4(), question_position=None)
    assert s.question_position is None


def test_brand_publisher_scope_defaults() -> None:
    s = BrandPublisherScope(brand_id=uuid4(), publisher_id=uuid4())
    assert s.status == PlacementRowStatus.ACTIVE


def test_publisher_placement_config_constructible() -> None:
    c = PublisherPlacementConfig(publisher_id=uuid4())
    assert c.global_match_ratio is None


def test_placement_audit_defaults() -> None:
    """selection_weight is mandatory (winner's confidence × ad_ratio);
    the losing_candidates jsonb defaults to [] so an audit row with a
    single eligible brand can still be written.
    """
    a = PlacementAudit(
        id=uuid4(),
        brand_id=uuid4(),
        publisher_id=uuid4(),
        article_url="https://example.test/x",
        article_url_hash="0" * 64,
        question_text="q",
        answer_text="a",
        placement_position=0,
        rationale="r",
        selection_weight=0.42,
        trace_id="t",
        parent_trace_id="pt",
    )
    assert a.losing_candidates == []
