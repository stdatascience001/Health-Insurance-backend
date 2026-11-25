from sqlalchemy import Column, String, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.database.connection import Base


class Plan(Base):
    __tablename__ = "plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Basic Plan Information
    name = Column(String(100), nullable=False)
    description = Column(String, nullable=True)
    plan_type = Column(String(50), nullable=False)

    min_entry_age = Column(Integer, nullable=False)
    max_entry_age = Column(Integer, nullable=False)

    # Policy Duration (in months)
    duration_months = Column(Integer, nullable=False)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    applications = relationship("InsuranceApplication", back_populates="plan")

    benefits = relationship("PlanBenefit",back_populates="plan",cascade="all, delete-orphan")
    conditions = relationship("PlanCondition",back_populates="plan",cascade="all, delete-orphan")

    pricing_rules = relationship("PlanPricingRule",back_populates="plan",cascade="all, delete-orphan")

    premium_quotes = relationship("PremiumQuote",back_populates="plan")