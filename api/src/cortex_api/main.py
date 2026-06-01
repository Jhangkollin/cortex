"""FastAPI application entry point.

All container wiring happens here. Auth + tenant resolution lives in
`app/dependencies/`, not in middleware (per wiki §2.2). Middleware retains
only observability.
"""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import AsyncIterator, Awaitable, Callable

import structlog
from dependency_injector import providers
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from cortex_api.app.api.admin.router import router as admin_router
from cortex_api.app.api.auth.router import router as auth_router
from cortex_api.app.api.brand.router import router as brand_router
from cortex_api.app.api.brand_dashboard.router import router as brand_dashboard_router
from cortex_api.app.api.brand_identity.router import router as brand_identity_router
from cortex_api.app.api.brand_report.router import router as brand_report_router
from cortex_api.app.api.connectors.router import router as connectors_router
from cortex_api.app.api.eligible_brands.router import router as eligible_brands_router
from cortex_api.app.api.knowledge_base.router import router as knowledge_base_router
from cortex_api.app.api.media_network.router import router as media_network_router
from cortex_api.app.api.placement_claims.router import router as placement_claims_router
from cortex_api.app.api.publisher_dashboard.router import router as publisher_dashboard_router
from cortex_api.app.api.publisher_identity.router import router as publisher_identity_router
from cortex_api.app.api.questions.router import router as questions_router
from cortex_api.app.api.system.router import router as system_router
from cortex_api.app.api.voice.router import router as voice_router
from cortex_api.app.exception_handlers import register_exception_handlers
from cortex_api.app.middleware.observability_middleware import ObservabilityMiddleware
from cortex_api.app.middleware.service_bearer_middleware import ServiceBearerMiddleware
from cortex_api.core.container import Container as CoreContainer
from cortex_api.core.logger import configure_logging
from cortex_api.infra.container import Container as InfraContainer
from cortex_api.service.brand.container import Container as BrandContainer
from cortex_api.service.brand_dashboard.container import Container as BrandDashboardContainer
from cortex_api.service.brand_identity.container import Container as BrandIdentityContainer
from cortex_api.service.brand_report.container import Container as BrandReportContainer
from cortex_api.service.identity.container import Container as IdentityContainer
from cortex_api.service.media_network.container import Container as MediaNetworkContainer
from cortex_api.service.placement.cache.eligible_brands_cache import EligibleBrandsCache
from cortex_api.service.placement.container import Container as PlacementContainer
from cortex_api.service.placement.repo.scope_repo import ScopedBrandPublisherScopeRepo
from cortex_api.service.publisher_identity.container import Container as PublisherIdentityContainer
from cortex_api.service.questions.container import Container as QuestionsContainer
from cortex_api.service.voice.container import Container as VoiceContainer

# Global container instances. Per agent-will-smith convention, all wiring
# happens here — domain code receives dependencies via container providers.
_core_container = CoreContainer()
_infra_container = InfraContainer()
_identity_container = IdentityContainer()
_brand_identity_container = BrandIdentityContainer()
_placement_container = PlacementContainer()

# Build the eligible-brands cache. EligibleBrandsCache requires a raw
# redis.asyncio.Redis (uses .setex() / .delete() directly, not the
# RedisClient wrapper). Construct it from the config URL here — the
# process-wide singleton is safe because Redis connections are
# multiplexed per command, not per request.
_redis_url = _core_container.redis_config().url
from redis.asyncio import Redis as _RawRedis  # noqa: E402 — local import to avoid circular at module level

_raw_redis = _RawRedis.from_url(_redis_url)

_scoped_scope_repo = ScopedBrandPublisherScopeRepo(
    repo=_placement_container.scope_repo(),
    # Reuse the canonical _infra_container (line above) — a second
    # InfraContainer() here would build a parallel DatabaseClient + engine
    # that's invisible to _all_containers() and therefore to the integration
    # test's _reset_app_db_singletons fan-out. One engine per process.
    session_factory=_infra_container._database_client_factory().session,
)
_eligible_brands_cache = EligibleBrandsCache(
    redis_client=_raw_redis,
    scope_repo=_scoped_scope_repo,
)

