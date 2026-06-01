"""Knowledge base DTOs — placeholder."""

from pydantic import BaseModel


class PlaceholderResponse(BaseModel):
    status: str = "not_implemented"
    message: str = "knowledge_base is post-MVP"
