"""brand_profile (hybrid: scalar columns + JSONB snapshot)

Revision ID: c3d4e5f6a7b8
Revises: a1f4c8d2e3b5
Create Date: 2026-05-18 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c3d4e5f6a7b8"
down_revision: str | None = "a1f4c8d2e3b5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "brand_profile",
        sa.Column("brand_id", sa.Uuid(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("legal_name", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column("tagline", sqlmodel.sql.sqltypes.AutoString(length=512), nullable=True),
        sa.Column("monogram", sqlmodel.sql.sqltypes.AutoString(length=8), nullable=True),
        sa.Column("brand_color", sqlmodel.sql.sqltypes.AutoString(length=32), nullable=True),
        sa.Column("founded", sqlmodel.sql.sqltypes.AutoString(length=32), nullable=True),
        sa.Column("about", sa.Text(), nullable=True),
        sa.Column("source_url", sqlmodel.sql.sqltypes.AutoString(length=2048), nullable=True),
        sa.Column("industry_vertical", sqlmodel.sql.sqltypes.AutoString(length=128), nullable=True),
        sa.Column("primary_jurisdiction", sqlmodel.sql.sqltypes.AutoString(length=8), nullable=True),
        sa.Column("category_value", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column("category_confidence", sa.Integer(), nullable=True),
        sa.Column(
            "category_alternatives",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "region",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "voice_samples",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "products",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "competitors",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "media_matches",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("extraction_meta", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["brand_id"], ["brand.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("brand_id"),
    )


def downgrade() -> None:
    op.drop_table("brand_profile")
    # No ENUM created by this migration → no sa.Enum(...).drop() needed.
