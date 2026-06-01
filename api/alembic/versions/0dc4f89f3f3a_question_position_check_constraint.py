"""backfill question_position < 1 + CHECK constraint

Revision ID: 0dc4f89f3f3a
Revises: 7ab199ba95a2
Create Date: 2026-05-26 00:00:00.000000

Addresses PR #68 review feedback:

1. Backfill: any existing rows with question_position = 0 (or negative)
   are set to 1, the documented minimum (1-indexed for downstream PHP
   burst endpoint).
2. CHECK constraint: ``question_position IS NULL OR question_position >= 1``
   enforces the invariant at the DB layer. NULL is allowed because
   question_position is nullable (pre-compose state per D1).

The model-layer ``__init__`` validation (added in the prior commit)
catches bad values at the application boundary; this constraint is the
DB-level safety net for direct SQL, migrations, and future writers.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0dc4f89f3f3a"
down_revision: str | None = "7ab199ba95a2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Step 1: backfill rows that violate the new constraint.
    op.execute(
        "UPDATE brand_placement_settings "
        "SET question_position = 1 "
        "WHERE question_position IS NOT NULL AND question_position < 1"
    )

    # Step 2: add CHECK constraint so the DB enforces >= 1 going forward.
    op.create_check_constraint(
        "ck_brand_placement_settings_question_position_gte_1",
        "brand_placement_settings",
        "question_position IS NULL OR question_position >= 1",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_brand_placement_settings_question_position_gte_1",
        "brand_placement_settings",
        type_="check",
    )
