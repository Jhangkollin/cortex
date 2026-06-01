"""Unit tests for BrandReportUiStateService — fake repo, no DB required."""

from __future__ import annotations

from uuid import UUID

from cortex_api.core.identifiers import uuid7
from cortex_api.service.brand_report.model.report import BrandReport, BrandReportStatus
from cortex_api.service.brand_report.model.ui_state import BrandReportUiState
from cortex_api.service.brand_report.ui_state_service import (
    BrandReportUiStateService,
    ReportUiState,
)

# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


class _SessCtx:
    async def commit(self) -> None:
        pass

    def add(self, _obj: object) -> None:
        pass

    async def __aenter__(self) -> _SessCtx:
        return self

    async def __aexit__(self, *a: object) -> bool:
        return False


class _DB:
    def session(self) -> _SessCtx:
        return _SessCtx()


class _UiStateRepo:
    """Fake repo holding at most one in-memory BrandReportUiState row.

    Mirrors the real repo: get() returns None until a row is created;
    get_or_create() lazily creates the defaults row on first write.
    """

    def __init__(self) -> None:
        self._row: BrandReportUiState | None = None

    async def get(self, _session: object, brand_id: UUID) -> BrandReportUiState | None:
        return self._row if self._row is not None and self._row.brand_id == brand_id else None

    async def get_or_create(self, _session: object, brand_id: UUID) -> BrandReportUiState:
        if self._row is None:
            self._row = BrandReportUiState(brand_id=brand_id)
        return self._row


class _ReportRepo:
    """Fake brand_report repo exposing only get_current (default → None).

    Mirrors the real ``BrandReportRepo.get_current`` contract: it only ever
    returns a report whose ``status == READY`` (and unarchived). A stored
    GENERATING/FAILED row is invisible to ``get_current`` and surfaces as None,
    exactly as the SQL ``WHERE status == READY`` clause would.
    """

    def __init__(self) -> None:
        self._current: BrandReport | None = None

    def set_current(self, report: BrandReport | None) -> None:
        self._current = report

    async def get_current(self, _session: object, _brand_id: UUID) -> BrandReport | None:
        if self._current is None or self._current.status != BrandReportStatus.READY:
            return None
        return self._current


def _report(status: BrandReportStatus, brand_id: UUID) -> BrandReport:
    return BrandReport(brand_id=brand_id, report_id="r1", version="v1.0", status=status)


def _svc() -> tuple[BrandReportUiStateService, _UiStateRepo, _ReportRepo]:
    repo = _UiStateRepo()
    report_repo = _ReportRepo()
    svc = BrandReportUiStateService(
        database_client=_DB(),
        ui_state_repo=repo,
        report_repo=report_repo,
    )
    return svc, repo, report_repo


# ---------------------------------------------------------------------------
# get_ui_state
# ---------------------------------------------------------------------------


async def test_get_ui_state_defaults_when_no_row() -> None:
    bid = uuid7()
    svc, _, _ = _svc()
    state = await svc.get_ui_state(bid)
    assert state == ReportUiState(
        celebrate_pending=False,
        hero_dismissed=False,
        celebrate_ready=False,
    )


# ---------------------------------------------------------------------------
# arm / consume / dismiss
# ---------------------------------------------------------------------------


async def test_arm_celebrate_sets_pending_true() -> None:
    bid = uuid7()
    svc, _, _ = _svc()
    await svc.arm_celebrate(bid)
    state = await svc.get_ui_state(bid)
    assert state.celebrate_pending is True


async def test_consume_celebrate_clears_pending_and_latches_consumed() -> None:
    bid = uuid7()
    svc, repo, _ = _svc()
    await svc.arm_celebrate(bid)
    await svc.consume_celebrate(bid)
    state = await svc.get_ui_state(bid)
    assert state.celebrate_pending is False
    assert repo._row is not None
    assert repo._row.celebrate_consumed is True


async def test_consume_celebrate_idempotent_without_arming() -> None:
    bid = uuid7()
    svc, repo, _ = _svc()
    # Never armed — consume is still safe (creates a row, latches consumed).
    await svc.consume_celebrate(bid)
    state = await svc.get_ui_state(bid)
    assert state.celebrate_pending is False
    assert repo._row is not None
    assert repo._row.celebrate_consumed is True


async def test_dismiss_hero_sets_hero_dismissed() -> None:
    bid = uuid7()
    svc, _, _ = _svc()
    await svc.dismiss_hero(bid)
    state = await svc.get_ui_state(bid)
    assert state.hero_dismissed is True


# ---------------------------------------------------------------------------
# "arm once" semantic — arm is a no-op once consumed
# ---------------------------------------------------------------------------


async def test_arm_after_consume_is_noop() -> None:
    """Re-running onboarding after the celebration was consumed must NOT
    resurrect it — arm_celebrate is a no-op once celebrate_consumed is true."""
    bid = uuid7()
    svc, repo, _ = _svc()
    await svc.arm_celebrate(bid)
    await svc.consume_celebrate(bid)  # celebrate_consumed = True

    # Onboarding re-run arms again — but it's been consumed, so no-op.
    await svc.arm_celebrate(bid)

    state = await svc.get_ui_state(bid)
    assert state.celebrate_pending is False
    assert repo._row is not None
    assert repo._row.celebrate_consumed is True


async def test_arm_twice_before_consume_keeps_pending() -> None:
    """Arming twice before any consume just keeps celebrate_pending true."""
    bid = uuid7()
    svc, _, _ = _svc()
    await svc.arm_celebrate(bid)
    await svc.arm_celebrate(bid)
    state = await svc.get_ui_state(bid)
    assert state.celebrate_pending is True


# ---------------------------------------------------------------------------
# celebrate_ready — server-side correlation of armed + current READY report
# ---------------------------------------------------------------------------


async def test_celebrate_ready_true_when_armed_and_report_ready() -> None:
    bid = uuid7()
    svc, _, report_repo = _svc()
    await svc.arm_celebrate(bid)
    report_repo.set_current(_report(BrandReportStatus.READY, bid))
    state = await svc.get_ui_state(bid)
    assert state.celebrate_ready is True


async def test_celebrate_ready_false_when_armed_but_no_current_report() -> None:
    bid = uuid7()
    svc, _, report_repo = _svc()
    await svc.arm_celebrate(bid)
    report_repo.set_current(None)
    state = await svc.get_ui_state(bid)
    assert state.celebrate_ready is False


async def test_celebrate_ready_false_when_report_still_generating() -> None:
    bid = uuid7()
    svc, _, report_repo = _svc()
    await svc.arm_celebrate(bid)
    report_repo.set_current(_report(BrandReportStatus.GENERATING, bid))
    state = await svc.get_ui_state(bid)
    assert state.celebrate_ready is False


async def test_celebrate_ready_false_after_consume_even_with_ready_report() -> None:
    bid = uuid7()
    svc, _, report_repo = _svc()
    await svc.arm_celebrate(bid)
    await svc.consume_celebrate(bid)  # celebrate_consumed = True
    report_repo.set_current(_report(BrandReportStatus.READY, bid))
    state = await svc.get_ui_state(bid)
    assert state.celebrate_ready is False
