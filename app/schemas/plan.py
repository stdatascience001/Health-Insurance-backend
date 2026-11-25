from pydantic import BaseModel, Field
from decimal import Decimal


class PlanCreate(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    description: str | None = None
    premium_amount: Decimal = Field(gt=0)
    coverage_amount: Decimal = Field(gt=0)
    duration_months: int = Field(gt=0)