"""Tests for query execution API endpoint"""
import pytest
from uuid import uuid4
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.product import Product


@pytest.mark.asyncio
async def test_execute_query_with_product_ids(
    client: AsyncClient,
    test_db: AsyncSession
):
    """Test query execution with explicit product IDs"""
    # Create test products
    product1 = Product(
        id=uuid4(),
        sku="TEST-001",
        normalized_sku="test-001",
        name="Test Product 1",
        category="Electronics",
        price=Decimal("99.99"),
        currency="USD",
        marketplace="test_marketplace",
        inventory_level=100
    )
    product2 = Product(
        id=uuid4(),
        sku="TEST-002",
        normalized_sku="test-002",
        name="Test Product 2",
        category="Electronics",
        price=Decimal("149.99"),
        currency="USD",
        marketplace="test_marketplace",
        inventory_level=50
    )
    
    test_db.add(product1)
    test_db.add(product2)
    await test_db.commit()
    
    # Execute query
    response = await client.post(
        "/api/v1/query",
        json={
            "query_text": "Analyze pricing for my products",
            "product_ids": [str(product1.id), str(product2.id)],
            "analysis_type": "pricing"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert "query_id" in data
    assert "executive_summary" in data
    assert "key_metrics" in data
    assert "pricing_analysis" in data
    assert "confidence_score" in data
    assert "created_at" in data
    
    # Verify executive summary is not empty
    assert len(data["executive_summary"]) > 0
    
    # Verify confidence score is valid
    assert 0 <= data["confidence_score"] <= 1
    
    # Verify key metrics
    assert "price_gaps_identified" in data["key_metrics"]
    assert "recommendations_generated" in data["key_metrics"]


@pytest.mark.asyncio
async def test_execute_query_without_product_ids(
    client: AsyncClient,
    test_db: AsyncSession
):
    """Test query execution without explicit product IDs (uses sample products)"""
    # Create test products
    for i in range(3):
        product = Product(
            id=uuid4(),
            sku=f"AUTO-{i:03d}",
            normalized_sku=f"auto-{i:03d}",
            name=f"Auto Product {i}",
            category="Test",
            price=Decimal(f"{100 + i * 10}.00"),
            currency="USD",
            marketplace="test_marketplace",
            inventory_level=100
        )
        test_db.add(product)
    
    await test_db.commit()
    
    # Execute query without product IDs
    response = await client.post(
        "/api/v1/query",
        json={
            "query_text": "What are the pricing trends?",
            "analysis_type": "pricing"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Should still return valid report
    assert "query_id" in data
    assert "executive_summary" in data
    assert "pricing_analysis" in data


@pytest.mark.asyncio
async def test_execute_query_with_uuid_in_text(
    client: AsyncClient,
    test_db: AsyncSession
):
    """Test query execution with UUID in query text"""
    # Create test product
    product = Product(
        id=uuid4(),
        sku="UUID-TEST",
        normalized_sku="uuid-test",
        name="UUID Test Product",
        category="Test",
        price=Decimal("199.99"),
        currency="USD",
        marketplace="test_marketplace",
        inventory_level=75
    )
    
    test_db.add(product)
    await test_db.commit()
    
    # Execute query with UUID in text
    response = await client.post(
        "/api/v1/query",
        json={
            "query_text": f"Analyze pricing for product {product.id}",
            "analysis_type": "pricing"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Should extract UUID from text and analyze
    assert "pricing_analysis" in data
    assert data["pricing_analysis"] is not None


@pytest.mark.asyncio
async def test_execute_query_no_products_error(
    client: AsyncClient,
    test_db: AsyncSession
):
    """Test query execution with no products in database"""
    # Execute query with no products
    response = await client.post(
        "/api/v1/query",
        json={
            "query_text": "Analyze pricing",
            "analysis_type": "pricing"
        }
    )
    
    # Should return 400 error
    assert response.status_code == 400
    assert "No products found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_query_response_structure(
    client: AsyncClient,
    test_db: AsyncSession
):
    """Test that query response has correct structure"""
    # Create test product
    product = Product(
        id=uuid4(),
        sku="STRUCT-TEST",
        normalized_sku="struct-test",
        name="Structure Test Product",
        category="Test",
        price=Decimal("299.99"),
        currency="USD",
        marketplace="test_marketplace",
        inventory_level=25
    )
    
    test_db.add(product)
    await test_db.commit()
    
    # Execute query
    response = await client.post(
        "/api/v1/query",
        json={
            "query_text": "Analyze pricing",
            "product_ids": [str(product.id)],
            "analysis_type": "pricing"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify pricing analysis structure
    pricing = data["pricing_analysis"]
    assert "price_gaps" in pricing
    assert "price_changes" in pricing
    assert "promotions" in pricing
    assert "recommendations" in pricing
    
    # Verify recommendations have required fields
    if pricing["recommendations"]:
        rec = pricing["recommendations"][0]
        assert "product_id" in rec
        assert "current_price" in rec
        assert "suggested_price" in rec
        assert "reasoning" in rec
        assert "confidence_score" in rec
        assert "expected_impact" in rec


@pytest.mark.asyncio
async def test_query_key_metrics_calculation(
    client: AsyncClient,
    test_db: AsyncSession
):
    """Test that key metrics are calculated correctly"""
    # Create test products
    products = []
    for i in range(2):
        product = Product(
            id=uuid4(),
            sku=f"METRIC-{i:03d}",
            normalized_sku=f"metric-{i:03d}",
            name=f"Metric Test Product {i}",
            category="Test",
            price=Decimal(f"{150 + i * 50}.00"),
            currency="USD",
            marketplace="test_marketplace",
            inventory_level=50
        )
        products.append(product)
        test_db.add(product)
    
    await test_db.commit()
    
    # Execute query
    response = await client.post(
        "/api/v1/query",
        json={
            "query_text": "Analyze pricing for products",
            "product_ids": [str(p.id) for p in products],
            "analysis_type": "pricing"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify key metrics
    metrics = data["key_metrics"]
    assert metrics["price_gaps_identified"] >= 0
    assert metrics["recommendations_generated"] == len(products)
    
    # Should have average confidence if recommendations exist
    if metrics["recommendations_generated"] > 0:
        assert "average_recommendation_confidence" in metrics
        assert 0 <= metrics["average_recommendation_confidence"] <= 1


@pytest.mark.asyncio
async def test_query_executive_summary_content(
    client: AsyncClient,
    test_db: AsyncSession
):
    """Test that executive summary contains meaningful content"""
    # Create test product
    product = Product(
        id=uuid4(),
        sku="SUMMARY-TEST",
        normalized_sku="summary-test",
        name="Summary Test Product",
        category="Test",
        price=Decimal("399.99"),
        currency="USD",
        marketplace="test_marketplace",
        inventory_level=10
    )
    
    test_db.add(product)
    await test_db.commit()
    
    # Execute query
    response = await client.post(
        "/api/v1/query",
        json={
            "query_text": "What's the pricing situation?",
            "product_ids": [str(product.id)],
            "analysis_type": "pricing"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    summary = data["executive_summary"]
    
    # Summary should mention analysis completion
    assert "Analysis completed" in summary or "product" in summary.lower()
    
    # Summary should be reasonably long
    assert len(summary) > 20


@pytest.mark.asyncio
async def test_query_confidence_score_range(
    client: AsyncClient,
    test_db: AsyncSession
):
    """Test that confidence score is always in valid range"""
    # Create test products with varying characteristics
    for i in range(3):
        product = Product(
            id=uuid4(),
            sku=f"CONF-{i:03d}",
            normalized_sku=f"conf-{i:03d}",
            name=f"Confidence Test Product {i}",
            category="Test",
            price=Decimal(f"{100 + i * 100}.00"),
            currency="USD",
            marketplace="test_marketplace",
            inventory_level=50 - i * 10
        )
        test_db.add(product)
    
    await test_db.commit()
    
    # Execute query
    response = await client.post(
        "/api/v1/query",
        json={
            "query_text": "Analyze all products",
            "analysis_type": "pricing"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Confidence should always be between 0 and 1
    confidence = data["confidence_score"]
    assert 0 <= confidence <= 1
    assert isinstance(confidence, (int, float))
