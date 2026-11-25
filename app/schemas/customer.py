
from uuid import UUID
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, EmailStr


class CustomerCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=20)


class CustomerResponse(BaseModel):
    id: UUID
    full_name: str
    email: str
    phone: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CustomerUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
