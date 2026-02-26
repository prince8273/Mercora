"""User preferences database model"""
from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from src.database import Base


class GUID(TypeDecorator):
    """Platform-independent GUID type.
    
    Uses PostgreSQL's UUID type, otherwise uses CHAR(36), storing as stringified hex values.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PGUUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            if not isinstance(value, uuid4.__class__):
                return str(value)
            else:
                return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid4.__class__):
                from uuid import UUID
                return UUID(value)
            else:
                return value


class UserPreferences(Base):
    """User preferences model for personalization"""
    __tablename__ = "user_preferences"
    
    user_id = Column(GUID, ForeignKey("users.id"), primary_key=True)
    tenant_id = Column(GUID, ForeignKey("tenants.id"), nullable=False, index=True)
    kpi_preferences = Column(JSON, nullable=False, default=dict)
    marketplace_focus = Column(JSON, nullable=False, default=list)  # Stored as JSON array
    business_goals = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="preferences")
    tenant = relationship("Tenant")