_brand_container = BrandContainer(
    tracker=_placement_container.tracker,
    settings_repo=_placement_container.settings_repo,
    eligible_brands_cache=providers.Object(_eligible_brands_cache),
    eligible_brands_repo=_placement_container.eligible_brands_repo,
)
# Composition-root wiring: BrandContainer declares ``tracker``,
# ``settings_repo``, ``eligible_brands_cache``, and
# ``eligible_brands_repo`` as ``providers.Dependency`` (no default).
# Supplying them here is the ONLY way to construct BrandContainer — any
# future test rig or script that instantiates ``BrandContainer()`` without
# these args will raise ``DependencyError`` instead of silently getting
# a second tracker that the lifespan-shutdown drain would miss.
_publisher_identity_container = PublisherIdentityContainer()
_brand_dashboard_container = BrandDashboardContainer()
_media_network_container = MediaNetworkContainer()
_questions_container = QuestionsContainer()
_voice_container = VoiceContainer()
_brand_report_container = BrandReportContainer()


def _all_containers() -> tuple[object, ...]:
    """Return every container instantiated by ``main.py``.

    Sole consumer right now is the integration test harness's
    singleton-reset fixture (``tests/integration/conftest.py``).
    Centralising the list here means the test rig doesn't hard-code
    container names — when a new domain container lands (e.g. a future
    cortex sub-domain), adding it to this tuple is enough for the
    reset fixture to cover it. This is a deliberate **test seam**, not
    a runtime introspection API; production code should not iterate
    containers generically.
    """
    return (
        _core_container,
        _infra_container,
        _identity_container,
        _brand_identity_container,
        _publisher_identity_container,
        _placement_container,
        _brand_container,
        _brand_dashboard_container,
        _media_network_container,
        _questions_container,
        _voice_container,
        _brand_report_container,
        # Add new domain containers here.
    )


async def _sweep_stale_loop(interval_seconds: float) -> None:
    """Reclaim orphaned RUNNING jobs so a pod death can't deadlock a brand.

    The FIRST iteration is the *startup* reclaim — it sweeps immediately (no
    initial sleep) to flip RUNNING rows orphaned by a previous pod's hard
    death (SIGKILL / OOM between ``mark_running`` and ``mark_succeeded``),
    after which dedupe (`find_in_flight`) would otherwise return the orphan
    forever. Subsequent iterations are the *periodic* reclaim: on multi-pod
    EKS a long-lived pod must keep clearing orphans stranded by sibling pods.

    Running the startup sweep inside this task (rather than inline before the
    lifespan ``yield``) keeps every reclaim DB round-trip owned by one
    cancellable task: boot is never blocked on a DB call, and shutdown
    cancels this task cleanly so no pooled connection outlives its loop.
    Each iteration is fully guarded — a transient DB blip can't kill the
    loop — and ``CancelledError`` is re-raised so the task ends cleanly
    (no "Task exception was never retrieved").
    """
    logger = structlog.get_logger(__name__)
    first = True
    # Per-domain sweep with isolated try/except so (a) a failing sweep in one
    # domain doesn't skip its siblings this iteration, and (b) the structured
    # event name accurately identifies WHICH domain failed (@owl Issue 4 — a
    # single try/except previously logged ``analyze_sweep_stale_failed`` for a
    # voice/media failure, misleading at incident time).
    sweeps: tuple[tuple[str, Callable[[], Awaitable[int]]], ...] = (
        ("analyze", lambda: _brand_container.analyze_service().sweep_stale()),
        ("media", lambda: _media_network_container.job_service().sweep_stale()),
        ("questions", lambda: _questions_container.job_service().sweep_stale()),
        ("voice", lambda: _voice_container.job_service().sweep_stale()),
        ("brand_report", lambda: _brand_report_container.job_service().sweep_stale()),
    )
    while True:
        if not first:
            try:
                await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                raise
        for domain, run in sweeps:
            try:
                reclaimed = await run()
                logger.info(
                    f"{domain}_sweep_stale",
                    phase="startup" if first else "periodic",
                    reclaimed=reclaimed,
                )
            except asyncio.CancelledError:
                raise
            except Exception:  # noqa: BLE001 — one bad sweep mustn't skip its siblings
                logger.exception(
                    f"{domain}_sweep_stale_failed",
                    phase="startup" if first else "periodic",
                )
        first = False


