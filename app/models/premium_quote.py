import uuid

from sqlalchemy import (
    Column,
    String,
    Numeric,
    Integer,
    DateTime,
    ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.connection import Base


class PremiumQuote(Base):
    __tablename__ = "premium_quotes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # References
    plan_id = Column(
        UUID(as_uuid=True),
        ForeignKey("plans.id"),
        nullable=False
    )

    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id"),
        nullable=False
    )

    pricing_rule_id = Column( UUID(as_uuid=True), ForeignKey("plan_pricing_rules.id"), nullable=False)

    # Customer and selected plan details
    customer_age = Column(Integer, nullable=False)
    coverage_amount = Column(Numeric(12, 2), nullable=False)
    duration_months = Column(Integer, nullable=False)

    premium_frequency = Column(String(30), nullable=False)
    premium_amount = Column(Numeric(10, 2), nullable=False)

    # Quote status
    status = Column(String(30), default="pending", nullable=False)

    # Quote timestamps
    created_at = Column(DateTime(timezone=True),server_default=func.now(),nullable=False)

    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    plan = relationship("Plan", back_populates="premium_quotes")
    customer = relationship("Customer")
    pricing_rule = relationship("PlanPricingRule")