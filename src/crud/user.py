"""CRUD operations for User model"""
from typing import Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.models.tenant import Tenant
from src.auth.security import get_password_hash, verify_password


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Get a user by email"""
    result = await db.execute(
        select(User).where(User.email == email)
    )
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[User]:
    """Get a user by ID"""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    email: str,
    password: str,
    tenant_id: UUID,
    full_name: Optional[str] = None,
    is_superuser: bool = False
) -> User:
    """
    Create a new user
    
    Args:
        db: Database session
        email: User email
        password: Plain text password (will be hashed)
        tenant_id: Tenant UUID
        full_name: Optional full name
        is_superuser: Whether user is a superuser
    
    Returns:
        Created User object
    """
    hashed_password = get_password_hash(password)
    
    user = User(
        email=email,
        hashed_password=hashed_password,
        tenant_id=tenant_id,
        full_name=full_name,
        is_superuser=is_superuser,
        is_active=True
    )
    
    db.add(user)
    await db.flush()
    await db.refresh(user)
    
    return user


async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str
) -> Optional[User]:
    """
    Authenticate a user by email and password
    
    Args:
        db: Database session
        email: User email
        password: Plain text password
    
    Returns:
        User object if authentication successful, None otherwise
    """
    user = await get_user_by_email(db, email)
    
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    if not user.is_active:
        return None
    
    return user


async def update_last_login(db: AsyncSession, user_id: UUID) -> None:
    """Update user's last login timestamp"""
    user = await get_user_by_id(db, user_id)
    if user:
        user.last_login = datetime.utcnow()
        await db.flush()
