"""Role-Based Access Control (RBAC) utilities."""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models.user import User
from src.models.role import Role, Permission, RoleType, ROLE_PERMISSIONS
from src.auth.dependencies import get_current_active_user


logger = logging.getLogger(__name__)


class RBACService:
    """Service for role-based access control operations."""
    
    @staticmethod
    async def get_user_roles(user: User, db: AsyncSession) -> List[Role]:
        """
        Get all roles for a user.
        
        Args:
            user: User object
            db: Database session
            
        Returns:
            List of Role objects
        """
        # In production, this would query the user_roles association table
        # For now, we'll use a simplified approach based on is_superuser
        if user.is_superuser:
            # Superuser has all permissions
            return [Role(
                id=UUID(int=0),
                tenant_id=user.tenant_id,
                name="Superuser",
                role_type=RoleType.SUPERUSER,
                is_system_role=True,
                is_active=True
            )]
        
        # Default to USER role
        return [Role(
            id=UUID(int=1),
            tenant_id=user.tenant_id,
            name="User",
            role_type=RoleType.USER,
            is_system_role=True,
            is_active=True
        )]
    
    @staticmethod
    async def get_user_permissions(user: User, db: AsyncSession) -> List[str]:
        """
        Get all permissions for a user (aggregated from all roles).
        
        Args:
            user: User object
            db: Database session
            
        Returns:
            List of permission strings
        """
        roles = await RBACService.get_user_roles(user, db)
        
        # Aggregate permissions from all roles
        permissions = set()
        for role in roles:
            permissions.update(role.get_permissions())
        
        return list(permissions)
    
    @staticmethod
    async def user_has_permission(
        user: User,
        permission: Permission,
        db: AsyncSession
    ) -> bool:
        """
        Check if user has a specific permission.
        
        Args:
            user: User object
            permission: Permission to check
            db: Database session
            
        Returns:
            True if user has permission, False otherwise
        """
        permissions = await RBACService.get_user_permissions(user, db)
        return permission.value in permissions
    
    @staticmethod
    async def user_has_role(
        user: User,
        role_type: RoleType,
        db: AsyncSession
    ) -> bool:
        """
        Check if user has a specific role.
        
        Args:
            user: User object
            role_type: Role type to check
            db: Database session
            
        Returns:
            True if user has role, False otherwise
        """
        roles = await RBACService.get_user_roles(user, db)
        return any(role.role_type == role_type for role in roles)
    
    @staticmethod
    async def require_permission(
        user: User,
        permission: Permission,
        db: AsyncSession
    ) -> None:
        """
        Require user to have a specific permission.
        
        Args:
            user: User object
            permission: Required permission
            db: Database session
            
        Raises:
            HTTPException: If user doesn't have permission
        """
        if not await RBACService.user_has_permission(user, permission, db):
            logger.warning(
                f"User {user.id} attempted to access resource requiring "
                f"{permission.value} permission"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {permission.value}"
            )
    
    @staticmethod
    async def require_role(
        user: User,
        role_type: RoleType,
        db: AsyncSession
    ) -> None:
        """
        Require user to have a specific role.
        
        Args:
            user: User object
            role_type: Required role type
            db: Database session
            
        Raises:
            HTTPException: If user doesn't have role
        """
        if not await RBACService.user_has_role(user, role_type, db):
            logger.warning(
                f"User {user.id} attempted to access resource requiring "
                f"{role_type.value} role"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {role_type.value}"
            )


# Dependency factories for FastAPI
def require_permission(permission: Permission):
    """
    Create a FastAPI dependency that requires a specific permission.
    
    Args:
        permission: Required permission
        
    Returns:
        Dependency function
    """
    async def permission_checker(
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        """Check if user has required permission."""
        await RBACService.require_permission(current_user, permission, db)
        return current_user
    
    return permission_checker


def require_role(role_type: RoleType):
    """
    Create a FastAPI dependency that requires a specific role.
    
    Args:
        role_type: Required role type
        
    Returns:
        Dependency function
    """
    async def role_checker(
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        """Check if user has required role."""
        await RBACService.require_role(current_user, role_type, db)
        return current_user
    
    return role_checker


# Convenience dependencies for common permissions
require_read_data = require_permission(Permission.READ_DATA)
require_write_data = require_permission(Permission.WRITE_DATA)
require_delete_data = require_permission(Permission.DELETE_DATA)
require_execute_query = require_permission(Permission.EXECUTE_QUERY)
require_execute_deep_mode = require_permission(Permission.EXECUTE_DEEP_MODE)
require_manage_users = require_permission(Permission.MANAGE_USERS)
require_manage_settings = require_permission(Permission.MANAGE_SETTINGS)
require_view_audit_logs = require_permission(Permission.VIEW_AUDIT_LOGS)

# Convenience dependencies for common roles
require_admin = require_role(RoleType.ADMIN)
require_analyst = require_role(RoleType.ANALYST)
require_superuser = require_role(RoleType.SUPERUSER)
