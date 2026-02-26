"""Integration tests for Pricing API endpoints"""
import pytest
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.main import app
from src.models.product import Product
from src.database import get_db


@pytest.mark.asyncio
async def test_pricing_analysis_endpoint(client: AsyncClient, test_db: AsyncSession):
    """Test the pricing analysis endpoint"""
    # Create test products
    product1 = Product(
        sku="TEST-API-001",
        normalized_sku="TESTAPI001",
        name="API Test Product 1",
        category="Electronics",
        price=Decimal("99.99"),
        currency="USD",
        marketplace="our_store",
        inventory_level=50
    )
    
    product2 = Product(
        sku="TEST-API-002",
        normalized_sku="TESTAPI002",
        name="API Test Product 2",
        category="Electronics",
        price=Decimal("149.99"),
        currency="USD",
        marketplace="our_store",
        inventory_level=30
    )
    
    test_db.add(product1)
    test_db.add(product2)
    await test_db.commit()
    await test_db.refresh(product1)
    await test_db.refresh(product2)
    
    # Make API request
    response = await client.post(
        "/api/v1/pricing/analysis",
        json={
            "product_ids": [str(product1.id), str(product2.id)],
            "include_recommendations": True,
            "margin_constraints": {
                "min_margin_percentage": 20.0,
                "max_discount_percentage": 30.0
            }
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert "price_gaps" in data
    assert "price_changes" in data
    assert "promotions" in data
    assert "recommendations" in data
    
    # Verify we got recommendations for both products
    assert len(data["recommendations"]) == 2
    
    # Verify recommendation structure
    for rec in data["recommendations"]:
        assert "product_id" in rec
        assert "current_price" in rec
        assert "suggested_price" in rec
        assert "reasoning" in rec
        assert "confidence_score" in rec
        assert "expected_impact" in rec
        assert 0 <= rec["confidence_score"] <= 1


@pytest.mark.asyncio
async def test_pricing_analysis_without_recommendations(client: AsyncClient, test_db: AsyncSession):
    """Test pricing analysis without recommendations"""
    # Create test product
    product = Product(
        sku="TEST-API-003",
        normalized_sku="TESTAPI003",
        name="API Test Product 3",
        category="Electronics",
        price=Decimal("79.99"),
        currency="USD",
        marketplace="our_store",
        inventory_level=100
    )
    
    test_db.add(product)
    await test_db.commit()
    await test_db.refresh(product)
    
    # Make API request without recommendations
    response = await client.post(
        "/api/v1/pricing/analysis",
        json={
            "product_ids": [str(product.id)],
            "include_recommendations": False
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Should have empty recommendations
    assert len(data["recommendations"]) == 0
    
    # But should still have other analysis
    assert "price_gaps" in data
    assert "price_changes" in data
    assert "promotions" in data


@pytest.mark.asyncio
async def test_pricing_analysis_invalid_product_id(client: AsyncClient, test_db: AsyncSession):
    """Test pricing analysis with invalid product ID"""
    response = await client.post(
        "/api/v1/pricing/analysis",
        json={
            "product_ids": ["00000000-0000-0000-0000-000000000000"],
            "include_recommendations": True
        }
    )
    
    assert response.status_code == 404
    assert "no products found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_pricing_analysis_with_custom_constraints(client: AsyncClient, test_db: AsyncSession):
    """Test pricing analysis with custom margin constraints"""
    # Create test product
    product = Product(
        sku="TEST-API-004",
        normalized_sku="TESTAPI004",
        name="API Test Product 4",
        category="Electronics",
        price=Decimal("199.99"),
        currency="USD",
        marketplace="our_store",
        inventory_level=25
    )
    
    test_db.add(product)
    await test_db.commit()
    await test_db.refresh(product)
    
    # Make API request with strict constraints
    response = await client.post(
        "/api/v1/pricing/analysis",
        json={
            "product_ids": [str(product.id)],
            "include_recommendations": True,
            "margin_constraints": {
                "min_margin_percentage": 30.0,
                "max_discount_percentage": 10.0
            }
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify recommendation respects constraints
    if data["recommendations"]:
        rec = data["recommendations"][0]
        suggested_price = Decimal(str(rec["suggested_price"]))
        current_price = Decimal(str(rec["current_price"]))
        
        # Should not discount more than 10%
        min_allowed = current_price * Decimal("0.90")
        assert suggested_price >= min_allowed
