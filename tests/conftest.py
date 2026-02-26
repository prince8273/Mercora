"""Pytest configuration and fixtures"""
import pytest
import asyncio
import os
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker, AsyncEngine, AsyncConnection
from uuid import UUID, uuid4

from src.main import app
from src.database import Base, get_db
# Import all models to register with SQLAlchemy
from src.models.role import Role  # Import Role first
from src.models.product import Product
from src.models.tenant import Tenant
from src.models.user import User
from src.models.review import Review
from src.models.sales_record import SalesRecord
from src.models.price_history import PriceHistory
from src.models.analytical_report import AnalyticalReport
from src.models.forecast_result import ForecastResult
from src.models.aggregated_metrics import AggregatedMetrics


# Using pytest-asyncio's default event_loop fixture
# No need to override unless custom behavior is required


@pytest.fixture(autouse=True)
def fast_password_hash(monkeypatch):
    """
    Replace bcrypt hashing with a fast deterministic stub for property tests.
    
    This removes bcrypt computational cost entirely, making tests fast and deterministic.
    Auth security is tested separately in dedicated auth tests.
    Multi-tenant isolation tests should not be coupled to crypto cost.
    """
    from src.auth import security
    
    def fake_hash(password: str) -> str:
        """Fast deterministic password hash for testing"""
        return f"hashed::{password}"
    
    def fake_verify(plain_password: str, hashed_password: str) -> bool:
        """Fast deterministic password verification for testing"""
        return hashed_password == f"hashed::{plain_password}"
    
    monkeypatch.setattr(security, "get_password_hash", fake_hash)
    monkeypatch.setattr(security, "verify_password", fake_verify)


@pytest.fixture(scope="function")
def test_tenant_id() -> UUID:
    """Provide a unique test tenant ID per test"""
    return uuid4()


@pytest.fixture(scope="function")
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """
    Create a fresh in-memory SQLite engine per test.
    
    This ensures complete isolation between tests and Hypothesis examples.
    Each test gets its own database that is destroyed after the test completes.
    """
    # Create a new in-memory database for this test
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=None  # Disable pooling for test isolation
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Clean up: drop all tables and dispose engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture(scope="function")
async def async_db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create an isolated database session with transaction rollback.
    
    This fixture:
    - Opens a connection from the test engine
    - Begins a transaction
    - Binds a session to that connection
    - Yields the session for the test
    - ALWAYS rolls back the transaction after the test (even on success)
    - Closes the connection
    
    This ensures:
    - Each test has a fresh session
    - No state leaks between tests
    - Hypothesis reruns are deterministic
    - Full compatibility with property-based testing
    
    CRITICAL: We manually control the transaction and force rollback.
    Using 'async with connection.begin()' would commit on successful exit,
    which would persist test data and cause state leakage.
    """
    async with test_engine.connect() as connection:
        # Begin transaction manually (not as context manager)
        transaction = await connection.begin()
        
        # Create session bound to this connection
        TestSessionLocal = async_sessionmaker(
            bind=connection,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
        
        session = TestSessionLocal()
        
        try:
            yield session
        finally:
            await session.close()
            # ALWAYS rollback - never commit test data
            await transaction.rollback()


@pytest.fixture(scope="function")
async def test_db(async_db_session: AsyncSession) -> AsyncSession:
    """Alias for async_db_session to match existing test expectations"""
    return async_db_session


@pytest.fixture(scope="function")
async def db_session(async_db_session: AsyncSession) -> AsyncSession:
    """Another alias for async_db_session to match test expectations"""
    return async_db_session


@pytest.fixture(scope="function")
async def test_product_id(test_db: AsyncSession, test_tenant_id: UUID) -> UUID:
    """Create a test product and return its ID"""
    from src.models.product import Product
    from decimal import Decimal
    
    product = Product(
        id=uuid4(),
        tenant_id=test_tenant_id,
        sku="TEST-SKU-001",
        normalized_sku="TESTSKU001",
        name="Test Product",
        category="Test Category",
        price=Decimal("99.99"),
        currency="USD",
        marketplace="test-marketplace",
        inventory_level=100
    )
    
    test_db.add(product)
    await test_db.flush()
    await test_db.refresh(product)
    
    return product.id


@pytest.fixture(scope="function")
async def client(test_db: AsyncSession, test_tenant_id: UUID) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database override"""
    from src.models.user import User
    from src.auth.dependencies import get_current_active_user, get_tenant_id
    
    # Create a test user for this specific test
    test_user = User(
        id=uuid4(),
        tenant_id=test_tenant_id,
        email="test@example.com",
        hashed_password="test_hash",
        is_active=True
    )
    
    async def override_get_db():
        yield test_db
    
    async def override_get_current_active_user():
        return test_user
    
    async def override_get_tenant_id():
        return test_tenant_id
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_active_user] = override_get_current_active_user
    app.dependency_overrides[get_tenant_id] = override_get_tenant_id
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()
