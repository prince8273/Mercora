"""CRUD operations for Tenant model"""
from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.tenant import Tenant


async def get_tenant_by_id(db: AsyncSession, tenant_id: UUID) -> Optional[Tenant]:
    """Get a tenant by ID"""
    result = await db.execute(
        select(Tenant).where(Tenant.id == tenant_id)
    )
    return result.scalar_one_or_none()


async def get_tenant_by_slug(db: AsyncSession, slug: str) -> Optional[Tenant]:
    """Get a tenant by slug"""
    result = await db.execute(
        select(Tenant).where(Tenant.slug == slug)
    )
    return result.scalar_one_or_none()


async def create_tenant(
    db: AsyncSession,
    name: str,
    slug: str,
    contact_email: Optional[str] = None,
    plan: str = "free"
) -> Tenant:
    """
    Create a new tenant
    
    Args:
        db: Database session
        name: Tenant name
        slug: Unique tenant slug
        contact_email: Optional contact email
        plan: Subscription plan (free, basic, pro, enterprise)
    
    Returns:
        Created Tenant object
    """
    # Set limits based on plan
    plan_limits = {
        "free": {"max_products": 100, "max_users": 5},
        "basic": {"max_products": 1000, "max_users": 10},
        "pro": {"max_products": 10000, "max_users": 50},
        "enterprise": {"max_products": 100000, "max_users": 500}
    }
    
    limits = plan_limits.get(plan, plan_limits["free"])
    
    tenant = Tenant(
        name=name,
        slug=slug,
        contact_email=contact_email,
        plan=plan,
        max_products=limits["max_products"],
        max_users=limits["max_users"],
        is_active=True
    )
    
    db.add(tenant)
    await db.flush()
    await db.refresh(tenant)
    
    return tenant


async def update_tenant_status(
    db: AsyncSession,
    tenant_id: UUID,
    is_active: bool
) -> Optional[Tenant]:
    """Update tenant active status"""
    tenant = await get_tenant_by_id(db, tenant_id)
    if tenant:
        tenant.is_active = is_active
        await db.flush()
        await db.refresh(tenant)
    return tenant
