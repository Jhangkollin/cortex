from __future__ import annotations

from uuid import UUID

from cortex_api.app.api.brand.dto import AnalyzeJobDTO, AnalyzeRequest
from cortex_api.service.brand.model.analysis_job import BrandProfileAnalysisJob


def test_analyze_request_validates_url() -> None:
    assert AnalyzeRequest(url="acmebank.asia").url == "acmebank.asia"


def test_job_dto_from_model_without_profile() -> None:
    job = BrandProfileAnalysisJob(
        brand_id=UUID("00000000-0000-0000-0000-000000000002"),
        source_url="x",
    )
    dto = AnalyzeJobDTO.from_model(job, profile=None)
    assert dto.status == "pending"
    assert dto.profile is None
    assert dto.job_id == job.id
