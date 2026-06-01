"""brand.onboarded_at (nullable lifecycle stamp)

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-05-19 00:00:00.000000

Rebased after sp-media's e5f6a7b8c9d0_media_network (PR #36): this
migration was originally also e5f6a7b8c9d0 off d4e5f6a7b8c9 — renumbered
to linearize the chain (d4e5f6a7b8c9 -> e5f6a7b8c9d0 media_network ->
f6a7b8c9d0e1 brand_onboarded_at) and resolve the duplicate-revision /
multiple-heads collision.

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f6a7b8c9d0e1"
down_revision: str | None = "e5f6a7b8c9d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Nullable with NO server_default on purpose. NULL legitimately means
    # "this brand has not finished onboarding". The CLAUDE.md hard-won rule
    # "server_default=sa.func.now() on every created_at / updated_at"
    # deliberately does NOT apply here — this is a lifecycle stamp, not a
    # row-audit timestamp; defaulting it to now() would mark every existing
    # brand as already onboarded.
    op.add_column("brand", sa.Column("onboarded_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    # No Postgres ENUM was created by upgrade(), so no
    # sa.Enum(name=...).drop(op.get_bind(), checkfirst=True) is needed here
    # (contrast the analyzejobstatus drop in d4e5f6a7b8c9's downgrade).
    op.drop_column("brand", "onboarded_at")
