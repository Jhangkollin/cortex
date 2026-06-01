"""drop brand_membership founder unique (multi-brand)

Removes the ``brand_membership_founder_uniq`` partial UNIQUE index
(``brand_membership(user_id) WHERE invited_by IS NULL``, added in
``a1f4c8d2e3b5``) so a user can found MORE THAN ONE brand. This unblocks the
multi-brand onboarding model: every onboarding run creates a new, independent
brand + founder (ADMIN) membership, never overriding an existing one.

``downgrade()`` re-creates the index exactly as ``a1f4c8d2e3b5.upgrade()`` did,
so the chain round-trips. (A downgrade would fail if a user already holds two
founder memberships — acceptable; that is the state this migration enables.)

Revision ID: 7ab199ba95a2
Revises: a2b3c4d5e6f7
Create Date: 2026-05-26

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7ab199ba95a2"
down_revision: str | None = "a2b3c4d5e6f7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index(
        "brand_membership_founder_uniq",
        table_name="brand_membership",
    )


def downgrade() -> None:
    op.create_index(
        "brand_membership_founder_uniq",
        "brand_membership",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("invited_by IS NULL"),
    )
