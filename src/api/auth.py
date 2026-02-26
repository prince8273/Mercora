"""Authentication API endpoints"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.schemas.auth import (
    UserLogin,
    UserRegister,
    Token,
    UserResponse,
    TenantCreate,
    TenantResponse
)
from src.crud.user import (
    authenticate_user,
    create_user,
    get_user_by_email,
    update_last_login
)
from src.crud.tenant import (
    create_tenant,
    get_tenant_by_slug
)
from src.auth.security import create_access_token
from src.auth.dependencies import get_current_active_user
from src.models.user import User
from src.config import settings

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user and tenant"
)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user and create a new tenant
    
    This endpoint creates both a tenant and the first user for that tenant.
    The user will be set as an admin for the tenant.
    """
    # Check if email already exists
    existing_user = await get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if tenant slug already exists
    existing_tenant = await get_tenant_by_slug(db, user_data.tenant_slug)
    if existing_tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant slug already taken"
        )
    
    # Create tenant
    tenant = await create_tenant(
        db,
        name=user_data.tenant_slug.replace("-", " ").title(),
        slug=user_data.tenant_slug,
        contact_email=user_data.email,
        plan="free"
    )
    
    # Create user (first user is admin)
    user = await create_user(
        db,
        email=user_data.email,
        password=user_data.password,
        tenant_id=tenant.id,
        full_name=user_data.full_name,
        is_superuser=False  # First user is admin but not superuser
    )
    
    await db.commit()
    
    return user


@router.post(
    "/login",
    response_model=Token,
    summary="Login and get access token"
)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and return JWT access token
    
    The token contains:
    - user_id (sub)
    - tenant_id
    - role
    - expiration time
    """
    # Authenticate user
    user = await authenticate_user(db, credentials.email, credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    await update_last_login(db, user.id)
    await db.commit()
    
    # Determine role
    role = "superuser" if user.is_superuser else "admin"
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        user_id=user.id,
        tenant_id=user.tenant_id,
        role=role,
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user information"
)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get information about the currently authenticated user"""
    return current_user


@router.post(
    "/tenants",
    response_model=TenantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tenant (superuser only)"
)
async def create_tenant_endpoint(
    tenant_data: TenantCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new tenant (superuser only)
    
    This endpoint is for superusers to create tenants directly.
    Regular users should use the /register endpoint.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can create tenants directly"
        )
    
    # Check if tenant slug already exists
    existing_tenant = await get_tenant_by_slug(db, tenant_data.slug)
    if existing_tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant slug already taken"
        )
    
    # Create tenant
    tenant = await create_tenant(
        db,
        name=tenant_data.name,
        slug=tenant_data.slug,
        contact_email=tenant_data.contact_email,
        plan=tenant_data.plan
    )
    
    await db.commit()
    
    return tenant
