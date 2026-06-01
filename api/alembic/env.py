"""Alembic env — async-aware migration runner.

Uses `DatabaseConfig` as the single source of truth for the DSN, so alembic
and the running app read the same env-var contract (`CORE_DB_*`). Avoids
the configparser `%` interpolation trap by never stuffing the raw URL into
alembic.ini's `[alembic]` section.
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlmodel import SQLModel

from cortex_api.core.config.database_config import DatabaseConfig
from cortex_api.service.brand.model.analysis_job import BrandProfileAnalysisJob  # noqa: F401
from cortex_api.service.brand.model.profile import BrandProfile  # noqa: F401

# Import all SQLModel tables here so Alembic autogenerate sees them.
# Publisher tables intentionally NOT imported at MVP — PHP handles publisher
# side. When Cortex takes over publisher onboarding from PHP, add the two
# publisher imports here and generate a follow-up migration.
from cortex_api.service.brand_identity.model.brand import Brand  # noqa: F401
from cortex_api.service.brand_identity.model.brand_membership import BrandMembership  # noqa: F401
from cortex_api.service.brand_report.model.report import BrandReport  # noqa: F401
from cortex_api.service.brand_report.model.ui_state import BrandReportUiState  # noqa: F401
from cortex_api.service.identity.model.app_user import AppUser  # noqa: F401
from cortex_api.service.media_network.model.job import BrandMediaNetwork  # noqa: F401
from cortex_api.service.media_network.model.member import MediaNetworkMember  # noqa: F401
from cortex_api.service.placement.model.audit import PlacementAudit  # noqa: F401
from cortex_api.service.placement.model.publisher_config import PublisherPlacementConfig  # noqa: F401
from cortex_api.service.placement.model.scope import BrandPublisherScope  # noqa: F401
from cortex_api.service.placement.model.settings import BrandPlacementSettings  # noqa: F401
from cortex_api.service.questions.model.job import BrandWeeklyQuestions  # noqa: F401
from cortex_api.service.questions.model.question import WeeklyQuestion  # noqa: F401
from cortex_api.service.voice.model.job import BrandVoice  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def _database_url() -> str:
    """Resolve DSN from the same config the running app uses.

    DatabaseConfig reads CORE_DB_{HOST,PORT,USERNAME,PASSWORD,NAME} and
    URL-encodes credentials in its `url` property, so passwords containing
    %, @, /, :, [, etc. assemble safely. Local-dev defaults assemble
    localhost:5433/cortex with cortex/cortex creds.
    """
    return DatabaseConfig().url


def run_migrations_offline() -> None:
    """Run migrations without a database connection."""
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations against the configured database (async)."""
    cfg = {"sqlalchemy.url": _database_url()}
    connectable = async_engine_from_config(cfg, prefix="sqlalchemy.", poolclass=pool.NullPool)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
