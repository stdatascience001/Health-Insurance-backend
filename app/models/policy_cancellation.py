import uuid

from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.connection import Base


class PolicyCancellationRequest(Base):
    __tablename__ = "policy_cancellation_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("policies.id"), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)

    reason = Column(String(100), nullable=False)
    additional_comments = Column(Text, nullable=True)

    status = Column(String(20), nullable=False, default="pending")

    admin_remarks = Column(Text, nullable=True)

    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    policy = relationship("Policy")
    customer = relationship("Customer")
    reviewer = relationship("User")
