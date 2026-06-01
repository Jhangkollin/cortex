"""Smoke test: the SQLModel imports cleanly and constructs."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from cortex_api.service.placement.model.placement_compute_claim import (
    PlacementClaimStatus,
    PlacementComputeClaim,
)


def test_model_instantiation_minimal() -> None:
    """Construct with the AC's required fields; verify defaults."""
    now = datetime.now(tz=UTC)
    claim = PlacementComputeClaim(
        publisher_id=uuid.uuid4(),
        article_url_hash=b"\x00" * 32,
        claim_id=uuid.uuid4(),
        agent_ws_request_id="req-abc",
        brand_ids=[uuid.uuid4(), uuid.uuid4()],
        expires_at=now + timedelta(seconds=60),
    )
    assert claim.status == PlacementClaimStatus.IN_FLIGHT
    assert claim.completed_at is None
    assert claim.placement_audit_id is None


def test_status_enum_values() -> None:
    assert PlacementClaimStatus.IN_FLIGHT.value == "in_flight"
    assert PlacementClaimStatus.DONE.value == "done"
    assert PlacementClaimStatus.FAILED.value == "failed"
