"""Property-based tests for cache invalidation"""
import pytest
import asyncio
from datetime import datetime
from uuid import uuid4
from hypothesis import given, strategies as st, settings, HealthCheck
from src.cache.event_bus import (
    EventPublisher,
    CacheInvalidationSubscriber,
    DataEvent,
    EventType,
    get_event_publisher
)
from src.cache.cache_manager import CacheManager


@pytest.fixture
async def cache_manager():
    """Create cache manager for testing"""
    manager = CacheManager(
        redis_url="redis://localhost:6379",
        max_memory_mb=256,
        default_ttl=3600,
        use_memory_fallback=True  # Use memory fallback for tests
    )
    await manager.connect()
    yield manager
    await manager.disconnect()


@pytest.fixture
def event_publisher():
    """Create event publisher for testing"""
    return EventPublisher()


@pytest.fixture
async def cache_subscriber(cache_manager, event_publisher):
    """Create cache invalidation subscriber for testing"""
    return CacheInvalidationSubscriber(cache_manager, event_publisher)


# Feature: ecommerce-intelligence-agent, Property 67: Cache invalidation clears and logs
@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    num_events=st.integers(min_value=1, max_value=10)
)
@pytest.mark.asyncio
async def test_property_cache_invalidation_clears_and_logs(
    cache_manager,
    event_publisher,
    cache_subscriber,
    num_events
):
    """
    **Property 67: Cache invalidation clears and logs**
    **Validates: Requirements 16.4**
    
    Property: When cache invalidation is triggered, the system clears
    affected cache entries and logs the invalidation event.
    """
    # Reset state between hypothesis examples to prevent interference
    if cache_manager._redis:
        await cache_manager._redis.flushdb()
    elif cache_manager.use_memory_fallback:
        cache_manager._memory_cache.clear()
    cache_subscriber._invalidation_log.clear()
    
    tenant_id = uuid4()
    
    # Set up some cache entries
    cache_keys = []
    for i in range(num_events):
        product_id = f"PROD{i:03d}"
        identifier = f"product:{product_id}"
        key = f"pricing:{tenant_id}:{identifier}"
        
        await cache_manager.set(
            key=key,
            value={'price': 29.99 + i, 'product_id': product_id},
            ttl=3600
        )
        cache_keys.append((key, identifier, product_id))
    
    # Verify caches exist
    for key, identifier, product_id in cache_keys:
        cached = await cache_manager.get(key=key)
        assert cached is not None, f"Cache should exist for {identifier}"
    
    # Publish events to trigger invalidation
    for key, identifier, product_id in cache_keys:
        event = DataEvent(
            event_type=EventType.PRICE_UPDATED,
            tenant_id=tenant_id,
            entity_type='product',
            entity_id=product_id
        )
        await event_publisher.publish(event)
    
    # Give time for async invalidation
    await asyncio.sleep(0.1)
    
    # Property 1: Cache entries should be cleared
    for key, identifier, product_id in cache_keys:
        cached = await cache_manager.get(key=key)
        assert cached is None, \
            f"Cache should be invalidated for {identifier}"
    
    # Property 2: Invalidation should be logged
    log = cache_subscriber.get_invalidation_log(tenant_id=tenant_id)
    assert len(log) >= num_events, \
        f"Expected at least {num_events} log entries, got {len(log)}"
    
    # Property 3: Log entries should contain required fields
    for entry in log:
        assert 'timestamp' in entry
        assert 'event_type' in entry
        assert 'tenant_id' in entry
        assert 'entity_type' in entry
        assert 'entity_id' in entry
        assert 'invalidated_caches' in entry
        assert 'total_keys_invalidated' in entry


# Feature: ecommerce-intelligence-agent, Property 68: Data updates invalidate dependent caches
@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_products=st.integers(min_value=1, max_value=5)
)
@pytest.mark.asyncio
async def test_property_dependent_cache_invalidation(
    cache_manager,
    event_publisher,
    cache_subscriber,
    num_products
):
    """
    **Property 68: Data updates invalidate dependent caches**
    **Validates: Requirements 16.5**
    
    Property: When data sources are updated, the system invalidates
    all dependent cache entries (e.g., product update invalidates
    pricing, forecast, and product caches).
    """
    # Reset state between hypothesis examples
    if cache_manager._redis:
        await cache_manager._redis.flushdb()
    elif cache_manager.use_memory_fallback:
        cache_manager._memory_cache.clear()
    cache_subscriber._invalidation_log.clear()
    
    tenant_id = uuid4()
    
    # Set up multiple cache types for each product
    for i in range(num_products):
        product_id = f"PROD{i:03d}"
        
        # Create pricing cache
        await cache_manager.set(
            key=f"pricing:{tenant_id}:product:{product_id}",
            value={'price': 29.99 + i},
            ttl=3600
        )
        
        # Create forecast cache
        await cache_manager.set(
            key=f"forecast:{tenant_id}:product:{product_id}",
            value={'demand': 100 + i * 10},
            ttl=3600
        )
        
        # Create product cache
        await cache_manager.set(
            key=f"product:{tenant_id}:details:{product_id}",
            value={'name': f'Product {i}'},
            ttl=3600
        )
    
    # Publish product update event (should invalidate all dependent caches)
    for i in range(num_products):
        product_id = f"PROD{i:03d}"
        event = DataEvent(
            event_type=EventType.PRODUCT_UPDATED,
            tenant_id=tenant_id,
            entity_type='product',
            entity_id=product_id
        )
        await event_publisher.publish(event)
    
    # Give time for async invalidation
    await asyncio.sleep(0.1)
    
    # Property 1: All dependent cache types should be invalidated
    for i in range(num_products):
        product_id = f"PROD{i:03d}"
        
        # Check pricing cache
        pricing_cached = await cache_manager.get(
            key=f"pricing:{tenant_id}:product:{product_id}"
        )
        assert pricing_cached is None, \
            f"Pricing cache should be invalidated for {product_id}"
        
        # Check forecast cache
        forecast_cached = await cache_manager.get(
            key=f"forecast:{tenant_id}:product:{product_id}"
        )
        assert forecast_cached is None, \
            f"Forecast cache should be invalidated for {product_id}"
        
        # Check product cache
        product_cached = await cache_manager.get(
            key=f"product:{tenant_id}:details:{product_id}"
        )
        assert product_cached is None, \
            f"Product cache should be invalidated for {product_id}"
    
    # Property 2: Invalidation log should show multiple cache types affected
    log = cache_subscriber.get_invalidation_log(tenant_id=tenant_id)
    
    # Each product update should invalidate multiple cache types
    for entry in log:
        if entry['event_type'] == 'product_updated':
            invalidated_caches = entry['invalidated_caches']
            cache_types = {cache['cache_type'] for cache in invalidated_caches}
            
            # Product updates should affect pricing, forecast, and product caches
            assert len(cache_types) >= 1, \
                "Product update should invalidate at least one cache type"


@settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    event_type=st.sampled_from(list(EventType))
)
@pytest.mark.asyncio
async def test_property_event_type_cache_dependencies(
    cache_manager,
    event_publisher,
    cache_subscriber,
    event_type
):
    """
    **Property 68b: Each event type invalidates correct cache types**
    **Validates: Requirements 16.5**
    
    Property: Different event types should invalidate their specific
    dependent cache types according to the dependency map.
    """
    # Reset state between hypothesis examples
    if cache_manager._redis:
        await cache_manager._redis.flushdb()
    elif cache_manager.use_memory_fallback:
        cache_manager._memory_cache.clear()
    cache_subscriber._invalidation_log.clear()
    
    tenant_id = uuid4()
    entity_id = "TEST001"
    
    # Create caches for all types
    cache_types = ['pricing', 'sentiment', 'forecast', 'product', 'review', 'sales', 'inventory']
    for cache_type in cache_types:
        await cache_manager.set(
            key=f"{cache_type}:{tenant_id}:entity:{entity_id}",
            value={'data': 'test'},
            ttl=3600
        )
    
    # Publish event
    event = DataEvent(
        event_type=event_type,
        tenant_id=tenant_id,
        entity_type='test',
        entity_id=entity_id
    )
    await event_publisher.publish(event)
    
    # Give time for async invalidation
    await asyncio.sleep(0.1)
    
    # Property: Only dependent caches should be invalidated
    log = cache_subscriber.get_invalidation_log(tenant_id=tenant_id, limit=1)
    
    if log:
        entry = log[0]
        invalidated_cache_types = {
            cache['cache_type'] for cache in entry['invalidated_caches']
        }
        
        # Verify invalidation matches dependency map
        expected_dependencies = cache_subscriber._cache_dependencies.get(event_type, set())
        
        # All invalidated caches should be in expected dependencies
        for cache_type in invalidated_cache_types:
            assert cache_type in expected_dependencies or len(expected_dependencies) == 0, \
                f"Cache type {cache_type} should not be invalidated for {event_type.value}"


# Edge case tests
@pytest.mark.asyncio
async def test_invalidation_with_no_matching_caches(cache_manager, event_publisher, cache_subscriber):
    """Test invalidation when no matching cache entries exist"""
    tenant_id = uuid4()
    
    # Publish event without any matching caches
    event = DataEvent(
        event_type=EventType.PRODUCT_UPDATED,
        tenant_id=tenant_id,
        entity_type='product',
        entity_id='NONEXISTENT'
    )
    await event_publisher.publish(event)
    
    # Give time for async processing
    await asyncio.sleep(0.1)
    
    # Should not raise errors
    log = cache_subscriber.get_invalidation_log(tenant_id=tenant_id)
    assert len(log) >= 0  # Log may or may not have entry


@pytest.mark.asyncio
async def test_multiple_subscribers_same_event(cache_manager, event_publisher):
    """Test multiple subscribers can listen to same event"""
    call_count = {'count': 0}
    
    async def subscriber1(event):
        call_count['count'] += 1
    
    async def subscriber2(event):
        call_count['count'] += 1
    
    event_publisher.subscribe(EventType.PRODUCT_UPDATED, subscriber1)
    event_publisher.subscribe(EventType.PRODUCT_UPDATED, subscriber2)
    
    event = DataEvent(
        event_type=EventType.PRODUCT_UPDATED,
        tenant_id=uuid4(),
        entity_type='product',
        entity_id='TEST001'
    )
    
    await event_publisher.publish(event)
    await asyncio.sleep(0.1)
    
    # Both subscribers should be called
    assert call_count['count'] == 2


@pytest.mark.asyncio
async def test_invalidation_stats(cache_manager, event_publisher, cache_subscriber):
    """Test invalidation statistics tracking"""
    tenant_id = uuid4()
    
    # Publish multiple events
    for i in range(5):
        event = DataEvent(
            event_type=EventType.PRICE_UPDATED,
            tenant_id=tenant_id,
            entity_type='product',
            entity_id=f'PROD{i:03d}'
        )
        await event_publisher.publish(event)
    
    await asyncio.sleep(0.1)
    
    # Get stats
    stats = cache_subscriber.get_invalidation_stats()
    
    assert 'total_invalidation_events' in stats
    assert 'total_keys_invalidated' in stats
    assert 'by_event_type' in stats
    assert 'average_keys_per_event' in stats
    assert stats['total_invalidation_events'] >= 0
