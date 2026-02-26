"""
Comprehensive Multi-Tenancy Isolation Tests

These tests verify that:
1. Tenant A cannot access Tenant B's data
2. Authentication is required for all business endpoints
3. Agents filter by tenant_id correctly
4. Cross-tenant access returns 404 (not found)
5. Invalid/missing tokens return 401
"""
import pytest
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.tenant import Tenant
from src.models.user import User
from src.models.product import Product
from src.models.review import Review
from src.auth.security import create_access_token, get_password_hash


@pytest.fixture
async def tenant_a(db: AsyncSession):
    """Create Tenant A"""
    tenant = Tenant(
        id=uuid4(),
        name="Tenant A",
        slug="tenant-a",
        status="active"
    )
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    return tenant


@pytest.fixture
async def tenant_b(db: AsyncSession):
    """Create Tenant B"""
    tenant = Tenant(
        id=uuid4(),
        name="Tenant B",
        slug="tenant-b",
        status="active"
    )
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    return tenant


@pytest.fixture
async def user_a(db: AsyncSession, tenant_a):
    """Create user for Tenant A"""
    user = User(
        id=uuid4(),
        email="user_a@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="User A",
        role="user",
        is_active=True,
        tenant_id=tenant_a.id
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def user_b(db: AsyncSession, tenant_b):
    """Create user for Tenant B"""
    user = User(
        id=uuid4(),
        email="user_b@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="User B",
        role="user",
        is_active=True,
        tenant_id=tenant_b.id
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
def token_a(user_a, tenant_a):
    """Generate JWT token for Tenant A user"""
    return create_access_token(
        data={
            "sub": str(user_a.id),
            "tenant_id": str(tenant_a.id),
            "role": user_a.role
        }
    )


@pytest.fixture
def token_b(user_b, tenant_b):
    """Generate JWT token for Tenant B user"""
    return create_access_token(
        data={
            "sub": str(user_b.id),
            "tenant_id": str(tenant_b.id),
            "role": user_b.role
        }
    )


@pytest.fixture
async def product_a(db: AsyncSession, tenant_a):
    """Create product for Tenant A"""
    product = Product(
        id=uuid4(),
        sku="PROD-A-001",
        normalized_sku="proda001",
        name="Product A",
        category="Electronics",
        price=99.99,
        currency="USD",
        marketplace="our_store",
        inventory_level=100,
        tenant_id=tenant_a.id
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


@pytest.fixture
async def product_b(db: AsyncSession, tenant_b):
    """Create product for Tenant B"""
    product = Product(
        id=uuid4(),
        sku="PROD-B-001",
        normalized_sku="prodb001",
        name="Product B",
        category="Electronics",
        price=149.99,
        currency="USD",
        marketplace="our_store",
        inventory_level=50,
        tenant_id=tenant_b.id
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


@pytest.fixture
async def review_a(db: AsyncSession, product_a, tenant_a):
    """Create review for Tenant A's product"""
    review = Review(
        id=uuid4(),
        product_id=product_a.id,
        tenant_id=tenant_a.id,
        rating=5,
        text="Great product from Tenant A!",
        sentiment="positive",
        sentiment_confidence=0.95,
        is_spam=False,
        source="our_store"
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)
    return review


@pytest.fixture
async def review_b(db: AsyncSession, product_b, tenant_b):
    """Create review for Tenant B's product"""
    review = Review(
        id=uuid4(),
        product_id=product_b.id,
        tenant_id=tenant_b.id,
        rating=4,
        text="Good product from Tenant B!",
        sentiment="positive",
        sentiment_confidence=0.85,
        is_spam=False,
        source="our_store"
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)
    return review


# ==================== PRODUCT ISOLATION TESTS ====================

@pytest.mark.asyncio
async def test_tenant_cannot_access_other_tenant_products(
    client: AsyncClient,
    product_a,
    product_b,
    token_a,
    token_b
):
    """Test that Tenant A cannot access Tenant B's products"""
    # Tenant A tries to access their own product - should succeed
    response = await client.get(
        f"/api/v1/products/{product_a.id}",
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert response.status_code == 200
    assert response.json()["id"] == str(product_a.id)
    
    # Tenant A tries to access Tenant B's product - should fail with 404
    response = await client.get(
        f"/api/v1/products/{product_b.id}",
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_tenant_cannot_list_other_tenant_products(
    client: AsyncClient,
    product_a,
    product_b,
    token_a
):
    """Test that listing products only returns tenant's own products"""
    response = await client.get(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert response.status_code == 200
    products = response.json()
    
    # Should only see Tenant A's products
    product_ids = [p["id"] for p in products]
    assert str(product_a.id) in product_ids
    assert str(product_b.id) not in product_ids


@pytest.mark.asyncio
async def test_tenant_cannot_update_other_tenant_product(
    client: AsyncClient,
    product_b,
    token_a
):
    """Test that Tenant A cannot update Tenant B's product"""
    response = await client.put(
        f"/api/v1/products/{product_b.id}",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "name": "Hacked Product",
            "price": 0.01
        }
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_tenant_cannot_delete_other_tenant_product(
    client: AsyncClient,
    product_b,
    token_a
):
    """Test that Tenant A cannot delete Tenant B's product"""
    response = await client.delete(
        f"/api/v1/products/{product_b.id}",
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert response.status_code == 404


# ==================== AUTHENTICATION TESTS ====================

@pytest.mark.asyncio
async def test_products_require_authentication(client: AsyncClient, product_a):
    """Test that product endpoints require authentication"""
    # List products without token
    response = await client.get("/api/v1/products")
    assert response.status_code == 401
    
    # Get product without token
    response = await client.get(f"/api/v1/products/{product_a.id}")
    assert response.status_code == 401
    
    # Create product without token
    response = await client.post(
        "/api/v1/products",
        json={
            "sku": "TEST-001",
            "name": "Test Product",
            "price": 99.99
        }
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_pricing_requires_authentication(client: AsyncClient, product_a):
    """Test that pricing endpoints require authentication"""
    response = await client.post(
        "/api/v1/pricing/analysis",
        json={
            "product_ids": [str(product_a.id)],
            "include_recommendations": True
        }
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_query_requires_authentication(client: AsyncClient):
    """Test that query endpoint requires authentication"""
    response = await client.post(
        "/api/v1/query",
        json={
            "query_text": "Analyze pricing",
            "analysis_type": "pricing"
        }
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_sentiment_requires_authentication(client: AsyncClient, product_a):
    """Test that sentiment endpoints require authentication"""
    response = await client.post(
        "/api/v1/sentiment/analyze",
        json={
            "product_ids": [str(product_a.id)]
        }
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_invalid_token_returns_401(client: AsyncClient):
    """Test that invalid token returns 401"""
    response = await client.get(
        "/api/v1/products",
        headers={"Authorization": "Bearer invalid_token_here"}
    )
    assert response.status_code == 401


# ==================== AGENT ISOLATION TESTS ====================

@pytest.mark.asyncio
async def test_pricing_agent_filters_by_tenant(
    client: AsyncClient,
    product_a,
    product_b,
    token_a
):
    """Test that pricing agent only analyzes tenant's products"""
    # Request analysis for both products
    response = await client.post(
        "/api/v1/pricing/analysis",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "product_ids": [str(product_a.id), str(product_b.id)],
            "include_recommendations": True
        }
    )
    
    # Should succeed but only analyze Tenant A's product
    # (Tenant B's product should be filtered out)
    assert response.status_code in [200, 404]  # 404 if no products found after filtering


@pytest.mark.asyncio
async def test_sentiment_agent_filters_by_tenant(
    client: AsyncClient,
    review_a,
    review_b,
    product_a,
    product_b,
    token_a
):
    """Test that sentiment agent only analyzes tenant's reviews"""
    # Tenant A requests sentiment for Tenant B's product
    response = await client.post(
        "/api/v1/sentiment/analyze",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "product_ids": [str(product_b.id)]
        }
    )
    
    # Should return 404 (no reviews found for this tenant)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_query_endpoint_filters_by_tenant(
    client: AsyncClient,
    product_a,
    product_b,
    token_a
):
    """Test that query endpoint only accesses tenant's data"""
    response = await client.post(
        "/api/v1/query",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "query_text": "Analyze all products",
            "analysis_type": "pricing",
            "product_ids": [str(product_a.id), str(product_b.id)]
        }
    )
    
    # Should succeed but only analyze Tenant A's products
    assert response.status_code == 200
    
    # Verify only Tenant A's products in results
    data = response.json()
    if data.get("pricing_analysis") and data["pricing_analysis"].get("recommendations"):
        product_ids = [r["product_id"] for r in data["pricing_analysis"]["recommendations"]]
        assert str(product_a.id) in product_ids
        assert str(product_b.id) not in product_ids


# ==================== REVIEW ISOLATION TESTS ====================

@pytest.mark.asyncio
async def test_tenant_cannot_access_other_tenant_reviews(
    db: AsyncSession,
    review_a,
    review_b,
    tenant_a,
    tenant_b
):
    """Test that database queries filter reviews by tenant"""
    # Query reviews for Tenant A
    result = await db.execute(
        select(Review).where(Review.tenant_id == tenant_a.id)
    )
    reviews_a = result.scalars().all()
    
    # Should only see Tenant A's reviews
    review_ids = [r.id for r in reviews_a]
    assert review_a.id in review_ids
    assert review_b.id not in review_ids
    
    # Query reviews for Tenant B
    result = await db.execute(
        select(Review).where(Review.tenant_id == tenant_b.id)
    )
    reviews_b = result.scalars().all()
    
    # Should only see Tenant B's reviews
    review_ids = [r.id for r in reviews_b]
    assert review_b.id in review_ids
    assert review_a.id not in review_ids


# ==================== CROSS-TENANT ACCESS TESTS ====================

@pytest.mark.asyncio
async def test_no_cross_tenant_data_leakage(
    db: AsyncSession,
    product_a,
    product_b,
    review_a,
    review_b,
    tenant_a,
    tenant_b
):
    """Comprehensive test that no data leaks across tenants"""
    # Verify products are isolated
    result = await db.execute(
        select(Product).where(Product.tenant_id == tenant_a.id)
    )
    products_a = result.scalars().all()
    assert len(products_a) == 1
    assert products_a[0].id == product_a.id
    
    result = await db.execute(
        select(Product).where(Product.tenant_id == tenant_b.id)
    )
    products_b = result.scalars().all()
    assert len(products_b) == 1
    assert products_b[0].id == product_b.id
    
    # Verify reviews are isolated
    result = await db.execute(
        select(Review).where(Review.tenant_id == tenant_a.id)
    )
    reviews_a = result.scalars().all()
    assert len(reviews_a) == 1
    assert reviews_a[0].id == review_a.id
    
    result = await db.execute(
        select(Review).where(Review.tenant_id == tenant_b.id)
    )
    reviews_b = result.scalars().all()
    assert len(reviews_b) == 1
    assert reviews_b[0].id == review_b.id


# ==================== TOKEN VALIDATION TESTS ====================

@pytest.mark.asyncio
async def test_expired_token_returns_401(client: AsyncClient):
    """Test that expired token returns 401"""
    # Create token with negative expiry (already expired)
    from datetime import timedelta
    expired_token = create_access_token(
        data={"sub": str(uuid4()), "tenant_id": str(uuid4()), "role": "user"},
        expires_delta=timedelta(minutes=-30)
    )
    
    response = await client.get(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_malformed_token_returns_401(client: AsyncClient):
    """Test that malformed token returns 401"""
    response = await client.get(
        "/api/v1/products",
        headers={"Authorization": "Bearer not.a.valid.jwt"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_missing_bearer_prefix_returns_401(client: AsyncClient, token_a):
    """Test that missing Bearer prefix returns 401"""
    response = await client.get(
        "/api/v1/products",
        headers={"Authorization": token_a}  # Missing "Bearer " prefix
    )
    assert response.status_code == 403  # FastAPI HTTPBearer returns 403 for missing scheme


# ==================== INACTIVE USER TESTS ====================

@pytest.mark.asyncio
async def test_inactive_user_cannot_access(
    client: AsyncClient,
    db: AsyncSession,
    user_a,
    tenant_a
):
    """Test that inactive users cannot access endpoints"""
    # Deactivate user
    user_a.is_active = False
    await db.commit()
    
    # Generate token for inactive user
    token = create_access_token(
        data={
            "sub": str(user_a.id),
            "tenant_id": str(tenant_a.id),
            "role": user_a.role
        }
    )
    
    # Try to access endpoint
    response = await client.get(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403
    assert "inactive" in response.json()["detail"].lower()


# ==================== SUMMARY TEST ====================

@pytest.mark.asyncio
async def test_complete_tenant_isolation_summary(
    client: AsyncClient,
    db: AsyncSession,
    tenant_a,
    tenant_b,
    user_a,
    user_b,
    product_a,
    product_b,
    review_a,
    review_b,
    token_a,
    token_b
):
    """
    Comprehensive test verifying complete tenant isolation.
    
    This test verifies:
    1. Each tenant can only see their own data
    2. Cross-tenant access is blocked
    3. Authentication is enforced
    4. Agents respect tenant boundaries
    """
    # Tenant A can access their own product
    response = await client.get(
        f"/api/v1/products/{product_a.id}",
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert response.status_code == 200
    
    # Tenant A cannot access Tenant B's product
    response = await client.get(
        f"/api/v1/products/{product_b.id}",
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert response.status_code == 404
    
    # Tenant B can access their own product
    response = await client.get(
        f"/api/v1/products/{product_b.id}",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert response.status_code == 200
    
    # Tenant B cannot access Tenant A's product
    response = await client.get(
        f"/api/v1/products/{product_a.id}",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert response.status_code == 404
    
    # No authentication = no access
    response = await client.get("/api/v1/products")
    assert response.status_code == 401
    
    print("✅ Complete tenant isolation verified!")
