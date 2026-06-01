"""Database config — AWS RDS PostgreSQL connection.

Component-based shape: env vars are five discrete parts (host/port/username/
password/name) that match what the helm chart projects from the AWS Secrets
Manager-backed `cortex-rds-credentials` Kubernetes Secret. The `url` property
URL-encodes credentials (`urllib.parse.quote_plus`) before assembling the DSN
so passwords containing %, @, /, :, [, etc. don't corrupt the connection string.

Local dev uses the same shape — defaults assemble `localhost:5433/cortex`
with `cortex/cortex` credentials, matching `docker-compose.yml`.
"""

from urllib.parse import quote_plus

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseSettings):
    """RDS / Postgres connection config.

    Cortex uses RDS PostgreSQL in Tokyo (`ap-northeast-1`) as its OLTP store.
    Drivers / SQLModel / Alembic are Postgres-generic; swapping to Lakebase
    later (when it ships in our region) is essentially a DSN change.
    """

    model_config = SettingsConfigDict(env_prefix="CORE_DB_", extra="forbid")

    # Components — chart projects these from cortex-rds-credentials Secret keys.
    host: str = Field(default="localhost")
    port: int = Field(default=5433)
    username: str = Field(default="cortex")
    password: SecretStr = Field(default=SecretStr("cortex"))
    name: str = Field(default="cortex", description="Database name")

    # Pool / behavior
    pool_size: int = Field(default=10)
    pool_pre_ping: bool = Field(default=True)
    echo: bool = Field(default=False, description="Log SQL statements (dev only)")

    @property
    def url(self) -> str:
        """SQLAlchemy DSN with URL-encoded credentials. asyncpg driver."""
        return (
            f"postgresql+asyncpg://"
            f"{quote_plus(self.username)}:"
            f"{quote_plus(self.password.get_secret_value())}"
            f"@{self.host}:{self.port}/{self.name}"
        )
