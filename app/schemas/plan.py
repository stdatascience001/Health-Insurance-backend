from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class PlanPricingRuleCreate(BaseModel):
    id: UUID | None = None

    min_age: int = Field(ge=18)
    max_age: int = Field(ge=18)

    coverage_amount: Decimal = Field(gt=0)
    duration_months: int = Field(gt=0)

    premium_frequency: Literal["annual", "monthly"]
    premium_amount: Decimal = Field(gt=0)

    is_active: bool = True

    @model_validator(mode="after")
    def validate_age_range(self):
        if self.min_age > self.max_age:
            raise ValueError("Minimum age cannot exceed maximum age.")
        return self


class PlanBenefitCreate(BaseModel):
    id: UUID | None = None

    benefit_name: str = Field(min_length=2, max_length=150)
    description: str | None = None
    is_included: bool = True


class PlanConditionCreate(BaseModel):
    id: UUID | None = None

    condition_type: str = Field(min_length=2, max_length=100)
    condition_value: str = Field(min_length=1, max_length=150)
    description: str | None = None


class PlanCreate(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    description: str | None = None
    plan_type: str = Field(min_length=2, max_length=50)

    min_entry_age: int = Field(ge=0)
    max_entry_age: int = Field(ge=0)

    duration_months: int = Field(gt=0)

    pricing_rules: list[PlanPricingRuleCreate] = Field(min_length=1)
    benefits: list[PlanBenefitCreate] = Field(default_factory=list)
    conditions: list[PlanConditionCreate] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_plan(self):
        if self.min_entry_age > self.max_entry_age:
            raise ValueError("Minimum entry age cannot exceed maximum entry age.")

        for rule in self.pricing_rules:
            if rule.min_age < self.min_entry_age or rule.max_age > self.max_entry_age:
                raise ValueError(
                    "Pricing rule age range must be within the plan's entry age range."
                )

        return self
