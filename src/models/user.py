"""User model for authentication"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from src.database import Base
from src.models.product import GUID


class User(Base):
    """User model for authentication and authorization"""
    __tablename__ = "users"
    
    # Primary key
    id = Column(GUID(), primary_key=True, default=uuid4)
    
    # Foreign key to tenant
    tenant_id = Column(GUID(), ForeignKey('tenants.id'), nullable=False)
    
    # User credentials
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    
    # User profile
    full_name = Column(String(255), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    preferences = relationship("UserPreferences", back_populates="user", uselist=False)
    roles = relationship("Role", secondary="user_roles", back_populates="users")
    
    # Indexes
    __table_args__ = (
        Index('idx_users_email', 'email'),
        Index('idx_users_tenant', 'tenant_id'),
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, tenant_id={self.tenant_id})>"
