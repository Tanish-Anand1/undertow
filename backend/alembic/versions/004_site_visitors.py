"""site visitors for the public homepage

Revision ID: 004
Revises: 003
Create Date: 2026-08-16
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "site_visitors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("visitor_key", sa.String(length=64), nullable=False),
        sa.Column("hits", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("cta_clicks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("first_seen", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_seen", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_site_visitors_visitor_key", "site_visitors", ["visitor_key"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_site_visitors_visitor_key", table_name="site_visitors")
    op.drop_table("site_visitors")
