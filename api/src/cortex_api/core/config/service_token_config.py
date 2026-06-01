"""Service-to-service bearer token config.

Holds secrets for outbound/inbound service auth (e.g. agent-ws → cortex F2).
Per D5/D6: tokens come from AWS Secrets Manager via the Secrets Store CSI
Driver, projected into k8s Secret `cortex-service-tokens`, then injected as
env vars on the cortex-api pod.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServiceTokenConfig(BaseSettings):
    """Bearer tokens accepted on service-to-service routes."""

    model_config = SettingsConfigDict(env_prefix="CORE_SERVICE_TOKEN_", extra="forbid")

    agent_ws: str = Field(default="", description="Token agent-will-smith presents to cortex on /v1/publishers/*")
