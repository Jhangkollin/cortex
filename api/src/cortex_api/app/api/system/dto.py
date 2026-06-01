"""System endpoint DTOs."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str = "ok"


class VersionResponse(BaseModel):
    name: str
    version: str
