
import uuid

from sqlalchemy import Column, String, Date, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.connection import Base


class Policy(Base):
    __tablename__ = "policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    policy_number = Column(String(50), unique=True, nullable=False)
    application_id = Column(UUID(as_uuid=True),ForeignKey("insurance_applications.id"),unique=True,nullable=False)
    customer_id = Column(UUID(as_uuid=True),ForeignKey("customers.id"),nullable=False)
    plan_id = Column(UUID(as_uuid=True),  ForeignKey("plans.id"),nullable=False)
    premium_amount = Column(Numeric(10, 2), nullable=False)
    coverage_amount = Column(Numeric(12, 2), nullable=False)

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    status = Column(String(20), default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    application = relationship("InsuranceApplication")
    customer = relationship("Customer")
    plan = relationship("Plan")
