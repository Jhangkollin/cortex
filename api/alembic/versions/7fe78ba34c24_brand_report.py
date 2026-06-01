"""brand report

Revision ID: 7fe78ba34c24
Revises: 4facedd34e4d
Create Date: 2026-05-24 00:37:36.556207

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "7fe78ba34c24"
down_revision: str | None = "4facedd34e4d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "brand_report",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("brand_id", sa.Uuid(), nullable=False),
        sa.Column("report_id", sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
        sa.Column("version", sqlmodel.sql.sqltypes.AutoString(length=16), nullable=False),
        sa.Column("status", sa.Enum("generating", "ready", "failed", name="brandreportstatus"), nullable=False),
        sa.Column("report_json", postgresql.JSONB(), nullable=True),
        sa.Column("cost_usd", sa.Float(), nullable=True),
        sa.Column("error", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("archived_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(["brand_id"], ["brand.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_brand_report_brand_id", "brand_report", ["brand_id"])
    op.create_index("ix_brand_report_report_id", "brand_report", ["report_id"])
    op.create_index("ix_brand_report_brand_id_status", "brand_report", ["brand_id", "status"])
    op.create_unique_constraint("uq_brand_report_brand_id_version", "brand_report", ["brand_id", "version"])
    op.create_index(
        "uq_brand_report_one_current",
        "brand_report",
        ["brand_id"],
        unique=True,
        postgresql_where=sa.text("status = 'ready' AND archived_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_brand_report_one_current", table_name="brand_report")
    op.drop_constraint("uq_brand_report_brand_id_version", "brand_report", type_="unique")
    op.drop_index("ix_brand_report_brand_id_status", table_name="brand_report")
    op.drop_index("ix_brand_report_report_id", table_name="brand_report")
    op.drop_index("ix_brand_report_brand_id", table_name="brand_report")
    op.drop_table("brand_report")
    sa.Enum(name="brandreportstatus").drop(op.get_bind(), checkfirst=True)
