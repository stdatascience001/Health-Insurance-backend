import uuid

from sqlalchemy import Column, String, Text, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.connection import Base


class PlanBenefit(Base):
    __tablename__ = "plan_benefits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    plan_id = Column(UUID(as_uuid=True),ForeignKey("plans.id"), nullable=False)

    benefit_name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    is_included = Column(Boolean, default=True, nullable=False)

    plan = relationship("Plan", back_populates="benefits")