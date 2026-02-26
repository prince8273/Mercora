"""Tests for Query Cache Service"""
import pytest
from uuid import uuid4

from src.cache.cache_manager import CacheManager
from src.cache.query_cache_service import QueryCacheService


@pytest.fixture
async def cache_manager():
    """Create cache manager for testing"""
    manager = CacheManager(redis_url="redis://localhost:6379/15")
    
    try:
        await manager.connect()
        yield manager
    finally:
        if manager._redis:
            await manager._redis.flushdb()
            await manager.disconnect()


@pytest.fixture
def cache_service(cache_manager):
    """Create query cache service"""
    return QueryCacheService(cache_manager)


@pytest.fixture
def tenant_id():
    """Test tenant ID"""
    return uuid4()


@pytest.mark.asyncio
async def test_query_hash_generation(cache_service):
    """Test query hash generation is deterministic"""
    query1 = "What are my top selling products?"
    query2 = "what are my top selling products?"  # Different case
    
    hash1 = cache_service._generate_query_hash(query1)
    hash2 = cache_service._generate_query_hash(query2)
    
    # Should be same (case-insensitive)
    assert hash1 == hash2
    
    # Different query should have different hash
    query3 = "What are my worst selling products?"
    hash3 = cache_service._generate_query_hash(query3)
    assert hash1 != hash3


@pytest.mark.asyncio
async def test_query_hash_with_params(cache_service):
    """Test query hash includes parameters"""
    query = "Get product details"
    params1 = {'product_id': '123', 'include_reviews': True}
    params2 = {'product_id': '456', 'include_reviews': True}
    
    hash1 = cache_service._generate_query_hash(query, params1)
    hash2 = cache_service._generate_query_hash(query, params2)
    
    # Different params should produce different hashes
    assert hash1 != hash2


@pytest.mark.asyncio
async def test_cache_query_result(cache_service, tenant_id):
    """Test caching and retrieving query results"""
    query = "Show me pricing analysis"
    result = {
        'analysis': 'Pricing is competitive',
        'recommendations': ['Lower price by 5%'],
        'confidence': 0.85
    }
    
    # Cache the result
    success = await cache_service.set_query_result(
        tenant_id=tenant_id,
        query=query,
        result=result
    )
    assert success is True
    
    # Retrieve the result
    cached_result = await cache_service.get_query_result(
        tenant_id=tenant_id,
        query=query
    )
    
    assert cached_result is not None
    assert cached_result['analysis'] == 'Pricing is competitive'
    assert cached_result['confidence'] == 0.85


@pytest.mark.asyncio
async def test_cache_pricing_analysis(cache_service, tenant_id):
    """Test caching pricing analysis"""
    product_id = uuid4()
    analysis = {
        'price_gap': -5.0,
        'competitor_prices': [99.99, 104.99],
        'recommendation': 'Increase price'
    }
    
    # Cache pricing analysis
    success = await cache_service.set_pricing_analysis(
        tenant_id=tenant_id,
        product_id=product_id,
        analysis=analysis
    )
    assert success is True
    
    # Retrieve pricing analysis
    cached_analysis = await cache_service.get_pricing_analysis(
        tenant_id=tenant_id,
        product_id=product_id
    )
    
    assert cached_analysis is not None
    assert cached_analysis['price_gap'] == -5.0
    assert cached_analysis['recommendation'] == 'Increase price'


@pytest.mark.asyncio
async def test_cache_sentiment_analysis(cache_service, tenant_id):
    """Test caching sentiment analysis"""
    product_id = uuid4()
    analysis = {
        'overall_sentiment': 'positive',
        'sentiment_score': 0.75,
        'topics': ['quality', 'price', 'shipping']
    }
    
    # Cache sentiment analysis
    success = await cache_service.set_sentiment_analysis(
        tenant_id=tenant_id,
        product_id=product_id,
        analysis=analysis
    )
    assert success is True
    
    # Retrieve sentiment analysis
    cached_analysis = await cache_service.get_sentiment_analysis(
        tenant_id=tenant_id,
        product_id=product_id
    )
    
    assert cached_analysis is not None
    assert cached_analysis['overall_sentiment'] == 'positive'
    assert cached_analysis['sentiment_score'] == 0.75


