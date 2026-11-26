
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.plan import PlanCreate


def get_valid_plan_data():
    return {
        "name": "Health Premium",
        "description": "Complete health insurance coverage",
        "plan_type": "individual",
        "min_entry_age": 18,
        "max_entry_age": 65,
        "duration_months": 12,
        "pricing_rules": [
            {
                "min_age": 18,
                "max_age": 65,
                "coverage_amount": Decimal("500000"),
                "duration_months": 12,
                "premium_frequency": "annual",
                "premium_amount": Decimal("5000")
            },
            {
                "min_age": 18,
                "max_age": 65,
                "coverage_amount": Decimal("500000"),
                "duration_months": 12,
                "premium_frequency": "monthly",
                "premium_amount": Decimal("500")
            }
        ]
    }


def test_plan_with_valid_data():
    plan = PlanCreate(**get_valid_plan_data())

    assert plan.name == "Health Premium"
    assert len(plan.pricing_rules) == 2
    assert plan.pricing_rules[0].premium_frequency == "annual"
    assert plan.pricing_rules[0].premium_amount == Decimal("5000")
    assert plan.pricing_rules[1].premium_frequency == "monthly"
    assert plan.pricing_rules[1].premium_amount == Decimal("500")


def test_plan_with_zero_premium():
    data = get_valid_plan_data()
    data["pricing_rules"][0]["premium_amount"] = 0

    with pytest.raises(ValidationError):
        PlanCreate(**data)


def test_plan_with_zero_coverage():
    data = get_valid_plan_data()
    data["pricing_rules"][0]["coverage_amount"] = 0

    with pytest.raises(ValidationError):
        PlanCreate(**data)


def test_plan_with_zero_duration():
    data = get_valid_plan_data()
    data["duration_months"] = 0

    with pytest.raises(ValidationError):
        PlanCreate(**data)


def test_plan_with_short_name():
    data = get_valid_plan_data()
    data["name"] = "AB"

    with pytest.raises(ValidationError):
        PlanCreate(**data)
