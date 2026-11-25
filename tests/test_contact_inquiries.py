
import pytest
from pydantic import ValidationError

from app.schemas.contact_inquiries import ContactInquiryCreate


def test_contact_inquiry_with_valid_data():
    inquiry = ContactInquiryCreate(
        full_name="John Smith",
        email="john@example.com",
        phone="9876543210",
        subject="Insurance enquiry",
        message="I would like to know more about your insurance plans."
    )

    assert inquiry.subject == "Insurance enquiry"


def test_contact_inquiry_with_invalid_email():
    with pytest.raises(ValidationError):
        ContactInquiryCreate(
            full_name="John Smith",
            email="invalid-email",
            subject="Insurance enquiry",
            message="I need information about insurance."
        )


def test_contact_inquiry_with_short_message():
    with pytest.raises(ValidationError):
        ContactInquiryCreate(
            full_name="John Smith",
            email="john@example.com",
            subject="Insurance enquiry",
            message="Short"
        )


def test_contact_inquiry_without_optional_phone():
    inquiry = ContactInquiryCreate(
        full_name="John Smith",
        email="john@example.com",
        subject="Insurance enquiry",
        message="I need information about insurance."
    )

    assert inquiry.phone is None
