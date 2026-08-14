"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-08-13

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "watchlists",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("keyword", sa.String(length=255), nullable=False),
        sa.Column("platforms", sa.String(length=128), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_watchlists_owner_id", "watchlists", ["owner_id"])
    op.create_index("ix_watchlists_keyword", "watchlists", ["keyword"])

    op.create_table(
        "posts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("platform", sa.String(length=32), nullable=False),
        sa.Column("external_id", sa.String(length=128), nullable=False),
        sa.Column("source", sa.String(length=255), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("author", sa.String(length=255), nullable=False),
        sa.Column("engagement", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ingested_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("tag", sa.String(length=32), nullable=True),
        sa.Column("relevance_score", sa.Float(), nullable=True),
        sa.Column("classified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.UniqueConstraint("platform", "external_id", name="uq_posts_platform_external"),
    )
    op.create_index("ix_posts_platform", "posts", ["platform"])
    op.create_index("ix_posts_tag", "posts", ["tag"])

    op.create_table(
        "watchlist_matches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("watchlist_id", sa.Integer(), sa.ForeignKey("watchlists.id", ondelete="CASCADE"), nullable=False),
        sa.Column("post_id", sa.Integer(), sa.ForeignKey("posts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("match_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("matched_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("watchlist_id", "post_id", name="uq_watchlist_post"),
    )
    op.create_index("ix_watchlist_matches_watchlist_id", "watchlist_matches", ["watchlist_id"])
    op.create_index("ix_watchlist_matches_post_id", "watchlist_matches", ["post_id"])


def downgrade() -> None:
    op.drop_table("watchlist_matches")
    op.drop_table("posts")
    op.drop_table("watchlists")
    op.drop_table("users")
