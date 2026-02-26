"""Authentication dependencies for FastAPI"""
from typing import Optional
from uuid import UUID, uuid4
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db, set_tenant_context
from src.models.user import User
from src.auth.security import decode_access_token
from src.config import settings

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)  # Don't auto-error in demo mode


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from JWT token
    
    In DEMO_MODE: Returns a mock demo user without authentication
    
    Args:
        credentials: HTTP Bearer credentials containing JWT token
        db: Database session
    
    Returns:
        User object
    
    Raises:
        HTTPException: If token is invalid or user not found (only in production mode)
    """
    # DEMO MODE: Return mock user without authentication
    if settings.demo_mode:
        demo_tenant_id = UUID('54d459ab-4ae8-480a-9d1c-d53b218a4fb2')
        set_tenant_context(demo_tenant_id)
        
        # Return mock demo user
        demo_user = User(
            id=UUID('83bf2b99-5d62-4c1a-9703-92191eeb84b7'),
            tenant_id=demo_tenant_id,
            email="seller@tenant-001.com",
            hashed_password="",  # Not used in demo mode
            full_name="TechGear Pro Seller",
            is_active=True,
            is_superuser=True
        )
        return demo_user
    
    # PRODUCTION MODE: Require authentication
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode the JWT token
        payload = decode_access_token(credentials.credentials)
        user_id: str = payload.get("sub")
        tenant_id: str = payload.get("tenant_id")
        
        if user_id is None or tenant_id is None:
            raise credentials_exception
        
        # Convert to UUID
        user_uuid = UUID(user_id)
        tenant_uuid = UUID(tenant_id)
        
        # CRITICAL: Set tenant context for this request
        set_tenant_context(tenant_uuid)
        
    except (JWTError, ValueError):
        raise credentials_exception
    
    # Fetch user from database
    result = await db.execute(
        select(User).where(
            User.id == user_uuid,
            User.tenant_id == tenant_uuid
        )
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get the current active user
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        User object if active
    
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


async def get_tenant_id(
    current_user: User = Depends(get_current_active_user)
) -> UUID:
    """
    Extract tenant_id from current user
    
    This is the primary dependency for tenant isolation.
    All API endpoints should use this to get the tenant context.
    
    IMPORTANT: This also sets the tenant context for the request,
    which enables automatic tenant filtering in database queries.
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        Tenant UUID
    """
    # Tenant context is already set in get_current_user
    return current_user.tenant_id


def require_role(required_role: str):
    """
    Dependency factory for role-based access control
    
    Args:
        required_role: Required role (user, admin, superuser)
    
    Returns:
        Dependency function
    """
    async def role_checker(
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> bool:
        """Check if user has required role"""
        try:
            payload = decode_access_token(credentials.credentials)
            user_role = payload.get("role", "user")
            
            # Superuser has access to everything
            if user_role == "superuser":
                return True
            
            # Admin has access to admin and user
            if required_role == "admin" and user_role in ["admin", "superuser"]:
                return True
            
            # Check exact role match
            if user_role == required_role:
                return True
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}"
            )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    
    return role_checker


async def get_current_user_from_token(token: str) -> Optional[User]:
    """
    Get user from JWT token string (for WebSocket authentication).
    
    This is a simplified version of get_current_user that takes
    a token string directly instead of using FastAPI dependencies.
    
    Args:
        token: JWT token string
        
    Returns:
        User object if token is valid, None otherwise
    """
    # DEMO MODE: Return mock user
    if settings.demo_mode:
        demo_tenant_id = UUID('54d459ab-4ae8-480a-9d1c-d53b218a4fb2')
        return User(
            id=UUID('83bf2b99-5d62-4c1a-9703-92191eeb84b7'),
            tenant_id=demo_tenant_id,
            email="seller@tenant-001.com",
            hashed_password="",
            full_name="TechGear Pro Seller",
            is_active=True,
            is_superuser=True
        )
    
    try:
        # Decode the JWT token
        payload = decode_access_token(token)
        user_id: str = payload.get("sub")
        tenant_id: str = payload.get("tenant_id")
        
        if user_id is None or tenant_id is None:
            return None
        
        # Convert to UUID
        user_uuid = UUID(user_id)
        tenant_uuid = UUID(tenant_id)
        
        # For WebSocket, we create a mock user object
        # In production, you'd want to fetch from database
        return User(
            id=user_uuid,
            tenant_id=tenant_uuid,
            email=payload.get("email", ""),
            hashed_password="",
            full_name=payload.get("full_name", ""),
            is_active=True,
            is_superuser=payload.get("is_superuser", False)
        )
        
    except (JWTError, ValueError):
        return None