async def _placement_sweep_iteration(*, limit: int) -> int:
    """Single iteration of the placement stale-sweep, factored out so
    unit + integration tests can call it without spinning the loop.

    Finds brands with stale or missing placement_settings (per
    ``PlacementSettingsRepo.find_stale_brand_ids``) and schedules a
    composer task per brand on the shared tracker. Returns the count of
    brands scheduled (not completed) — composes run on the tracker and
    will be awaited by the lifespan-shutdown drain.
    """
    db = _brand_container.database_client()
    settings_repo = _placement_container.settings_repo()
    composer = _brand_container.composer()
    tracker = _placement_container.tracker()
    async with db.session() as session:
        stale = await settings_repo.find_stale_brand_ids(session, limit=limit)
    for brand_id in stale:
        tracker.track(asyncio.create_task(composer.compose(brand_id)))
    return len(stale)


async def _sweep_stale_placement_loop(interval_seconds: float, limit: int) -> None:
    """Periodic reclaim for brand_placement_settings rows orphaned by a
    hard pod death between brand_profile commit and Hook A's composer
    task. Mirrors ``_sweep_stale_loop`` — first iteration is the startup
    reclaim (no initial sleep), subsequent iterations are the periodic
    reclaim. Each iteration is fully guarded; CancelledError re-raises
    so the task ends cleanly. See PR #52 Issue 3 for the rationale.
    """
    logger = structlog.get_logger(__name__)
    first = True
    while True:
        if not first:
            try:
                await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                raise
        try:
            reclaimed = await _placement_sweep_iteration(limit=limit)
            logger.info(
                "placement_sweep_stale",
                phase="startup" if first else "periodic",
                reclaimed=reclaimed,
            )
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001 — must not kill the loop
            logger.exception(
                "placement_sweep_stale_failed",
                phase="startup" if first else "periodic",
            )
        first = False


async def _compute_claims_gc_iteration() -> int:
    """One pass: delete completed-or-old-failed claim rows past
    ``PlacementClaimConfig.gc_retention_days`` (AD8)."""
    from sqlalchemy import text as _text

    db = _brand_container.database_client()
    retention_days = _brand_container.placement_claim_config().gc_retention_days
    async with db.session() as session:
        result = await session.execute(
            _text(
                """
                DELETE FROM placement_compute_claim
                WHERE completed_at
                          < NOW() - CAST(:retention_days AS integer) * interval '1 day'
                   OR (status = 'failed'
                       AND expires_at
                            < NOW() - CAST(:retention_days AS integer) * interval '1 day')
                """
            ),
            {"retention_days": retention_days},
        )
        await session.commit()
        return result.rowcount or 0


async def _sweep_compute_claims_loop(interval_seconds: float) -> None:
    """Daily GC for placement_compute_claim (COR-75 / AD8). Mirrors
    ``_sweep_stale_placement_loop`` — first iteration is the startup sweep;
    subsequent iterations are periodic. CancelledError re-raises so the
    task ends cleanly."""
    logger = structlog.get_logger(__name__)
    first = True
    while True:
        if not first:
            try:
                await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                raise
        try:
            deleted = await _compute_claims_gc_iteration()
            logger.info(
                "placement_compute_claim_gc",
                phase="startup" if first else "periodic",
                deleted=deleted,
            )
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001
            logger.exception(
                "placement_compute_claim_gc_failed",
                phase="startup" if first else "periodic",
            )
        first = False


@contextlib.asynccontextmanager
async def _lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """App lifecycle. Startup wiring stays in ``create_app``; this hook owns
    the analyze-job reclaim loop so a pod death can't deadlock a brand.

    A single background task does the startup reclaim (immediate first sweep)
    then keeps reclaiming sibling pods' orphans on an interval. Shutdown
    cancels that task, then runs ``cancel_all`` (which now also FAIL-marks
    THIS pod's in-flight rows immediately rather than after the TTL). Every
    step is best-effort and must never raise / block boot.
    """
    # Sweep cadence: track the configured TTL so reclaim latency stays close
    # to one TTL, but clamp it — a floor so a tiny/misconfigured TTL can't
    # busy-loop the DB, a ceiling so a very long TTL still reclaims sibling
    # pods' orphans within a bounded window.
    stale_ttl = _brand_container.analyze_config().stale_job_seconds
    sweep_interval = float(min(max(stale_ttl, 60), 300))
    sweep_task = asyncio.create_task(_sweep_stale_loop(sweep_interval))
    # Placement sweep runs at the same cadence — same exposure model
    # (background tasks that must complete; pod death between commit and
    # task is the failure mode). Limit of 100 keeps each pass bounded.
    placement_sweep_task = asyncio.create_task(_sweep_stale_placement_loop(sweep_interval, limit=100))
    # F2b GC (COR-75 / AD8): daily cleanup of completed/failed claim rows >30 days old.
    claims_gc_task = asyncio.create_task(_sweep_compute_claims_loop(24 * 3600.0))

    try:
        yield
    finally:
        sweep_task.cancel()
        placement_sweep_task.cancel()
        claims_gc_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await claims_gc_task
        with contextlib.suppress(asyncio.CancelledError):
            await sweep_task
        with contextlib.suppress(asyncio.CancelledError):
            await placement_sweep_task
        with contextlib.suppress(Exception):
            await _brand_container.analyze_service().cancel_all()
        with contextlib.suppress(Exception):
            await _media_network_container.job_service().cancel_all()
        with contextlib.suppress(Exception):
            await _questions_container.job_service().cancel_all()
        with contextlib.suppress(Exception):
            await _voice_container.job_service().cancel_all()
        with contextlib.suppress(Exception):
            await _brand_report_container.job_service().cancel_all()
        # Drain composer hook tasks last — the analyze/media/questions/voice
        # cancel_all calls above may themselves have scheduled composer tasks
        # via Hook B; drain after they finish so nothing in-flight escapes.
        with contextlib.suppress(Exception):
            await _placement_container.tracker().drain()


