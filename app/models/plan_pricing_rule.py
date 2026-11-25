import uuid

from sqlalchemy import Column, Integer, Numeric, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.connection import Base


class PlanPricingRule(Base):
    __tablename__ = "plan_pricing_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    plan_id = Column(UUID(as_uuid=True),ForeignKey("plans.id"),nullable=False)

    min_age = Column(Integer, nullable=False)
    max_age = Column(Integer, nullable=False)

    coverage_amount = Column(Numeric(12, 2), nullable=False)
    duration_months = Column(Integer, nullable=False)

    premium_frequency = Column(String(30), nullable=False)
    premium_amount = Column(Numeric(10, 2), nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)

    plan = relationship("Plan", back_populates="pricing_rules")