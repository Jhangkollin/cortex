from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from cortex_api.service.brand_report.contract import (
    INSUFFICIENT_DATA,
    ReportDTO,
    SectionStatusBody,
)


def _minimal_kwargs() -> dict[str, Any]:
    return {
        "meta": {
            "subject": "Acme",
            "enName": "Acme",
            "legalName": None,
            "domain": "acme.tw",
            "primaryMarket": "台灣",
            "extendedMarkets": [],
            "reportDate": "2026-05-24",
            "windowFrom": "2025-05-24",
            "windowTo": "2026-05-24",
            "monogram": "A",
            "brandColor": None,
            "tagline": None,
            "founded": None,
            "category": "金融",
            "confidence": 90,
            "reportId": "BIQ-2026-05-24-ACME",
            "pageCount": 8,
            "preparedFor": "Brand",
            "preparedBy": "Cortex",
        },
        "core": [],
        "coreJudgement": "",
        "productLines": [],
        "productNote": "",
        "subBrands": [],
        "endorsements": {"status": INSUFFICIENT_DATA, "body": "x"},
        "ipCollabs": {"status": INSUFFICIENT_DATA, "body": "x"},
        "mediaNetwork": [],
        "competitors": [],
        "competitorNote": "",
        "insights": {"confirmed": [], "inferences": [], "hypotheses": []},
        "faq": [],
        "channels": [],
        "risks": [],
        "sources": {"A": [], "B": [], "C": []},
        "quality": {"high": "", "midLow": "", "gaps": "", "conflicts": "", "open": ""},
    }


def test_report_dto_round_trips_to_brand_iq_camelcase() -> None:
    dto = ReportDTO(**_minimal_kwargs())
    dumped = dto.model_dump()
    assert dumped["meta"]["enName"] == "Acme"
    assert dumped["endorsements"]["status"] == "資料不足"
    assert set(dumped) >= {
        "meta",
        "core",
        "productLines",
        "subBrands",
        "endorsements",
        "ipCollabs",
        "mediaNetwork",
        "competitors",
        "insights",
        "faq",
        "channels",
        "risks",
        "sources",
        "quality",
    }


def test_report_dto_is_frozen() -> None:
    dto = ReportDTO(**_minimal_kwargs())
    with pytest.raises(ValidationError):
        dto.coreJudgement = "mutated"


def test_report_dto_nested_models_are_frozen() -> None:
    dto = ReportDTO(**_minimal_kwargs())
    with pytest.raises(ValidationError):
        dto.meta.enName = "mutated"


def test_insufficient_constant_is_the_honesty_marker() -> None:
    assert INSUFFICIENT_DATA == "資料不足"
    SectionStatusBody(status=INSUFFICIENT_DATA, body="no evidence")
