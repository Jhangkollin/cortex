from __future__ import annotations

from uuid import UUID

from cortex_api.service.brand.model.analysis_job import (
    AnalyzeJobStatus,
    BrandProfileAnalysisJob,
)


def test_status_enum_values() -> None:
    assert [s.value for s in AnalyzeJobStatus] == [
        "pending",
        "running",
        "succeeded",
        "failed",
    ]


def test_job_defaults() -> None:
    job = BrandProfileAnalysisJob(
        brand_id=UUID("00000000-0000-0000-0000-000000000001"),
        source_url="acmebank.asia",
    )
    assert isinstance(job.id, UUID)
    assert job.status == AnalyzeJobStatus.PENDING
    assert job.cost_usd is None
    assert job.error is None
    assert job.__tablename__ == "brand_profile_analysis_job"
