"""Admin DTOs — placeholder."""

from pydantic import BaseModel


class PlaceholderResponse(BaseModel):
    status: str = "not_implemented"
    message: str = "admin is post-MVP — PHP admin (aigc-mvp) handles ops during transition"
