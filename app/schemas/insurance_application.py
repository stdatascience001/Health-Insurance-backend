
from datetime import date
from typing import Literal
from pydantic import BaseModel, Field, model_validator, field_validator
from uuid import UUID


class InsuranceApplicationCreate(BaseModel):
    plan_id: UUID
    date_of_birth: date
    gender: str = Field(min_length=1, max_length=20)
    address: str = Field(min_length=5)

    nominee_name: str = Field(min_length=2, max_length=150)
    nominee_relationship: str = Field(min_length=2, max_length=50)
    nominee_dob: date | None = None
    nominee_phone: str | None = None

    medical_history: str | None = None

    #this will prevent the future dates to enter...
    @field_validator("date_of_birth", "nominee_dob")
    @classmethod
    def validate_dates(cls, value):
        if value is not None and value >= date.today():
            raise ValueError("Date of birth must be in the past.")
        return value


# For the admin so they can approve or reject the application.
class InsuranceApplicationReview(BaseModel):
    status: Literal["approved", "rejected"]
    rejection_reason: str | None = None

    @model_validator(mode="after")
    def validate_rejection_reason(self):
        if self.status == "rejected":
            if not self.rejection_reason or not self.rejection_reason.strip():
                raise ValueError("Rejection reason is required.")
        return self
