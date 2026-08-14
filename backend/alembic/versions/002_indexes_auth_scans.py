"""indexes, auth columns, scans, draft_text

Revision ID: 002
Revises: 001
Create Date: 2026-08-14

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.text("true")))
    op.add_column("users", sa.Column("email_verify_token", sa.String(length=128), nullable=True))
    op.add_column("users", sa.Column("reset_token", sa.String(length=128), nullable=True))
    op.add_column("users", sa.Column("reset_token_expires", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("last_scan_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("last_digest_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_users_reset_token", "users", ["reset_token"])

    op.add_column("posts", sa.Column("draft_text", sa.Text(), nullable=True))
    op.create_index("ix_posts_ingested_at", "posts", ["ingested_at"])
    op.create_index("ix_posts_relevance_ingested", "posts", ["relevance_score", "ingested_at"])

    op.create_index("ix_watchlist_matches_wl_matched", "watchlist_matches", ["watchlist_id", "matched_at"])
    op.create_index("ix_watchlists_keyword_active", "watchlists", ["keyword", "active"])

    op.create_table(
        "scans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("total_jobs", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("finished_jobs", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("results", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_scans_user_id", "scans", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_scans_user_id", table_name="scans")
    op.drop_table("scans")
    op.drop_index("ix_watchlists_keyword_active", table_name="watchlists")
    op.drop_index("ix_watchlist_matches_wl_matched", table_name="watchlist_matches")
    op.drop_index("ix_posts_relevance_ingested", table_name="posts")
    op.drop_index("ix_posts_ingested_at", table_name="posts")
    op.drop_column("posts", "draft_text")
    op.drop_index("ix_users_reset_token", table_name="users")
    op.drop_column("users", "last_digest_at")
    op.drop_column("users", "last_scan_at")
    op.drop_column("users", "reset_token_expires")
    op.drop_column("users", "reset_token")
    op.drop_column("users", "email_verify_token")
    op.drop_column("users", "email_verified")
