"""Publisher Dashboard DTOs — placeholder projection over shared insights."""

from pydantic import BaseModel


class PlaceholderResponse(BaseModel):
    status: str = "not_implemented"
    message: str = "publisher_dashboard is post-MVP"
