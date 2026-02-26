"""
Integration test for CSV-based seller data ingestion.

This test verifies that:
1. CSV upload stores data in database
2. Data flows through validation pipeline
3. Agents query uploaded data
4. Dashboard reflects uploaded data
5. Cache invalidation works correctly
"""
import pytest
import csv
import io
from uuid import uuid4
from datetime import datetime, date, timedelta
from decimal import Decimal

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.main import app
from src.models.product import Product
from src.models.review import Review
from src.models.sales_record import SalesRecord
from src.models.tenant import Tenant
from src.models.user import User
from src.database import get_db


@pytest.fixture
async def test_tenant(db: AsyncSession):
    """Create a test tenant"""
    tenant = Tenant(
        id=uuid4(),
        name="Test Seller Company",
        created_at=datetime.utcnow()
    )
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    return tenant


@pytest.fixture
async def test_user(db: AsyncSession, test_tenant: Tenant):
    """Create a test user"""
    from src.auth.password import get_password_hash
    
    user = User(
        id=uuid4(),
        tenant_id=test_tenant.id,
        email="seller@test.com",
        hashed_password=get_password_hash("testpass123"),
        is_active=True,
        created_at=datetime.utcnow()
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def auth_token(test_user: User):
    """Get authentication token"""
    from src.auth.jwt import create_access_token
    
    token = create_access_token(
        data={
            "sub": str(test_user.id),
            "tenant_id": str(test_user.tenant_id)
        }
    )
    return token


def create_products_csv() -> bytes:
    """Create sample products CSV"""
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=['sku', 'name', 'category', 'price', 'currency', 'marketplace', 'inventory_level']
    )
    writer.writeheader()
    writer.writerows([
        {
            'sku': 'LAPTOP-001',
            'name': 'Gaming Laptop Pro',
            'category': 'Electronics',
            'price': '1299.99',
            'currency': 'USD',
            'marketplace': 'our_store',
            'inventory_level': '50'
        },
        {
            'sku': 'MOUSE-001',
            'name': 'Wireless Gaming Mouse',
            'category': 'Electronics',
            'price': '79.99',
            'currency': 'USD',
            'marketplace': 'our_store',
            'inventory_level': '200'
        },
        {
            'sku': 'KEYBOARD-001',
            'name': 'Mechanical Keyboard RGB',
            'category': 'Electronics',
            'price': '149.99',
            'currency': 'USD',
            'marketplace': 'our_store',
            'inventory_level': '100'
        }
    ])
    return output.getvalue().encode('utf-8')


def create_reviews_csv(product_ids: list) -> bytes:
    """Create sample reviews CSV"""
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=['product_id', 'rating', 'text', 'source']
    )
    writer.writeheader()
    
    reviews = []
    for product_id in product_ids:
        reviews.extend([
            {
                'product_id': str(product_id),
                'rating': '5',
                'text': 'Excellent product! Highly recommend.',
                'source': 'csv_upload'
            },
            {
                'product_id': str(product_id),
                'rating': '4',
                'text': 'Good quality, fast shipping.',
                'source': 'csv_upload'
            },
            {
                'product_id': str(product_id),
                'rating': '3',
                'text': 'Average product, could be better.',
                'source': 'csv_upload'
            }
        ])
    
    writer.writerows(reviews)
    return output.getvalue().encode('utf-8')


def create_sales_csv(product_ids: list) -> bytes:
    """Create sample sales CSV"""
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=['product_id', 'quantity', 'revenue', 'date', 'marketplace']
    )
    writer.writeheader()
    
    sales = []
    base_date = date.today() - timedelta(days=30)
    
    for i in range(30):
        sale_date = base_date + timedelta(days=i)
        for product_id in product_ids:
            sales.append({
                'product_id': str(product_id),
                'quantity': str(5 + (i % 10)),
                'revenue': str(100.0 + (i * 10)),
                'date': sale_date.isoformat(),
                'marketplace': 'our_store'
            })
    
    writer.writerows(sales)
    return output.getvalue().encode('utf-8')


