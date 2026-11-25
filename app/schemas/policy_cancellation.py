
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class PolicyCancellationCreate(BaseModel):
    reason: str = Field(..., min_length=3, max_length=100)
    additional_comments: Optional[str] = None


class PolicyCancellationResponse(BaseModel):
    id: UUID
    policy_id: UUID
    customer_id: UUID
    customer_name: str
    customer_email: str
    reason: str
    additional_comments: Optional[str] = None
    status: str
    admin_remarks: Optional[str] = None
    requested_at: datetime
    reviewed_at: Optional[datetime] = None


# For the admin
class PolicyCancellationReview(BaseModel):
    status: str = Field(..., pattern="^(approved|rejected)$")
    admin_remarks: Optional[str] = None
