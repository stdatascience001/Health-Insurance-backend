
import pytest
from pydantic import ValidationError

from app.schemas.auth import RegisterRequest, LoginRequest, LoginResponse


def test_register_with_valid_data():
    data = RegisterRequest(
        full_name="John Smith",
        email="john@example.com",
        phone="9876543210",
        password="password123",
        confirm_password="password123"
    )

    assert data.full_name == "John Smith"
    assert data.email == "john@example.com"


def test_register_with_invalid_email():
    with pytest.raises(ValidationError):
        RegisterRequest(
            full_name="John Smith",
            email="invalid-email",
            password="password123",
            confirm_password="password123"
        )


def test_register_with_short_password():
    with pytest.raises(ValidationError):
        RegisterRequest(
            full_name="John Smith",
            email="john@example.com",
            password="123",
            confirm_password="123"
        )


def test_register_with_password_mismatch():
    with pytest.raises(ValidationError):
        RegisterRequest(
            full_name="John Smith",
            email="john@example.com",
            password="password123",
            confirm_password="password456"
        )


def test_login_with_valid_data():
    data = LoginRequest(
        email="john@example.com",
        password="password123"
    )

    assert data.email == "john@example.com"


def test_login_response():
    response = LoginResponse(
        access_token="sample_token"
    )

    assert response.access_token == "sample_token"
    assert response.token_type == "bearer"
