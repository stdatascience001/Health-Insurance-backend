
import uuid

from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.connection import Base


class SuperAdmin(Base):
    __tablename__ = "super_admins"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Verified Microsoft Entra identity
    microsoft_object_id = Column(
        String(100),
        nullable=False,
    )

    microsoft_tenant_id = Column(
        String(100),
        nullable=False,
    )

    email = Column(
        String(255),
        nullable=False,
        index=True,
    )

    display_name = Column(
        String(150),
        nullable=True,
    )

    # Application-level authorization
    role = Column(
        String(30),
        nullable=False,
        default="super_admin",
    )

    # Identifies the one protected Main Admin
    is_primary = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    # Who granted this person's access
    invited_by = Column(
        UUID(as_uuid=True),
        ForeignKey("super_admins.id"),
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    inviter = relationship(
        "SuperAdmin",
        remote_side=[id],
        foreign_keys=[invited_by],
    )

    __table_args__ = (
        # Prevent duplicate Microsoft identities within a tenant
        Index(
            "uq_super_admin_microsoft_identity",
            "microsoft_tenant_id",
            "microsoft_object_id",
            unique=True,
        ),

        # PostgreSQL allows only one Main Admin
        Index(
            "uq_super_admin_primary",
            "is_primary",
            unique=True,
            postgresql_where=text("is_primary = true"),
        ),
    )
