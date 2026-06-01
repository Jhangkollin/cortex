"""Admin endpoints — placeholder.

Cortex-native admin replaces PHP admin (aigc-mvp) eventually. Until then, ops
work happens in the existing PHP admin.
"""

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/v1/admin", tags=["admin"])


@router.get("/health", summary="(Placeholder) Admin surface health")
async def admin_health() -> dict[str, str]:
    raise HTTPException(status_code=501, detail="admin is post-MVP")
