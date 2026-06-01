"""Knowledge base endpoints — placeholder."""

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/v1/kb", tags=["knowledge_base"])


@router.post("/search", summary="(Placeholder) Vector search per active org")
async def search() -> dict[str, str]:
    raise HTTPException(status_code=501, detail="knowledge_base is post-MVP")