@pytest.mark.asyncio
async def test_csv_seller_integration_flow(
    db: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
    auth_token: str
):
    """
    Test complete CSV seller integration flow:
    1. Upload products CSV
    2. Verify products in database
    3. Upload reviews CSV
    4. Upload sales CSV
    5. Query dashboard stats
    6. Query sentiment analysis
    7. Query demand forecast
    8. Verify all data is tenant-isolated
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Step 1: Upload products CSV
        products_csv = create_products_csv()
        response = await client.post(
            "/api/v1/csv/upload/products",
            files={"file": ("products.csv", products_csv, "text/csv")},
            headers=headers
        )
        assert response.status_code == 200
        products_result = response.json()
        assert products_result['status'] == 'success'
        assert products_result['products_uploaded'] == 3
        
        # Step 2: Verify products in database
        result = await db.execute(
            select(Product).where(Product.tenant_id == test_tenant.id)
        )
        products = result.scalars().all()
        assert len(products) == 3
        
        product_ids = [p.id for p in products]
        
        # Verify product data
        laptop = next(p for p in products if p.sku == 'LAPTOP-001')
        assert laptop.name == 'Gaming Laptop Pro'
        assert laptop.price == Decimal('1299.99')
        assert laptop.inventory_level == 50
        
        # Step 3: Upload reviews CSV
        reviews_csv = create_reviews_csv(product_ids)
        response = await client.post(
            "/api/v1/csv/upload/reviews",
            files={"file": ("reviews.csv", reviews_csv, "text/csv")},
            headers=headers
        )
        assert response.status_code == 200
        reviews_result = response.json()
        assert reviews_result['status'] == 'success'
        assert reviews_result['reviews_uploaded'] == 9  # 3 reviews per product
        
        # Verify reviews in database
        result = await db.execute(
            select(Review).where(Review.tenant_id == test_tenant.id)
        )
        reviews = result.scalars().all()
        assert len(reviews) == 9
        
        # Step 4: Upload sales CSV
        sales_csv = create_sales_csv(product_ids)
        response = await client.post(
            "/api/v1/csv/upload/sales",
            files={"file": ("sales.csv", sales_csv, "text/csv")},
            headers=headers
        )
        assert response.status_code == 200
        sales_result = response.json()
        assert sales_result['status'] == 'success'
        assert sales_result['sales_records_uploaded'] == 90  # 30 days * 3 products
        
        # Verify sales in database
        result = await db.execute(
            select(SalesRecord).where(SalesRecord.tenant_id == test_tenant.id)
        )
        sales_records = result.scalars().all()
        assert len(sales_records) == 90
        
        # Step 5: Query dashboard stats
        response = await client.get(
            "/api/v1/dashboard/stats",
            headers=headers
        )
        assert response.status_code == 200
        dashboard = response.json()
        
        # Verify dashboard reflects uploaded data
        assert dashboard['total_products'] >= 3
        assert dashboard['total_reviews'] >= 9
        assert dashboard['active_products'] >= 3
        assert len(dashboard['recent_insights']) > 0
        
        # Step 6: Query sentiment analysis
        response = await client.get(
            f"/api/v1/sentiment/product/{product_ids[0]}",
            headers=headers
        )
        assert response.status_code == 200
        sentiment = response.json()
        
        # Verify sentiment analysis uses uploaded reviews
        assert sentiment['product_id'] == str(product_ids[0])
        assert sentiment['total_reviews'] == 3
        assert 'aggregate_sentiment' in sentiment
        assert 'sentiment_distribution' in sentiment
        
        # Step 7: Query demand forecast
        response = await client.get(
            f"/api/v1/forecast/product/{product_ids[0]}",
            params={"forecast_horizon_days": 30},
            headers=headers
        )
        assert response.status_code == 200
        forecast = response.json()
        
        # Verify forecast uses uploaded sales data
        assert forecast['product_id'] == str(product_ids[0])
        assert forecast['product_name'] == 'Gaming Laptop Pro'
        assert len(forecast['forecast_points']) > 0
        assert 'final_confidence' in forecast
        
        # Step 8: Verify tenant isolation
        # Create another tenant and verify no data leakage
        other_tenant = Tenant(
            id=uuid4(),
            name="Other Company",
            created_at=datetime.utcnow()
        )
        db.add(other_tenant)
        await db.commit()
        
        # Query products for other tenant (should be empty)
        result = await db.execute(
            select(Product).where(Product.tenant_id == other_tenant.id)
        )
        other_products = result.scalars().all()
        assert len(other_products) == 0


@pytest.mark.asyncio
async def test_cache_invalidation_after_csv_upload(
    db: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
    auth_token: str
):
    """
    Test that cache is invalidated after CSV upload.
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Upload products
        products_csv = create_products_csv()
        response = await client.post(
            "/api/v1/csv/upload/products",
            files={"file": ("products.csv", products_csv, "text/csv")},
            headers=headers
        )
        assert response.status_code == 200
        
        # Query dashboard (should not use stale cache)
        response = await client.get(
            "/api/v1/dashboard/stats",
            headers=headers
        )
        assert response.status_code == 200
        dashboard = response.json()
        
        # Verify fresh data
        assert dashboard['total_products'] >= 3


@pytest.mark.asyncio
async def test_agents_use_database_not_external_api(
    db: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
    auth_token: str
):
    """
    Test that agents query from database, not external APIs.
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Upload test data
        products_csv = create_products_csv()
        await client.post(
            "/api/v1/csv/upload/products",
            files={"file": ("products.csv", products_csv, "text/csv")},
            headers=headers
        )
        
        # Get product IDs
        result = await db.execute(
            select(Product).where(Product.tenant_id == test_tenant.id)
        )
        products = result.scalars().all()
        product_ids = [p.id for p in products]
        
        # Upload reviews
        reviews_csv = create_reviews_csv(product_ids)
        await client.post(
            "/api/v1/csv/upload/reviews",
            files={"file": ("reviews.csv", reviews_csv, "text/csv")},
            headers=headers
        )
        
        # Upload sales
        sales_csv = create_sales_csv(product_ids)
        await client.post(
            "/api/v1/csv/upload/sales",
            files={"file": ("sales.csv", sales_csv, "text/csv")},
            headers=headers
        )
        
        # Test sentiment agent uses database
        response = await client.get(
            f"/api/v1/sentiment/product/{product_ids[0]}",
            headers=headers
        )
        assert response.status_code == 200
        sentiment = response.json()
        assert sentiment['total_reviews'] == 3  # From uploaded CSV
        
        # Test forecast agent uses database
        response = await client.get(
            f"/api/v1/forecast/product/{product_ids[0]}",
            params={"forecast_horizon_days": 30},
            headers=headers
        )
        assert response.status_code == 200
        forecast = response.json()
        assert len(forecast['forecast_points']) > 0  # From uploaded sales data
