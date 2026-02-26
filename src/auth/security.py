"""Security utilities for password hashing and JWT tokens"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID
from passlib.context import CryptContext
from jose import JWTError, jwt
from src.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


def create_access_token(
    user_id: UUID,
    tenant_id: UUID,
    role: str = "user",
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token
    
    Args:
        user_id: User's UUID
        tenant_id: Tenant's UUID
        role: User's role (user, admin, superuser)
        expires_delta: Optional custom expiration time
    
    Returns:
        Encoded JWT token string
    """
    # Use timezone-aware UTC and compute once to avoid timing drift
    now = datetime.now(timezone.utc)
    
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.access_token_expire_minutes)
    
    # JWT standard expects numeric timestamps (seconds since epoch)
    to_encode = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "role": role,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp())
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    Decode and validate a JWT access token
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded token payload
    
    Raises:
        JWTError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        return payload
    except JWTError as e:
        raise JWTError(f"Invalid token: {str(e)}")
