import uuid

from sqlalchemy import (
    Column,
    String,
    Date,
    DateTime,
    Text,
    ForeignKey,
    Numeric,
    Integer,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.connection import Base


class InsuranceApplication(Base):
    __tablename__ = "insurance_applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)

    plan_id = Column(UUID(as_uuid=True), ForeignKey("plans.id"), nullable=False)

    # Pricing details selected at the time of application
    pricing_rule_id = Column(
        UUID(as_uuid=True), ForeignKey("plan_pricing_rules.id"), nullable=True
    )

    duration_months = Column(Integer, nullable=True)
    premium_frequency = Column(String(30), nullable=True)

    # Customer information
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String(20), nullable=False)
    address = Column(Text, nullable=False)

    # Nominee information
    nominee_name = Column(String(150), nullable=False)
    nominee_relationship = Column(String(50), nullable=False)
    nominee_dob = Column(Date, nullable=True)
    nominee_phone = Column(String(20), nullable=True)

    # Medical declaration
    medical_history = Column(Text, nullable=True)

    # Plan details at the time of application
    premium_amount = Column(Numeric(10, 2), nullable=False)
    coverage_amount = Column(Numeric(12, 2), nullable=False)

    # Application status
    status = Column(String(20), nullable=False, default="pending")
    rejection_reason = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="applications")
    plan = relationship("Plan", back_populates="applications")
    pricing_rule = relationship("PlanPricingRule")
