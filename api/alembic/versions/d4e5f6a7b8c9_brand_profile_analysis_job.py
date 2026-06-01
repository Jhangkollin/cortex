"""brand profile analysis job

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: str | None = "c3d4e5f6a7b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "brand_profile_analysis_job",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("brand_id", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "running",
                "succeeded",
                "failed",
                name="analyzejobstatus",
            ),
            nullable=False,
        ),
        sa.Column(
            "source_url",
            sqlmodel.sql.sqltypes.AutoString(length=2048),
            nullable=False,
        ),
        sa.Column("cost_usd", sa.Float(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["brand_id"], ["brand.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_brand_profile_analysis_job_brand_id"),
        "brand_profile_analysis_job",
        ["brand_id"],
        unique=False,
    )
    op.create_index(
        "ix_brand_profile_analysis_job_brand_id_status",
        "brand_profile_analysis_job",
        ["brand_id", "status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_brand_profile_analysis_job_brand_id_status",
        table_name="brand_profile_analysis_job",
    )
    op.drop_index(
        op.f("ix_brand_profile_analysis_job_brand_id"),
        table_name="brand_profile_analysis_job",
    )
    op.drop_table("brand_profile_analysis_job")
    sa.Enum(name="analyzejobstatus").drop(op.get_bind(), checkfirst=True)
