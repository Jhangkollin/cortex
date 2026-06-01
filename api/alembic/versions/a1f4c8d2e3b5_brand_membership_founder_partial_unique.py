"""brand_membership founder partial unique

DB-enforces "one founder membership per user" — pairs with the
`create_brand_with_admin` service method that previously did a
read-then-write to enforce this (TOCTOU race under concurrent first
sign-ins). The partial UNIQUE makes the second concurrent INSERT fail
with IntegrityError, which the service maps to ConflictError → 409.

Predicate: `invited_by IS NULL` — founder rows are exactly the
self-created memberships with no inviter. Invited memberships (rows
with `invited_by` set) are explicitly excluded so a user can still be
invited to additional brands once multi-brand membership lands.

Revision ID: a1f4c8d2e3b5
Revises: 8e4ef4f9b295
Create Date: 2026-05-12

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1f4c8d2e3b5"
down_revision: str | None = "8e4ef4f9b295"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "brand_membership_founder_uniq",
        "brand_membership",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("invited_by IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "brand_membership_founder_uniq",
        table_name="brand_membership",
    )
