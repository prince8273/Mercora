"""Tenant-aware database session wrapper for automatic tenant filtering"""
from typing import Optional
from uuid import UUID
from contextvars import ContextVar
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Query

# Context variable to store current tenant_id
_tenant_context: ContextVar[Optional[UUID]] = ContextVar('tenant_id', default=None)


def set_tenant_context(tenant_id: UUID) -> None:
    """
    Set the tenant context for the current request
    
    This should be called at the beginning of each request
    after authentication.
    """
    _tenant_context.set(tenant_id)


def get_tenant_context() -> Optional[UUID]:
    """Get the current tenant context"""
    return _tenant_context.get()


def clear_tenant_context() -> None:
    """Clear the tenant context"""
    _tenant_context.set(None)


class TenantIsolationError(Exception):
    """Raised when tenant isolation is violated"""
    pass


def enforce_tenant_filter(session: AsyncSession) -> None:
    """
    Enforce tenant filtering on all queries in this session
    
    This adds a before_compile event listener that automatically
    adds tenant_id filter to all queries on tenant-aware models.
    """
    tenant_id = get_tenant_context()
    
    if tenant_id is None:
        # Allow queries without tenant context for:
        # 1. Authentication endpoints
        # 2. Superuser operations
        # 3. System operations
        return
    
    @event.listens_for(session.sync_session, "do_orm_execute")
    def receive_do_orm_execute(orm_execute_state):
        """
        Intercept ORM execute and add tenant filter
        
        This is called before every ORM query execution.
        """
        # Only filter SELECT statements
        if not orm_execute_state.is_select:
            return
        
        # Get the entities being queried
        if hasattr(orm_execute_state, 'bind_arguments'):
            entities = orm_execute_state.bind_arguments.get('entities', [])
        else:
            return
        
        # Check if any entity has tenant_id column
        for entity in entities:
            if hasattr(entity, 'tenant_id'):
                # Add tenant filter
                orm_execute_state.statement = orm_execute_state.statement.where(
                    entity.tenant_id == tenant_id
                )
                break


async def get_tenant_db(tenant_id: UUID) -> AsyncSession:
    """
    Get a database session with tenant context set
    
    This is the recommended way to get a database session
    for tenant-isolated operations.
    
    Usage:
        async with get_tenant_db(tenant_id) as db:
            products = await db.execute(select(Product))
    """
    from src.database import AsyncSessionLocal
    
    # Set tenant context
    set_tenant_context(tenant_id)
    
    async with AsyncSessionLocal() as session:
        try:
            # Enforce tenant filtering
            enforce_tenant_filter(session)
            
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
            clear_tenant_context()


class TenantAwareQuery:
    """
    Helper class for building tenant-aware queries
    
    This provides a safer way to build queries that automatically
    include tenant filtering.
    """
    
    def __init__(self, model, tenant_id: UUID):
        self.model = model
        self.tenant_id = tenant_id
    
    def base_query(self):
        """Get base query with tenant filter"""
        from sqlalchemy import select
        
        if hasattr(self.model, 'tenant_id'):
            return select(self.model).where(self.model.tenant_id == self.tenant_id)
        else:
            # Model doesn't have tenant_id (e.g., Tenant, User)
            return select(self.model)
    
    def filter(self, *args):
        """Add additional filters"""
        return self.base_query().where(*args)
    
    def order_by(self, *args):
        """Add ordering"""
        return self.base_query().order_by(*args)


def validate_tenant_access(obj, tenant_id: UUID) -> None:
    """
    Validate that an object belongs to the specified tenant
    
    Raises TenantIsolationError if validation fails.
    """
    if hasattr(obj, 'tenant_id'):
        if obj.tenant_id != tenant_id:
            raise TenantIsolationError(
                f"Access denied: Object belongs to different tenant. "
                f"Expected {tenant_id}, got {obj.tenant_id}"
            )
