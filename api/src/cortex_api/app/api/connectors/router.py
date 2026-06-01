"""Connectors endpoints — placeholder."""

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/v1/connectors", tags=["connectors"])


@router.get("", summary="(Placeholder) List connectors for the active org")
async def list_connectors() -> dict[str, str]:
    raise HTTPException(status_code=501, detail="connectors is post-MVP")
