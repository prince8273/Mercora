"""Tests for Redis Cache Manager"""
import pytest
from uuid import uuid4
from datetime import datetime, timedelta
import asyncio

from src.cache.cache_manager import CacheManager


@pytest.fixture
async def cache_manager():
    """Create cache manager for testing"""
    # Use a test Redis database (db=15)
    manager = CacheManager(redis_url="redis://localhost:6379/15")
    
    try:
        await manager.connect()
        yield manager
    finally:
        # Clean up: flush test database
        if manager._redis:
            await manager._redis.flushdb()
            await manager.disconnect()


@pytest.fixture
def tenant_id():
    """Test tenant ID"""
    return uuid4()


@pytest.mark.asyncio
async def test_cache_manager_connection(cache_manager):
    """Test Redis connection"""
    assert cache_manager._redis is not None
    
    # Test health check
    is_healthy = await cache_manager.health_check()
    assert is_healthy is True


@pytest.mark.asyncio
async def test_cache_set_and_get(cache_manager, tenant_id):
    """Test basic cache set and get operations"""
    test_data = {
        'product_name': 'Test Product',
        'price': 99.99,
        'stock': 100
    }
    
    # Set cache
    success = await cache_manager.set(
        cache_type='pricing',
        tenant_id=tenant_id,
        identifier='product-123',
        data=test_data
    )
    assert success is True
    
    # Get cache
    cached_data = await cache_manager.get(
        cache_type='pricing',
        tenant_id=tenant_id,
        identifier='product-123',
        check_freshness=False
    )
    
    assert cached_data is not None
    assert cached_data['product_name'] == 'Test Product'
    assert cached_data['price'] == 99.99
    assert cached_data['stock'] == 100


@pytest.mark.asyncio
async def test_cache_miss(cache_manager, tenant_id):
    """Test cache miss scenario"""
    cached_data = await cache_manager.get(
        cache_type='pricing',
        tenant_id=tenant_id,
        identifier='nonexistent',
        check_freshness=False
    )
    
    assert cached_data is None


@pytest.mark.asyncio
async def test_cache_freshness_check(cache_manager, tenant_id):
    """Test cache freshness validation"""
    test_data = {'value': 'test'}
    
    # Set cache with very short TTL
    await cache_manager.set(
        cache_type='pricing',
        tenant_id=tenant_id,
        identifier='test-fresh',
        data=test_data,
        ttl=2  # 2 seconds
    )
    
    # Should be fresh immediately
    cached_data = await cache_manager.get(
        cache_type='pricing',
        tenant_id=tenant_id,
        identifier='test-fresh',
        check_freshness=True
    )
    assert cached_data is not None
    
    # Wait for TTL to expire
    await asyncio.sleep(3)
    
    # Should be None after expiry
    cached_data = await cache_manager.get(
        cache_type='pricing',
        tenant_id=tenant_id,
        identifier='test-fresh',
        check_freshness=True
    )
    assert cached_data is None


@pytest.mark.asyncio
async def test_cache_delete(cache_manager, tenant_id):
    """Test cache deletion"""
    test_data = {'value': 'test'}
    
    # Set cache
    await cache_manager.set(
        cache_type='pricing',
        tenant_id=tenant_id,
        identifier='test-delete',
        data=test_data
    )
    
    # Verify it exists
    cached_data = await cache_manager.get(
        cache_type='pricing',
        tenant_id=tenant_id,
        identifier='test-delete',
        check_freshness=False
    )
    assert cached_data is not None
    
    # Delete
    deleted = await cache_manager.delete(
        cache_type='pricing',
        tenant_id=tenant_id,
        identifier='test-delete'
    )
    assert deleted is True
    
    # Verify it's gone
    cached_data = await cache_manager.get(
        cache_type='pricing',
        tenant_id=tenant_id,
        identifier='test-delete',
        check_freshness=False
    )
    assert cached_data is None


@pytest.mark.asyncio
async def test_cache_pattern_invalidation(cache_manager, tenant_id):
    """Test pattern-based cache invalidation"""
    # Set multiple cache entries
    for i in range(5):
        await cache_manager.set(
            cache_type='pricing',
            tenant_id=tenant_id,
            identifier=f'product-{i}',
            data={'id': i}
        )
    
    # Invalidate all pricing entries for tenant
    invalidated = await cache_manager.invalidate_pattern(
        cache_type='pricing',
        tenant_id=tenant_id,
        pattern='*'
    )
    
    assert invalidated == 5
    
    # Verify all are gone
    for i in range(5):
        cached_data = await cache_manager.get(
            cache_type='pricing',
            tenant_id=tenant_id,
            identifier=f'product-{i}',
            check_freshness=False
        )
        assert cached_data is None


