"""Tests for Sentiment Analysis API"""
import pytest
from uuid import uuid4
from httpx import AsyncClient
from datetime import datetime

from src.main import app
from src.models.product import Product
from src.models.review import Review


@pytest.mark.asyncio
async def test_sentiment_analysis_endpoint(client: AsyncClient, test_db, test_tenant_id):
    """Test sentiment analysis API endpoint"""
    # Create a test product
    product = Product(
        id=uuid4(),
        tenant_id=test_tenant_id,
        sku="TEST-SENT-001",
        normalized_sku="TESTSENT001",
        name="Test Product for Sentiment",
        price=99.99,
        currency="USD",
        marketplace="test",
        inventory_level=100
    )
    test_db.add(product)
    
    # Create test reviews
    reviews = [
        Review(
            id=uuid4(),
            tenant_id=test_tenant_id,
            product_id=product.id,
            rating=5,
            text="This product is amazing! I love it so much. Great quality.",
            source="test"
        ),
        Review(
            id=uuid4(),
            tenant_id=test_tenant_id,
            product_id=product.id,
            rating=1,
            text="Terrible product. It broke after one day. Very disappointed.",
            source="test"
        ),
        Review(
            id=uuid4(),
            tenant_id=test_tenant_id,
            product_id=product.id,
            rating=3,
            text="It's okay. Would like to see better features.",
            source="test"
        ),
    ]
    
    for review in reviews:
        test_db.add(review)
    
    await test_db.commit()
    
    # Call sentiment analysis endpoint
    response = await client.post(
        "/api/v1/sentiment/analyze",
        json={
            "product_ids": [str(product.id)],
            "num_clusters": 2
        }
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    
    result = data[0]
    assert result["product_id"] == str(product.id)
    assert "aggregate_sentiment" in result
    assert "sentiment_distribution" in result
    assert "top_topics" in result
    assert "feature_requests" in result
    assert "complaint_patterns" in result
    assert "confidence_score" in result
    assert result["total_reviews"] == 3


@pytest.mark.asyncio
async def test_sentiment_analysis_no_reviews(client: AsyncClient, test_db, test_tenant_id):
    """Test sentiment analysis with no reviews"""
    # Create a product with no reviews
    product = Product(
        id=uuid4(),
        tenant_id=test_tenant_id,
        sku="TEST-NO-REV-001",
        normalized_sku="TESTNOREV001",
        name="Product Without Reviews",
        price=49.99,
        currency="USD",
        marketplace="test",
        inventory_level=50
    )
    test_db.add(product)
    await test_db.commit()
    
    # Call sentiment analysis endpoint
    response = await client.post(
        "/api/v1/sentiment/analyze",
        json={
            "product_ids": [str(product.id)]
        }
    )
    
    # Should return 404 for no reviews
    assert response.status_code == 404
    assert "No reviews found" in response.json()["detail"]
