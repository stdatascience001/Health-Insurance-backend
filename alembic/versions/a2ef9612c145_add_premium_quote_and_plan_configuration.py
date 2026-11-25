
"""add premium quote and plan configuration

Revision ID: a2ef9612c145
Revises: 36f95dd1f0a7
"""

import uuid

from alembic import op
import sqlalchemy as sa


revision = "a2ef9612c145"
down_revision = "36f95dd1f0a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add pricing information to insurance applications.
    op.add_column(
        "insurance_applications",
        sa.Column("pricing_rule_id", sa.UUID(), nullable=True),
    )
    op.add_column(
        "insurance_applications",
        sa.Column("duration_months", sa.Integer(), nullable=True),
    )
    op.add_column(
        "insurance_applications",
        sa.Column("premium_frequency", sa.String(length=30), nullable=True),
    )

    # Prepare lightweight table definitions.
    plans = sa.table(
        "plans",
        sa.column("id", sa.UUID()),
        sa.column("premium_amount", sa.Numeric(10, 2)),
        sa.column("coverage_amount", sa.Numeric(12, 2)),
        sa.column("min_entry_age", sa.Integer()),
        sa.column("max_entry_age", sa.Integer()),
        sa.column("duration_months", sa.Integer()),
    )

    pricing_rules = sa.table(
        "plan_pricing_rules",
        sa.column("id", sa.UUID()),
        sa.column("plan_id", sa.UUID()),
        sa.column("min_age", sa.Integer()),
        sa.column("max_age", sa.Integer()),
        sa.column("coverage_amount", sa.Numeric(12, 2)),
        sa.column("duration_months", sa.Integer()),
        sa.column("premium_frequency", sa.String(30)),
        sa.column("premium_amount", sa.Numeric(10, 2)),
        sa.column("is_active", sa.Boolean()),
    )

    # Transfer existing plan prices into annual pricing rules.
    connection = op.get_bind()

    existing_plans = connection.execute(
        sa.select(
            plans.c.id,
            plans.c.premium_amount,
            plans.c.coverage_amount,
            plans.c.min_entry_age,
            plans.c.max_entry_age,
            plans.c.duration_months,
        )
    ).mappings().all()

    for plan in existing_plans:
        connection.execute(
            sa.insert(pricing_rules).values(
                id=uuid.uuid4(),
                plan_id=plan["id"],
                min_age=plan["min_entry_age"],
                max_age=plan["max_entry_age"],
                coverage_amount=plan["coverage_amount"],
                duration_months=plan["duration_months"],
                premium_frequency="annual",
                premium_amount=plan["premium_amount"],
                is_active=True,
            )
        )

    # Connect insurance applications to their selected pricing rule.
    op.create_foreign_key(
        "fk_insurance_applications_pricing_rule_id",
        "insurance_applications",
        "plan_pricing_rules",
        ["pricing_rule_id"],
        ["id"],
    )

    # Remove old pricing columns only after transferring their data.
    op.drop_column("plans", "premium_amount")
    op.drop_column("plans", "coverage_amount")


def downgrade() -> None:
    # Restore the old plan pricing columns.
    op.add_column(
        "plans",
        sa.Column("premium_amount", sa.Numeric(10, 2), nullable=True),
    )
    op.add_column(
        "plans",
        sa.Column("coverage_amount", sa.Numeric(12, 2), nullable=True),
    )

    connection = op.get_bind()

    plans = sa.table(
        "plans",
        sa.column("id", sa.UUID()),
        sa.column("premium_amount", sa.Numeric(10, 2)),
        sa.column("coverage_amount", sa.Numeric(12, 2)),
    )

    pricing_rules = sa.table(
        "plan_pricing_rules",
        sa.column("plan_id", sa.UUID()),
        sa.column("premium_frequency", sa.String(30)),
        sa.column("premium_amount", sa.Numeric(10, 2)),
        sa.column("coverage_amount", sa.Numeric(12, 2)),
    )

    # Restore the original annual premium and coverage values.
    annual_rules = connection.execute(
        sa.select(
            pricing_rules.c.plan_id,
            pricing_rules.c.premium_amount,
            pricing_rules.c.coverage_amount,
        ).where(pricing_rules.c.premium_frequency == "annual")
    ).mappings().all()

    for rule in annual_rules:
        connection.execute(
            sa.update(plans)
            .where(plans.c.id == rule["plan_id"])
            .values(
                premium_amount=rule["premium_amount"],
                coverage_amount=rule["coverage_amount"],
            )
        )

    op.alter_column(
        "plans",
        "premium_amount",
        existing_type=sa.Numeric(10, 2),
        nullable=False,
    )
    op.alter_column(
        "plans",
        "coverage_amount",
        existing_type=sa.Numeric(12, 2),
        nullable=False,
    )

    # Remove the application pricing relationship and new columns.
    op.drop_constraint(
        "fk_insurance_applications_pricing_rule_id",
        "insurance_applications",
        type_="foreignkey",
    )

    op.drop_column("insurance_applications", "premium_frequency")
    op.drop_column("insurance_applications", "duration_months")
    op.drop_column("insurance_applications", "pricing_rule_id")
