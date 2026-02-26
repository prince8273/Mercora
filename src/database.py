"""Database connection and session management"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from src.config import settings

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """
    Dependency for getting database sessions
    
    WARNING: This does NOT enforce tenant filtering automatically.
    Use get_tenant_db() for tenant-isolated operations.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Import tenant session utilities
from src.tenant_session import (
    set_tenant_context,
    get_tenant_context,
    clear_tenant_context,
    get_tenant_db,
    TenantAwareQuery,
    validate_tenant_access,
    TenantIsolationError
)

__all__ = [
    "engine",
    "AsyncSessionLocal",
    "Base",
    "get_db",
    "init_db",
    "set_tenant_context",
    "get_tenant_context",
    "clear_tenant_context",
    "get_tenant_db",
    "TenantAwareQuery",
    "validate_tenant_access",
    "TenantIsolationError"
]
