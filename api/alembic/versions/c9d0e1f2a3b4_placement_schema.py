"""placement schema — brand_placement_settings + 3 sibling tables

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-05-21 00:00:00.000000

COR-55 (F1). Design doc: Placement Runtime Design v4 § Schema changes.

Adds four tables for the new Cortex-owned placement runtime:

* ``brand_placement_settings`` — 1:1 with brand; row exists ⇔ brand is
  placement-ready (D1). All derivable columns are nullable as the
  transient mid-compose state; ``overrides_mask`` is NOT NULL with
  default ``'{}'::jsonb`` (D1). ``composed_at`` is NULL until the
  composer (COR-56) completes a successful derivation — consumers check
  ``composed_at IS NOT NULL`` rather than spelling out every required
  column.
* ``brand_publisher_scope`` — opt-in list of publishers per brand.
  Composite PK (brand_id, publisher_id). ``publisher_id`` has no FK
  because cortex does not own publisher onboarding at MVP.
* ``publisher_placement_config`` — future scaffold (D7 2026-05-21);
  not read at MVP because PHP retains the source of truth for
  ``brand_match_global_ratio`` and ships it via the request payload.
  Becomes canonical when publisher onboarding moves from PHP to Cortex.
* ``placement_audit`` — append-only audit log (winner +
  ``losing_candidates`` per R2; ``trace_id`` + ``parent_trace_id`` per
  R4). No FKs by design so audit rows outlive soft-deletes. Indexed on
  the four predictable read paths (per-brand, per-publisher, trace_id,
  article_url_hash).

ENUM types:

* ``placementmode`` (settings.mode) — created via op.create_table.
* ``placementrowstatus`` (settings.status + scope.status — shared since
  both describe the same lifecycle, locked by coordinator review
  2026-05-21) — created explicitly via ``ENUM.create(checkfirst=True)``
  so the second table can reference it without a duplicate CREATE TYPE.

Both ENUMs are dropped explicitly in ``downgrade()`` per the cortex
CLAUDE.md migration rules.

Deploy step (D4): manual ``kubectl cp alembic/versions/<file>.py
<pod>:/app/alembic/versions/`` + ``kubectl exec <pod> -- alembic upgrade
head`` until OPT-22 lands the helm pre-upgrade Job.
"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c9d0e1f2a3b4"
down_revision: str | None = "b8c9d0e1f2a3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Shared ENUM type across brand_placement_settings.status and
# brand_publisher_scope.status — declared once, referenced twice. Using
# ``create_type=False`` on the Column reference means SQLAlchemy won't
# try to auto-CREATE TYPE inside op.create_table; we call ``.create()``
# explicitly so the first table creation doesn't race with the second.
_placement_row_status = postgresql.ENUM(
    "active",
    "inactive",
    name="placementrowstatus",
    create_type=False,
)


def upgrade() -> None:
    _placement_row_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "brand_placement_settings",
        sa.Column("brand_id", sa.Uuid(), nullable=False),
        sa.Column("use_dynamic_question", sa.Boolean(), nullable=True),
        sa.Column("question_position", sa.SmallInteger(), nullable=True),
        sa.Column("ad_ratio", sa.Numeric(3, 2), nullable=True),
        sa.Column(
            "mode",
            sa.Enum(
                "question_replacement",
                "answer_only",
                "both",
                name="placementmode",
            ),
            nullable=True,
        ),
        sa.Column("matching_rules", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("matching_keywords", postgresql.JSONB(), nullable=True),
        sa.Column("matching_categories", postgresql.JSONB(), nullable=True),
        sa.Column("brand_answer_prompt", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("brand_question_prompt", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("brand_cta_text", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("brand_cta_url", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column(
            "status",
            _placement_row_status,
            nullable=False,
            server_default="active",
        ),
        sa.Column(
            "overrides_mask",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("composed_at", sa.DateTime(), nullable=True),
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

    op.create_table(
        "brand_publisher_scope",
        sa.Column("brand_id", sa.Uuid(), nullable=False),
        sa.Column("publisher_id", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            _placement_row_status,
            nullable=False,
            server_default="active",
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
        sa.PrimaryKeyConstraint("brand_id", "publisher_id"),
    )

    op.create_table(
        "publisher_placement_config",
        sa.Column("publisher_id", sa.Uuid(), nullable=False),
        sa.Column("global_match_ratio", sa.Numeric(3, 2), nullable=True),
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
        sa.PrimaryKeyConstraint("publisher_id"),
    )

    op.create_table(
        "placement_audit",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("brand_id", sa.Uuid(), nullable=False),
        sa.Column("publisher_id", sa.Uuid(), nullable=False),
        sa.Column("article_url", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column(
            "article_url_hash",
            sqlmodel.sql.sqltypes.AutoString(length=64),
            nullable=False,
        ),
        sa.Column("question_text", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("answer_text", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("placement_position", sa.SmallInteger(), nullable=False),
        sa.Column("rationale", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("selection_weight", sa.Numeric(5, 4), nullable=False),
        sa.Column(
            "losing_candidates",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "trace_id",
            sqlmodel.sql.sqltypes.AutoString(length=64),
            nullable=False,
        ),
        sa.Column(
            "parent_trace_id",
            sqlmodel.sql.sqltypes.AutoString(length=64),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Indexes for the four predictable read paths on placement_audit.
    # Append-only + monotonically growing — catching this at table-create
    # time costs ~four lines; retrofitting later means CREATE INDEX
    # CONCURRENTLY against a large live table.
    op.create_index(
        "ix_placement_audit_brand_id_created_at",
        "placement_audit",
        ["brand_id", sa.text("created_at DESC")],
    )
    op.create_index(
        "ix_placement_audit_publisher_id_created_at",
        "placement_audit",
        ["publisher_id", sa.text("created_at DESC")],
    )
    op.create_index("ix_placement_audit_trace_id", "placement_audit", ["trace_id"])
    op.create_index(
        "ix_placement_audit_article_url_hash",
        "placement_audit",
        ["article_url_hash"],
    )


def downgrade() -> None:
    op.drop_index("ix_placement_audit_article_url_hash", table_name="placement_audit")
    op.drop_index("ix_placement_audit_trace_id", table_name="placement_audit")
    op.drop_index(
        "ix_placement_audit_publisher_id_created_at",
        table_name="placement_audit",
    )
    op.drop_index(
        "ix_placement_audit_brand_id_created_at",
        table_name="placement_audit",
    )
    op.drop_table("placement_audit")
    op.drop_table("publisher_placement_config")
    op.drop_table("brand_publisher_scope")
    op.drop_table("brand_placement_settings")
    _placement_row_status.drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="placementmode").drop(op.get_bind(), checkfirst=True)
