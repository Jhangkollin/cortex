"""add lang to brand_publisher_scope and topics to brand_profile (COR-57)

Revision ID: e65e2383b6c5
Revises: c9d0e1f2a3b4
Create Date: 2026-05-21 21:51:46.169201

Hand-curated (autogen detected unrelated noise — phantom drops of
``publisher`` / ``publisher_membership`` tables which exist in DB but
intentionally aren't in cortex's SQLModel imports per cortex CLAUDE.md;
plus cosmetic FK name churn). This migration ONLY adds the two columns
needed by COR-57's F2 contract:

1. ``brand_publisher_scope.lang VARCHAR(16) NOT NULL DEFAULT 'zh-tw'``
   — added to composite PK so a brand can opt into the same publisher
   for multiple languages independently. Backfill existing rows with
   ``'zh-tw'`` before promoting to NOT NULL.

2. ``brand_profile.topics JSONB NOT NULL DEFAULT '[]'::jsonb`` — list of
   topic strings distinct from ``category_alternatives`` (which feeds
   the composer's ``matching_categories``).

Round-trip safe: see cortex CLAUDE.md L177 (upgrade → downgrade → upgrade).
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "e65e2383b6c5"
down_revision: Union[str, None] = "c9d0e1f2a3b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- brand_publisher_scope.lang ---
    # 1) Add as nullable so existing rows can be backfilled
    op.add_column(
        "brand_publisher_scope",
        sa.Column("lang", sa.String(length=16), nullable=True),
    )
    # 2) Backfill existing rows
    op.execute("UPDATE brand_publisher_scope SET lang = 'zh-tw' WHERE lang IS NULL")
    # 3) Promote to NOT NULL with server default
    op.alter_column(
        "brand_publisher_scope",
        "lang",
        existing_type=sa.String(length=16),
        nullable=False,
        server_default="zh-tw",
    )
    # 4) Rebuild PK to include lang
    op.drop_constraint("brand_publisher_scope_pkey", "brand_publisher_scope", type_="primary")
    op.create_primary_key(
        "brand_publisher_scope_pkey",
        "brand_publisher_scope",
        ["brand_id", "publisher_id", "lang"],
    )

    # --- brand_profile.topics ---
    op.add_column(
        "brand_profile",
        sa.Column(
            "topics",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )


def downgrade() -> None:
    # --- brand_profile.topics ---
    op.drop_column("brand_profile", "topics")

    # --- brand_publisher_scope.lang ---
    # 1) Rebuild PK without lang
    op.drop_constraint("brand_publisher_scope_pkey", "brand_publisher_scope", type_="primary")
    op.create_primary_key(
        "brand_publisher_scope_pkey",
        "brand_publisher_scope",
        ["brand_id", "publisher_id"],
    )
    # 2) Drop the column
    op.drop_column("brand_publisher_scope", "lang")
