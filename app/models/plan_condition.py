import uuid

from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.connection import Base


class PlanCondition(Base):
    __tablename__ = "plan_conditions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    plan_id = Column(UUID(as_uuid=True),ForeignKey("plans.id"),nullable=False)

    condition_type = Column(String(100), nullable=False)
    condition_value = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)

    plan = relationship("Plan", back_populates="conditions")