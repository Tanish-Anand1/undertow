"""guest accounts: name, guest flag, guest scan counter, guest device id

Revision ID: 005
Revises: 004
Create Date: 2026-08-19

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("name", sa.String(length=120), nullable=True))
    op.add_column("users", sa.Column("is_guest", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("users", sa.Column("guest_scans_used", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("users", sa.Column("guest_device_id", sa.String(length=64), nullable=True))
    op.create_index("ix_users_guest_device_id", "users", ["guest_device_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_guest_device_id", table_name="users")
    op.drop_column("users", "guest_device_id")
    op.drop_column("users", "guest_scans_used")
    op.drop_column("users", "is_guest")
    op.drop_column("users", "name")
