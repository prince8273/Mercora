"""Role and permission models for RBAC."""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Table, Enum as SQLEnum, TypeDecorator, CHAR
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


class RoleType(str, Enum):
    """Predefined role types."""
    SUPERUSER = "superuser"  # Full system access
    ADMIN = "admin"          # Tenant admin access
    ANALYST = "analyst"      # Read and analyze data
    USER = "user"            # Basic user access
    VIEWER = "viewer"        # Read-only access


class Permission(str, Enum):
    """System permissions."""
    # Data permissions
    READ_DATA = "read_data"
    WRITE_DATA = "write_data"
    DELETE_DATA = "delete_data"
    
    # Query permissions
    EXECUTE_QUERY = "execute_query"
    EXECUTE_DEEP_MODE = "execute_deep_mode"
    
    # Agent permissions
    USE_PRICING_AGENT = "use_pricing_agent"
    USE_SENTIMENT_AGENT = "use_sentiment_agent"
    USE_FORECAST_AGENT = "use_forecast_agent"
    
    # Report permissions
    VIEW_REPORTS = "view_reports"
    CREATE_REPORTS = "create_reports"
    EXPORT_REPORTS = "export_reports"
    
    # Admin permissions
    MANAGE_USERS = "manage_users"
    MANAGE_ROLES = "manage_roles"
    MANAGE_SETTINGS = "manage_settings"
    VIEW_AUDIT_LOGS = "view_audit_logs"
    
    # System permissions
    MANAGE_TENANTS = "manage_tenants"
    SYSTEM_ADMIN = "system_admin"


# Association table for role-permission many-to-many relationship
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', GUID, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    Column('permission', String, primary_key=True)
)


# Association table for user-role many-to-many relationship
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', GUID, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('role_id', GUID, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True)
)


class Role(Base):
    """
    Role model for RBAC.
    
    Roles define sets of permissions that can be assigned to users.
    Supports both predefined system roles and custom tenant-specific roles.
    """
    __tablename__ = "roles"
    
    id = Column(GUID, primary_key=True, default=uuid4)
    tenant_id = Column(GUID, ForeignKey("tenants.id"), nullable=True, index=True)
    
    name = Column(String, nullable=False)
    role_type = Column(SQLEnum(RoleType), nullable=False)
    description = Column(String, nullable=True)
    
    # System roles are predefined and cannot be modified
    is_system_role = Column(Boolean, default=False, nullable=False)
    
    # Active status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="roles")
    users = relationship("User", secondary=user_roles, back_populates="roles")
    
    def __repr__(self):
        return f"<Role {self.name} ({self.role_type})>"
    
    def has_permission(self, permission: Permission) -> bool:
        """
        Check if role has a specific permission.
        
        Args:
            permission: Permission to check
            
        Returns:
            True if role has permission, False otherwise
        """
        # Get permissions for this role from the association table
        # This would be implemented with a proper query in production
        return permission.value in self.get_permissions()
    
    def get_permissions(self) -> List[str]:
        """
        Get all permissions for this role.
        
        Returns:
            List of permission strings
        """
        # This is a simplified implementation
        # In production, this would query the role_permissions table
        return ROLE_PERMISSIONS.get(self.role_type, [])


# Default permissions for each role type
ROLE_PERMISSIONS = {
    RoleType.SUPERUSER: [p.value for p in Permission],  # All permissions
    
    RoleType.ADMIN: [
        Permission.READ_DATA.value,
        Permission.WRITE_DATA.value,
        Permission.DELETE_DATA.value,
        Permission.EXECUTE_QUERY.value,
        Permission.EXECUTE_DEEP_MODE.value,
        Permission.USE_PRICING_AGENT.value,
        Permission.USE_SENTIMENT_AGENT.value,
        Permission.USE_FORECAST_AGENT.value,
        Permission.VIEW_REPORTS.value,
        Permission.CREATE_REPORTS.value,
        Permission.EXPORT_REPORTS.value,
        Permission.MANAGE_USERS.value,
        Permission.MANAGE_ROLES.value,
        Permission.MANAGE_SETTINGS.value,
        Permission.VIEW_AUDIT_LOGS.value,
    ],
    
    RoleType.ANALYST: [
        Permission.READ_DATA.value,
        Permission.EXECUTE_QUERY.value,
        Permission.EXECUTE_DEEP_MODE.value,
        Permission.USE_PRICING_AGENT.value,
        Permission.USE_SENTIMENT_AGENT.value,
        Permission.USE_FORECAST_AGENT.value,
        Permission.VIEW_REPORTS.value,
        Permission.CREATE_REPORTS.value,
        Permission.EXPORT_REPORTS.value,
    ],
    
    RoleType.USER: [
        Permission.READ_DATA.value,
        Permission.EXECUTE_QUERY.value,
        Permission.USE_PRICING_AGENT.value,
        Permission.USE_SENTIMENT_AGENT.value,
        Permission.USE_FORECAST_AGENT.value,
        Permission.VIEW_REPORTS.value,
    ],
    
    RoleType.VIEWER: [
        Permission.READ_DATA.value,
        Permission.VIEW_REPORTS.value,
    ],
}


def get_default_role_permissions(role_type: RoleType) -> List[str]:
    """
    Get default permissions for a role type.
    
    Args:
        role_type: Role type
        
    Returns:
        List of permission strings
    """
    return ROLE_PERMISSIONS.get(role_type, [])
