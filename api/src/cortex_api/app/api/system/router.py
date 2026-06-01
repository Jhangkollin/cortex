"""System endpoints — /health and /version."""

from fastapi import APIRouter

from cortex_api import __version__
from cortex_api.app.api.system.dto import HealthResponse, VersionResponse

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse, summary="Liveness check")
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/version", response_model=VersionResponse, summary="App name + version")
async def version() -> VersionResponse:
    return VersionResponse(name="cortex-api", version=__version__)