@pytest.mark.asyncio
async def test_tenant_isolation(cache_manager):
    """Test that cache entries are isolated by tenant"""
    tenant1 = uuid4()
    tenant2 = uuid4()
    
    # Set data for tenant1
    await cache_manager.set(
        cache_type='pricing',
        tenant_id=tenant1,
        identifier='product-1',
        data={'tenant': 'tenant1'}
    )
    
    # Set data for tenant2
    await cache_manager.set(
        cache_type='pricing',
        tenant_id=tenant2,
        identifier='product-1',
        data={'tenant': 'tenant2'}
    )
    
    # Verify tenant1 gets their data
    data1 = await cache_manager.get(
        cache_type='pricing',
        tenant_id=tenant1,
        identifier='product-1',
        check_freshness=False
    )
    assert data1['tenant'] == 'tenant1'
    
    # Verify tenant2 gets their data
    data2 = await cache_manager.get(
        cache_type='pricing',
        tenant_id=tenant2,
        identifier='product-1',
        check_freshness=False
    )
    assert data2['tenant'] == 'tenant2'


@pytest.mark.asyncio
async def test_cache_metrics(cache_manager, tenant_id):
    """Test cache metrics tracking"""
    # Perform some cache operations
    await cache_manager.set(
        cache_type='pricing',
        tenant_id=tenant_id,
        identifier='test-1',
        data={'value': 1}
    )
    
    # Hit
    await cache_manager.get(
        cache_type='pricing',
        tenant_id=tenant_id,
        identifier='test-1',
        check_freshness=False
    )
    
    # Miss
    await cache_manager.get(
        cache_type='pricing',
        tenant_id=tenant_id,
        identifier='nonexistent',
        check_freshness=False
    )
    
    # Get metrics
    metrics = await cache_manager.get_metrics()
    
    assert metrics['hits'] >= 1
    assert metrics['misses'] >= 1
    assert metrics['sets'] >= 1
    assert metrics['total_requests'] >= 2
    assert 'hit_rate_percent' in metrics


@pytest.mark.asyncio
async def test_clear_tenant_cache(cache_manager):
    """Test clearing all cache for a tenant"""
    tenant1 = uuid4()
    tenant2 = uuid4()
    
    # Set data for both tenants
    await cache_manager.set('pricing', tenant1, 'p1', {'data': 1})
    await cache_manager.set('sentiment', tenant1, 's1', {'data': 2})
    await cache_manager.set('pricing', tenant2, 'p2', {'data': 3})
    
    # Clear tenant1 cache
    cleared = await cache_manager.clear_tenant_cache(tenant1)
    assert cleared == 2
    
    # Verify tenant1 cache is cleared
    assert await cache_manager.get('pricing', tenant1, 'p1', False) is None
    assert await cache_manager.get('sentiment', tenant1, 's1', False) is None
    
    # Verify tenant2 cache is intact
    assert await cache_manager.get('pricing', tenant2, 'p2', False) is not None


@pytest.mark.asyncio
async def test_different_cache_types(cache_manager, tenant_id):
    """Test different cache types with different TTLs"""
    # Set pricing cache (1 hour TTL)
    await cache_manager.set(
        cache_type='pricing',
        tenant_id=tenant_id,
        identifier='test',
        data={'type': 'pricing'}
    )
    
    # Set sentiment cache (24 hour TTL)
    await cache_manager.set(
        cache_type='sentiment',
        tenant_id=tenant_id,
        identifier='test',
        data={'type': 'sentiment'}
    )
    
    # Set forecast cache (12 hour TTL)
    await cache_manager.set(
        cache_type='forecast',
        tenant_id=tenant_id,
        identifier='test',
        data={'type': 'forecast'}
    )
    
    # Verify all are retrievable
    pricing_data = await cache_manager.get('pricing', tenant_id, 'test', False)
    sentiment_data = await cache_manager.get('sentiment', tenant_id, 'test', False)
    forecast_data = await cache_manager.get('forecast', tenant_id, 'test', False)
    
    assert pricing_data['type'] == 'pricing'
    assert sentiment_data['type'] == 'sentiment'
    assert forecast_data['type'] == 'forecast'
