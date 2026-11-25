
from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.policy_cancellation import (
    PolicyCancellationCreate,
    PolicyCancellationResponse,
    PolicyCancellationReview
)


def test_cancellation_with_valid_data():
    cancellation = PolicyCancellationCreate(
        reason="No longer required",
        additional_comments="I would like to discontinue my policy."
    )

    assert cancellation.reason == "No longer required"


def test_cancellation_with_short_reason():
    with pytest.raises(ValidationError):
        PolicyCancellationCreate(
            reason="No"
        )


def test_cancellation_response():
    response = PolicyCancellationResponse(
        id=uuid4(),
        policy_id=uuid4(),
        customer_id=uuid4(),
        customer_name="John Smith",
        customer_email="john@example.com",
        reason="No longer required",
        status="pending",
        admin_remarks=None,
        requested_at=datetime.now(),
        reviewed_at=None
    )

    assert response.status == "pending"
    assert response.reviewed_at is None


def test_admin_approves_cancellation():
    review = PolicyCancellationReview(
        status="approved",
        admin_remarks="Cancellation approved."
    )

    assert review.status == "approved"


def test_admin_rejects_cancellation():
    review = PolicyCancellationReview(
        status="rejected",
        admin_remarks="Request does not meet cancellation criteria."
    )

    assert review.status == "rejected"


def test_invalid_cancellation_status():
    with pytest.raises(ValidationError):
        PolicyCancellationReview(
            status="pending"
        )
