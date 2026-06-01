"""add placement_compute_claim (COR-75)

Revision ID: 4facedd34e4d
Revises: e65e2383b6c5
Create Date: 2026-05-22 20:59:10.984479

Per AD8: row-as-lease replaces the rejected COR-65 Redis lock. PK is
(publisher_id, article_url_hash); UPSERT-with-WHERE encodes the
single-flight semantics (see PlacementClaimRepo.claim).

Round-trip safe: see cortex CLAUDE.md L177.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "4facedd34e4d"
down_revision: str | None = "e65e2383b6c5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ENUM for status — Postgres enum type.
    claim_status = postgresql.ENUM(
        "in_flight",
        "done",
        "failed",
        name="placement_claim_status",
    )
    claim_status.create(op.get_bind(), checkfirst=False)

    op.create_table(
        "placement_compute_claim",
        sa.Column("publisher_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("article_url_hash", postgresql.BYTEA(), nullable=False),
        sa.Column("claim_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_ws_request_id", sa.Text(), nullable=False),
        sa.Column(
            "brand_ids",
            postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
            nullable=False,
        ),
        sa.Column(
            "claimed_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("placement_audit_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "in_flight",
                "done",
                "failed",
                name="placement_claim_status",
                create_type=False,
            ),
            nullable=False,
            server_default="in_flight",
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.PrimaryKeyConstraint("publisher_id", "article_url_hash", name="placement_compute_claim_pkey"),
    )


def downgrade() -> None:
    op.drop_table("placement_compute_claim")
    op.execute("DROP TYPE IF EXISTS placement_claim_status")
