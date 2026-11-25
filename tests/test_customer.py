
import pytest
from pydantic import ValidationError

from app.schemas.customer import CustomerCreate, CustomerUpdate


def test_customer_create_with_valid_data():
    customer = CustomerCreate(
        full_name="John Smith",
        email="john@example.com",
        phone="9876543210"
    )

    assert customer.full_name == "John Smith"
    assert customer.email == "john@example.com"


def test_customer_create_with_invalid_email():
    with pytest.raises(ValidationError):
        CustomerCreate(
            full_name="John Smith",
            email="invalid-email"
        )


def test_customer_create_with_short_name():
    with pytest.raises(ValidationError):
        CustomerCreate(
            full_name="J",
            email="john@example.com"
        )


def test_customer_update_with_valid_data():
    customer = CustomerUpdate(
        full_name="John Updated",
        phone="9876543210"
    )

    assert customer.full_name == "John Updated"


def test_customer_update_does_not_include_email():
    assert "email" not in CustomerUpdate.model_fields
