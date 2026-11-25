from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ContactInquiryCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=150)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=20)
    subject: str = Field(..., min_length=2, max_length=100)
    message: str = Field(..., min_length=10)


class ContactInquiryResponse(BaseModel):
    id: UUID
    full_name: str
    email: str
    phone: str | None
    subject: str
    message: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)