def create_app() -> FastAPI:
    """Build and configure the FastAPI app."""
    fastapi_config = _core_container.fastapi_config()
    log_config = _core_container.log_config()

    configure_logging(log_config)
    logger = structlog.get_logger(__name__)
    logger.info("application_starting", port=fastapi_config.port, debug=fastapi_config.debug)

    app = FastAPI(
        title=fastapi_config.title,
        version=fastapi_config.app_version,
        debug=fastapi_config.debug,
        docs_url=fastapi_config.docs_url,
        openapi_url=fastapi_config.openapi_url,
        lifespan=_lifespan,
    )

    # Middleware — observability only. Auth + tenant context are FastAPI deps.
    # ServiceBearerMiddleware is scoped to /v1/publishers/* (service-to-service
    # auth for F2). Other paths bypass it and continue through NextAuth + Depends.
    service_token_config = _core_container.service_token_config()
    app.add_middleware(ServiceBearerMiddleware, token=service_token_config.agent_ws)
    app.add_middleware(ObservabilityMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=fastapi_config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    # Wire DI for routes that use Depends(Provide[...]).
    # Each container's `wire()` processes Provide[ContainerClass.member]
    # references in the listed modules, binding them to live container
    # instances. A module that references multiple containers must be
    # listed once under each container's wire() call.
    _core_container.wire(modules=["cortex_api.app.dependencies.auth"])
    _identity_container.wire(
        modules=[
            "cortex_api.app.dependencies.auth",
            "cortex_api.app.api.auth.router",
            "cortex_api.app.api.brand_identity.router",
        ]
    )
    _brand_identity_container.wire(
        modules=[
            "cortex_api.app.api.auth.router",
            "cortex_api.app.api.brand_identity.router",
        ]
    )
    _brand_container.wire(
        modules=[
            "cortex_api.app.api.brand.router",
            "cortex_api.app.api.eligible_brands.router",
            "cortex_api.app.api.placement_claims.router",
        ]
    )
    _media_network_container.wire(modules=["cortex_api.app.api.media_network.router"])
    _questions_container.wire(modules=["cortex_api.app.api.questions.router"])
    _voice_container.wire(modules=["cortex_api.app.api.voice.router"])
    _brand_report_container.wire(modules=["cortex_api.app.api.brand_report.router"])

    # Routes
    app.include_router(system_router)
    app.include_router(auth_router)
    app.include_router(brand_identity_router)
    app.include_router(brand_router)
    app.include_router(media_network_router)
    app.include_router(questions_router)
    app.include_router(voice_router)
    app.include_router(brand_report_router)
    app.include_router(publisher_identity_router)
    app.include_router(brand_dashboard_router)
    app.include_router(publisher_dashboard_router)
    app.include_router(knowledge_base_router)
    app.include_router(connectors_router)
    app.include_router(admin_router)
    # F2 eligible-brands (service-to-service, protected by ServiceBearerMiddleware)
    app.include_router(eligible_brands_router)
    # F2b placement-claims (service-to-service, COR-75 / AD8)
    app.include_router(placement_claims_router)

    logger.info("application_ready", routes=[getattr(r, "path", "?") for r in app.routes])
    return app


app = create_app()
