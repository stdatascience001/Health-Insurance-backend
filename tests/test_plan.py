
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.plan import PlanCreate


def test_plan_with_valid_data():
    plan = PlanCreate(
        name="Health Premium",
        description="Complete health insurance coverage",
        premium_amount=Decimal("5000"),
        coverage_amount=Decimal("500000"),
        duration_months=12
    )

    assert plan.name == "Health Premium"
    assert plan.premium_amount == Decimal("5000")


def test_plan_with_zero_premium():
    with pytest.raises(ValidationError):
        PlanCreate(
            name="Health Premium",
            premium_amount=0,
            coverage_amount=500000,
            duration_months=12
        )


def test_plan_with_zero_coverage():
    with pytest.raises(ValidationError):
        PlanCreate(
            name="Health Premium",
            premium_amount=5000,
            coverage_amount=0,
            duration_months=12
        )


def test_plan_with_zero_duration():
    with pytest.raises(ValidationError):
        PlanCreate(
            name="Health Premium",
            premium_amount=5000,
            coverage_amount=500000,
            duration_months=0
        )


def test_plan_with_short_name():
    with pytest.raises(ValidationError):
        PlanCreate(
            name="AB",
            premium_amount=5000,
            coverage_amount=500000,
            duration_months=12
        )
