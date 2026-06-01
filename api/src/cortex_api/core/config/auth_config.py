"""Auth config — JWT verification settings.

cortex-web (NextAuth) signs JWTs that cortex-api verifies locally with the
same shared secret. No introspection round-trip.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthConfig(BaseSettings):
    """JWT verification config."""

    model_config = SettingsConfigDict(env_prefix="CORE_AUTH_", extra="forbid")

    # Field name matches chart key (CORE_AUTH_NEXTAUTH_SECRET) — cortex-web's
    # NextAuth signs JWTs with this; cortex-api verifies with the same value.
    nextauth_secret: str = Field(default="change-me", description="Shared secret with cortex-web")
    jwt_algorithm: str = Field(default="HS256")
    jwt_audience: str = Field(default="cortex-api")
    jwt_issuer: str = Field(default="cortex-web")
