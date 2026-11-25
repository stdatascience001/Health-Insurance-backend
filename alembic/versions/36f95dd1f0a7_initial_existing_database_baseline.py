"""safely update plan structure

Revision ID: 36f95dd1f0a7
Revises:
"""

from alembic import op
import sqlalchemy as sa

revision = "36f95dd1f0a7"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new fields temporarily as nullable.
    op.add_column("plans", sa.Column("plan_type", sa.String(length=50), nullable=True))
    op.add_column("plans", sa.Column("min_entry_age", sa.Integer(), nullable=True))
    op.add_column("plans", sa.Column("max_entry_age", sa.Integer(), nullable=True))

    # Set initial values for existing plans.
    op.execute("""
        UPDATE plans
        SET
            plan_type = 'individual',
            min_entry_age = 18,
            max_entry_age = 65
    """)

    # Make the new fields mandatory after backfilling.
    op.alter_column(
        "plans", "plan_type", existing_type=sa.String(length=50), nullable=False
    )
    op.alter_column(
        "plans", "min_entry_age", existing_type=sa.Integer(), nullable=False
    )
    op.alter_column(
        "plans", "max_entry_age", existing_type=sa.Integer(), nullable=False
    )
