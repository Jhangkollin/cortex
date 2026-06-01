"""brand_report_ui_state table (COR-82 dashboard UI state)

Revision ID: a2b3c4d5e6f7
Revises: 7fe78ba34c24
Create Date: 2026-05-24 00:00:00.000000

Creates a `brand_report_ui_state` table OWNED by the brand_report bounded
context. One row per brand (brand_id PK, FK→brand.id ON DELETE CASCADE) holds
the server-side dashboard UI flags that used to live in localStorage:

  celebrate_pending   BOOL NOT NULL DEFAULT false — armed at onboarding,
                      consumed on the first Discover visit.
  hero_dismissed      BOOL NOT NULL DEFAULT false — set when the user closes
                      the Brand IQ Report hero card.
  celebrate_consumed  BOOL NOT NULL DEFAULT false — latches the "arm once"
                      semantic so re-running onboarding can't resurrect a
                      dismissed celebration.

NOTE: this REPLACES the earlier draft of this revision that put two `report_*`
columns directly on `brand`. That coupled report-domain state to the identity
aggregate (CLAUDE.md bounded contexts) — moved to its own table here. The
`brand` table is untouched by this revision.

Round-trip safe: upgrade → downgrade → upgrade tested per CLAUDE.md. No ENUM
created, so no sa.Enum().drop() needed in downgrade().
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a2b3c4d5e6f7"
down_revision: str | None = "7fe78ba34c24"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "brand_report_ui_state",
        sa.Column("brand_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("celebrate_pending", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("hero_dismissed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("celebrate_consumed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("NOW()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["brand_id"],
            ["brand.id"],
            name="fk_brand_report_ui_state_brand_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("brand_id", name="pk_brand_report_ui_state"),
    )


def downgrade() -> None:
    op.drop_table("brand_report_ui_state")
