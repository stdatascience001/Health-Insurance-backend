import uuid

from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database.connection import Base


class ContactInquiry(Base):
    __tablename__ = "contact_inquiries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    full_name = Column(String(150), nullable=False)
    email = Column(String(150), nullable=False)
    phone = Column(String(20), nullable=True)

    subject = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)

    status = Column(String(20), default="New", nullable=False)

    created_at = Column(DateTime(timezone=True),server_default=func.now())