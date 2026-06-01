"""weekly_question + brand_weekly_questions

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-05-19 00:00:00.000000

Rebased onto post-#37/#39 develop: the original revision id
``f6a7b8c9d0e1`` collided with #37's ``brand_onboarded_at`` migration of the
same id (both authored independently and pre-merged before #38). This file
is the same upgrade/downgrade content with the revision id reassigned and
the chain re-pointed at the current develop head ``a7b8c9d0e1f2`` (#39
SP-VOICE brand_voice).

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "b8c9d0e1f2a3"
down_revision: str | None = "a7b8c9d0e1f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "weekly_question",
        sa.Column(
            "id",
            sqlmodel.sql.sqltypes.AutoString(length=64),
            nullable=False,
        ),
        sa.Column(
            "question_title",
            sqlmodel.sql.sqltypes.AutoString(length=2048),
            nullable=False,
        ),
        sa.Column(
            "publisher_name",
            sqlmodel.sql.sqltypes.AutoString(length=255),
            nullable=False,
        ),
        sa.Column("clicks", sa.Integer(), nullable=False),
        sa.Column("last_event_date", sa.Date(), nullable=True),
        sa.Column(
            "synced_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "brand_weekly_questions",
        sa.Column("brand_id", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "running",
                "succeeded",
                "failed",
                name="questionjobstatus",
            ),
            nullable=False,
        ),
        sa.Column("error", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column(
            "questions",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
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
        sa.PrimaryKeyConstraint("brand_id"),
    )


def downgrade() -> None:
    op.drop_table("brand_weekly_questions")
    op.drop_table("weekly_question")
    sa.Enum(name="questionjobstatus").drop(op.get_bind(), checkfirst=True)
