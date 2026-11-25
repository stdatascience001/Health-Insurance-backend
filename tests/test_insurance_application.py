
from datetime import date, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.insurance_application import (
    InsuranceApplicationCreate,
    InsuranceApplicationReview
)


def get_valid_application_data():
    return {
        "plan_id": uuid4(),
        "date_of_birth": date(1995, 5, 15),
        "gender": "Male",
        "address": "Delhi, India",
        "nominee_name": "Jane Smith",
        "nominee_relationship": "Spouse",
        "nominee_dob": date(1997, 8, 20),
        "nominee_phone": "9876543210",
        "medical_history": None
    }


def test_application_with_valid_data():
    application = InsuranceApplicationCreate(
        **get_valid_application_data()
    )

    assert application.gender == "Male"
    assert application.nominee_name == "Jane Smith"


def test_application_with_future_date_of_birth():
    data = get_valid_application_data()
    data["date_of_birth"] = date.today() + timedelta(days=1)

    with pytest.raises(ValidationError):
        InsuranceApplicationCreate(**data)


def test_application_with_future_nominee_dob():
    data = get_valid_application_data()
    data["nominee_dob"] = date.today() + timedelta(days=1)

    with pytest.raises(ValidationError):
        InsuranceApplicationCreate(**data)


def test_application_without_nominee_dob():
    data = get_valid_application_data()
    data["nominee_dob"] = None

    application = InsuranceApplicationCreate(**data)

    assert application.nominee_dob is None


def test_admin_approves_application():
    review = InsuranceApplicationReview(
        status="approved"
    )

    assert review.status == "approved"


def test_admin_rejects_without_reason():
    with pytest.raises(ValidationError):
        InsuranceApplicationReview(
            status="rejected"
        )


def test_admin_rejects_with_reason():
    review = InsuranceApplicationReview(
        status="rejected",
        rejection_reason="Incomplete documentation"
    )

    assert review.status == "rejected"
