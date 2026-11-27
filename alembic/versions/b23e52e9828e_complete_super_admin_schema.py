
"""complete super admin schema

Revision ID: b23e52e9828e
Revises: 1c2e93ea5c62
Create Date: 2026-11-27 16:19:14.343257
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b23e52e9828e"
down_revision: Union[str, Sequence[str], None] = "1c2e93ea5c62"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add full_name as nullable first to preserve existing records.
    op.add_column(
        "super_admins",
        sa.Column("full_name", sa.String(150), nullable=True),
    )

    # Populate full_name for existing Super Admin records.
    op.execute("""
        UPDATE super_admins
        SET full_name = email
        WHERE full_name IS NULL
    """)

    # Make full_name mandatory.
    op.alter_column(
        "super_admins",
        "full_name",
        existing_type=sa.String(150),
        nullable=False,
    )

    # Add updated_at.
    op.add_column(
        "super_admins",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Replace the non-unique email index with a unique index.
    op.drop_index(
        "ix_super_admins_email",
        table_name="super_admins",
    )

    op.create_index(
        "ix_super_admins_email",
        "super_admins",
        ["email"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_super_admins_email",
        table_name="super_admins",
    )

    op.create_index(
        "ix_super_admins_email",
        "super_admins",
        ["email"],
        unique=False,
    )

    op.drop_column("super_admins", "updated_at")
    op.drop_column("super_admins", "full_name")
