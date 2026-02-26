"""Authentication schemas"""
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserLogin(BaseModel):
    """User login request"""
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserRegister(BaseModel):
    """User registration request"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None
    tenant_slug: str = Field(..., min_length=3, max_length=100)


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenPayload(BaseModel):
    """JWT token payload"""
    sub: UUID  # user_id
    tenant_id: UUID
    role: str
    exp: int
    iat: int


class UserResponse(BaseModel):
    """User response"""
    id: UUID
    email: str
    full_name: Optional[str]
    tenant_id: UUID
    is_active: bool
    is_superuser: bool
    
    model_config = ConfigDict(from_attributes=True)


class TenantCreate(BaseModel):
    """Tenant creation request"""
    name: str = Field(..., min_length=3, max_length=255)
    slug: str = Field(..., min_length=3, max_length=100)
    contact_email: Optional[EmailStr] = None
    plan: str = Field(default="free", pattern="^(free|basic|pro|enterprise)$")


class TenantResponse(BaseModel):
    """Tenant response"""
    id: UUID
    name: str
    slug: str
    contact_email: Optional[str]
    plan: str
    is_active: bool
    max_products: int
    max_users: int
    
    model_config = ConfigDict(from_attributes=True)
