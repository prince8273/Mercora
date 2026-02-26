"""Tests for Multi-Agent Query Coordination"""
import pytest
from uuid import uuid4
from httpx import AsyncClient

from src.models.product import Product
from src.models.review import Review


@pytest.mark.asyncio
async def test_query_with_all_agents(client: AsyncClient, test_db):
    """Test query endpoint with both pricing and sentiment analysis"""
    # Create test products
    product1 = Product(
        id=uuid4(),
        sku="MULTI-001",
        normalized_sku="MULTI001",
        name="Multi-Agent Test Product",
        price=149.99,
        currency="USD",
        marketplace="test",
        inventory_level=75
    )
    test_db.add(product1)
    
    # Create reviews for sentiment analysis
    reviews = [
        Review(
            id=uuid4(),
            product_id=product1.id,
            rating=5,
            text="Excellent product! Highly recommend. Great value for money.",
            source="test"
        ),
        Review(
            id=uuid4(),
            product_id=product1.id,
            rating=4,
            text="Good quality but I wish it had more features.",
            source="test"
        ),
        Review(
            id=uuid4(),
            product_id=product1.id,
            rating=2,
            text="Poor quality. The product has issues with durability.",
            source="test"
        ),
    ]
    
    for review in reviews:
        test_db.add(review)
    
    await test_db.commit()
    
    # Execute query with analysis_type="all"
    response = await client.post(
        "/api/v1/query",
        json={
            "query_text": "Analyze pricing and customer sentiment for my products",
            "product_ids": [str(product1.id)],
            "analysis_type": "all"
        }
    )
    
    assert response.status_code == 200
    
    data = response.json()
    
    # Check report structure
    assert "query_id" in data
    assert "executive_summary" in data
    assert "key_metrics" in data
    assert "pricing_analysis" in data
    assert "sentiment_analysis" in data
    assert "confidence_score" in data
    
    # Check that both analyses are present
    assert data["pricing_analysis"] is not None
    assert data["sentiment_analysis"] is not None
    
    # Check sentiment analysis results
    sentiment_results = data["sentiment_analysis"]
    assert isinstance(sentiment_results, list)
    assert len(sentiment_results) == 1
    assert sentiment_results[0]["product_id"] == str(product1.id)
    assert sentiment_results[0]["total_reviews"] == 3
    
    # Check key metrics include both pricing and sentiment
    metrics = data["key_metrics"]
    assert "total_reviews_analyzed" in metrics
    assert "average_sentiment_score" in metrics
    assert "positive_reviews" in metrics
    assert "negative_reviews" in metrics
    
    # Check executive summary mentions both analyses
    summary = data["executive_summary"]
    assert "review" in summary.lower() or "sentiment" in summary.lower()


@pytest.mark.asyncio
async def test_query_pricing_only(client: AsyncClient, test_db):
    """Test query endpoint with pricing analysis only"""
    product = Product(
        id=uuid4(),
        sku="PRICE-ONLY-001",
        normalized_sku="PRICEONLY001",
        name="Pricing Only Product",
        price=99.99,
        currency="USD",
        marketplace="test",
        inventory_level=50
    )
    test_db.add(product)
    await test_db.commit()
    
    response = await client.post(
        "/api/v1/query",
        json={
            "query_text": "What's the competitive pricing for this product?",
            "product_ids": [str(product.id)],
            "analysis_type": "pricing"
        }
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["pricing_analysis"] is not None
    assert data["sentiment_analysis"] is None


@pytest.mark.asyncio
async def test_query_sentiment_only(client: AsyncClient, test_db):
    """Test query endpoint with sentiment analysis only"""
    product = Product(
        id=uuid4(),
        sku="SENT-ONLY-001",
        normalized_sku="SENTONLY001",
        name="Sentiment Only Product",
        price=79.99,
        currency="USD",
        marketplace="test",
        inventory_level=30
    )
    test_db.add(product)
    
    # Add reviews
    review = Review(
        id=uuid4(),
        product_id=product.id,
        rating=5,
        text="Amazing product! Love it!",
        source="test"
    )
    test_db.add(review)
    await test_db.commit()
    
    response = await client.post(
        "/api/v1/query",
        json={
            "query_text": "What do customers think about this product?",
            "product_ids": [str(product.id)],
            "analysis_type": "sentiment"
        }
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["pricing_analysis"] is None
    assert data["sentiment_analysis"] is not None
