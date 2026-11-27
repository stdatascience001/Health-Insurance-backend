"""simplify super admins table

Revision ID: 1c2e93ea5c62
Revises: 698ce1fe1a03
Create Date: 2026-11-27 16:12:38.322343

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "1c2e93ea5c62"
down_revision: Union[str, Sequence[str], None] = "698ce1fe1a03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add full_name
    op.add_column(
        "super_admins",
        sa.Column("full_name", sa.String(150), nullable=True),
    )

    # Populate existing records
    op.execute("""
        UPDATE super_admins
        SET full_name = email
        WHERE full_name IS NULL
    """)

    # Make full_name mandatory
    op.alter_column(
        "super_admins",
        "full_name",
        existing_type=sa.String(150),
        nullable=False,
    )

    # Add updated_at
    op.add_column(
        "super_admins",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Replace the existing non-unique email index
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