@pytest.mark.asyncio
async def test_cache_demand_forecast(cache_service, tenant_id):
    """Test caching demand forecasts"""
    product_id = uuid4()
    forecast = {
        'forecast_points': [
            {'date': '2024-01-01', 'quantity': 100},
            {'date': '2024-01-02', 'quantity': 105}
        ],
        'confidence': 0.82
    }
    
    # Cache forecast
    success = await cache_service.set_demand_forecast(
        tenant_id=tenant_id,
        product_id=product_id,
        forecast=forecast,
        horizon_days=30
    )
    assert success is True
    
    # Retrieve forecast
    cached_forecast = await cache_service.get_demand_forecast(
        tenant_id=tenant_id,
        product_id=product_id,
        horizon_days=30
    )
    
    assert cached_forecast is not None
    assert len(cached_forecast['forecast_points']) == 2
    assert cached_forecast['confidence'] == 0.82


@pytest.mark.asyncio
async def test_forecast_cache_with_different_horizons(cache_service, tenant_id):
    """Test that forecasts with different horizons are cached separately"""
    product_id = uuid4()
    
    forecast_7d = {'horizon': 7, 'data': 'forecast for 7 days'}
    forecast_30d = {'horizon': 30, 'data': 'forecast for 30 days'}
    
    # Cache both forecasts
    await cache_service.set_demand_forecast(
        tenant_id=tenant_id,
        product_id=product_id,
        forecast=forecast_7d,
        horizon_days=7
    )
    
    await cache_service.set_demand_forecast(
        tenant_id=tenant_id,
        product_id=product_id,
        forecast=forecast_30d,
        horizon_days=30
    )
    
    # Retrieve both
    cached_7d = await cache_service.get_demand_forecast(
        tenant_id=tenant_id,
        product_id=product_id,
        horizon_days=7
    )
    
    cached_30d = await cache_service.get_demand_forecast(
        tenant_id=tenant_id,
        product_id=product_id,
        horizon_days=30
    )
    
    # Verify they're different
    assert cached_7d['horizon'] == 7
    assert cached_30d['horizon'] == 30


@pytest.mark.asyncio
async def test_invalidate_product_cache(cache_service, tenant_id):
    """Test invalidating all cache for a product"""
    product_id = uuid4()
    
    # Cache pricing, sentiment, and forecast
    await cache_service.set_pricing_analysis(
        tenant_id=tenant_id,
        product_id=product_id,
        analysis={'price': 99.99}
    )
    
    await cache_service.set_sentiment_analysis(
        tenant_id=tenant_id,
        product_id=product_id,
        analysis={'sentiment': 'positive'}
    )
    
    await cache_service.set_demand_forecast(
        tenant_id=tenant_id,
        product_id=product_id,
        forecast={'forecast': 'data'},
        horizon_days=30
    )
    
    # Invalidate all product cache
    invalidated = await cache_service.invalidate_product_cache(
        tenant_id=tenant_id,
        product_id=product_id
    )
    
    assert invalidated >= 3
    
    # Verify all are gone
    assert await cache_service.get_pricing_analysis(tenant_id, product_id) is None
    assert await cache_service.get_sentiment_analysis(tenant_id, product_id) is None
    assert await cache_service.get_demand_forecast(tenant_id, product_id, 30) is None


@pytest.mark.asyncio
async def test_invalidate_query_cache(cache_service, tenant_id):
    """Test invalidating all query result caches"""
    # Cache multiple query results
    queries = [
        "What are my top products?",
        "Show pricing analysis",
        "Sentiment overview"
    ]
    
    for query in queries:
        await cache_service.set_query_result(
            tenant_id=tenant_id,
            query=query,
            result={'data': query}
        )
    
    # Invalidate all query caches
    invalidated = await cache_service.invalidate_query_cache(tenant_id)
    
    assert invalidated >= 3
    
    # Verify all are gone
    for query in queries:
        cached = await cache_service.get_query_result(tenant_id, query)
        assert cached is None
