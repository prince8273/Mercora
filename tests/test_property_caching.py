"""Property-based tests for caching layer"""
import pytest
import asyncio
from hypothesis import given, strategies as st, settings
from datetime import datetime, timedelta
from uuid import uuid4, UUID

from src.cache.cache_manager import CacheManager
from src.cache.cache_events import (
    EventPublisher,
    EventSubscriber,
    DataEvent,
    DataEventType,
    CacheDependency
)


class TestStaleCacheRefresh:
    """
    Property 66: Stale cache is refreshed before use
    Validates: Requirements 16.1, 16.2, 16.3
    """
    
    @pytest.mark.asyncio
    @given(
        cache_type=st.sampled_from(['pricing', 'sentiment', 'forecast']),
        age_hours=st.integers(min_value=1, max_value=48)
    )
    @settings(max_examples=10, deadline=None)
    async def test_stale_cache_returns_none(self, cache_type, age_hours):
        """Test that stale cache is not returned"""
        cache_manager = CacheManager(use_memory_fallback=True)
        tenant_id = uuid4()
        identifier = "test_product_123"
        
        # Mock cached data with old timestamp
        old_timestamp = datetime.utcnow() - timedelta(hours=age_hours)
        cached_data = {
            'data': {'value': 'test_data'},
            'cached_at': old_timestamp.isoformat(),
            'cache_type': cache_type,
            'tenant_id': str(tenant_id)
        }
        
        # Check if data should be stale
        threshold_hours = {
            'pricing': 1,
            'sentiment': 24,
            'forecast': 12
        }
        
        # Use >= for boundary case (age equals threshold means stale)
        is_stale = age_hours >= threshold_hours[cache_type]
        is_fresh = cache_manager._is_fresh(cache_type, cached_data)
        
        # Property: Stale cache must be detected
        assert is_fresh == (not is_stale)
        
        # Property: If stale, freshness check must return False
        if is_stale:
            assert not is_fresh


class TestCacheInvalidationLogging:
    """
    Property 67: Cache invalidation clears and logs
    Validates: Requirements 16.4
    """
    
    @pytest.mark.asyncio
    @given(
        event_type=st.sampled_from(list(DataEventType)),
        entity_id=st.text(min_size=1, max_size=50)
    )
    @settings(max_examples=10, deadline=None)
    async def test_invalidation_is_logged(self, event_type, entity_id):
        """Test that cache invalidations are logged"""
        cache_manager = CacheManager(use_memory_fallback=True)
        publisher = EventPublisher()
        subscriber = EventSubscriber(cache_manager, publisher)
        
        tenant_id = uuid4()
        
        # Create and publish event
        event = DataEvent(
            event_type=event_type,
            tenant_id=tenant_id,
            entity_id=entity_id
        )
        
        await publisher.publish(event)
        
        # Property: Event must be logged
        event_log = publisher.get_event_log()
        assert len(event_log) > 0
        assert event_log[-1]['event_type'] == event_type.value
        assert event_log[-1]['entity_id'] == entity_id
        
        # Property: Invalidation must be logged
        invalidation_log = subscriber.get_invalidation_log()
        if CacheDependency.get_affected_cache_types(event_type):
            assert len(invalidation_log) > 0


class TestDependentCacheInvalidation:
    """
    Property 68: Data updates invalidate dependent caches
    Validates: Requirements 16.5
    """
    
    @given(
        event_type=st.sampled_from(list(DataEventType))
    )
    @settings(max_examples=10, deadline=None)
    def test_dependencies_are_invalidated(self, event_type):
        """Test that dependent caches are identified for invalidation"""
        # Get affected cache types
        affected = CacheDependency.get_affected_cache_types(event_type)
        
        # Property: Dependencies must be defined for all event types
        assert affected is not None
        assert isinstance(affected, list)
        
        # Property: Product updates must affect all cache types
        if event_type in [DataEventType.PRODUCT_UPDATED, DataEventType.PRODUCT_DELETED]:
            assert 'pricing' in affected
            assert 'sentiment' in affected
            assert 'forecast' in affected
            assert 'query_result' in affected
        
        # Property: Price updates must affect pricing cache
        if event_type == DataEventType.PRICE_UPDATED:
            assert 'pricing' in affected
        
        # Property: Review updates must affect sentiment cache
        if event_type in [DataEventType.REVIEW_ADDED, DataEventType.REVIEW_UPDATED]:
            assert 'sentiment' in affected
        
        # Property: Sales updates must affect forecast cache
        if event_type == DataEventType.SALES_DATA_UPDATED:
            assert 'forecast' in affected


class TestLRUEviction:
    """
    Property 69: Cache eviction follows LRU policy
    Validates: Requirements 16.7
    """
    
    @given(
        max_memory_mb=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=10, deadline=None)
    def test_lru_configuration(self, max_memory_mb):
        """Test that LRU eviction is configured"""
        cache_manager = CacheManager(max_memory_mb=max_memory_mb, use_memory_fallback=True)
        
        # Property: Max memory must be configured
        assert cache_manager.max_memory_mb == max_memory_mb
        
        # Property: Eviction policy must be LRU
        assert cache_manager.eviction_policy == "allkeys-lru"
        
        # Property: Evictions must be tracked in metrics
        assert 'evictions' in cache_manager._metrics
    
    @pytest.mark.asyncio
    async def test_eviction_metrics_tracked(self):
        """Test that evictions are tracked in metrics"""
        cache_manager = CacheManager(max_memory_mb=1, use_memory_fallback=True)
        
        # Get initial metrics
        metrics = await cache_manager.get_metrics()
        
        # Property: Metrics must include eviction count
        assert 'evictions' in metrics
        
        # Property: Eviction count must be non-negative
        assert metrics['evictions'] >= 0


class TestTokenUsageMinimization:
    """
    Property 46: Token usage is minimized through caching
    Validates: Requirements 10.5, 19.4
    """
    
    @pytest.mark.asyncio
    @given(
        num_requests=st.integers(min_value=2, max_value=10)
    )
    @settings(max_examples=10, deadline=None)
    async def test_cache_reduces_redundant_calls(self, num_requests):
        """Test that caching reduces redundant LLM calls"""
        cache_manager = CacheManager(use_memory_fallback=True)
        tenant_id = uuid4()
        query_id = "test_query_123"
        
        # Simulate LLM result
        llm_result = {
            'response': 'test response',
            'tokens_used': 100
        }
        
        # First request - cache miss
        cached = await cache_manager.get('query_result', tenant_id, query_id)
        assert cached is None  # Cache miss
        
        # Store result
        await cache_manager.set('query_result', tenant_id, query_id, llm_result)
        
        # Subsequent requests - cache hits
        cache_hits = 0
        for _ in range(num_requests - 1):
            cached = await cache_manager.get('query_result', tenant_id, query_id, check_freshness=False)
            if cached is not None:
                cache_hits += 1
        
        # Property: Cache must reduce redundant calls
        # At least some requests should hit cache
        assert cache_hits > 0
        
        # Property: Cached data must match original
        final_cached = await cache_manager.get('query_result', tenant_id, query_id, check_freshness=False)
        if final_cached:
            assert final_cached == llm_result
    
    @pytest.mark.asyncio
    async def test_cache_hit_rate_improves_with_reuse(self):
        """Test that cache hit rate improves with repeated queries"""
        cache_manager = CacheManager(use_memory_fallback=True)
        tenant_id = uuid4()
        
        # Make multiple requests for same data
        for i in range(5):
            query_id = f"query_{i % 2}"  # Alternate between 2 queries
            
            # Try to get from cache
            cached = await cache_manager.get('query_result', tenant_id, query_id, check_freshness=False)
            
            # If miss, store data
            if cached is None:
                await cache_manager.set('query_result', tenant_id, query_id, {'data': f'result_{i}'})
        
        # Get metrics
        metrics = await cache_manager.get_metrics()
        
        # Property: Hit rate must be calculated
        assert 'hit_rate_percent' in metrics
        
        # Property: Hit rate must be between 0 and 100
        assert 0 <= metrics['hit_rate_percent'] <= 100
        
        # Property: With reuse, hit rate should be > 0
        if metrics['total_requests'] > 2:
            assert metrics['hit_rate_percent'] > 0


class TestCacheFreshnessThresholds:
    """Additional tests for cache freshness thresholds"""
    
    @given(
        cache_type=st.sampled_from(['pricing', 'sentiment', 'forecast', 'query_result'])
    )
    @settings(max_examples=10, deadline=None)
    def test_freshness_thresholds_defined(self, cache_type):
        """Test that freshness thresholds are defined for all cache types"""
        cache_manager = CacheManager(use_memory_fallback=True)
        
        # Property: All cache types must have freshness thresholds
        assert cache_type in cache_manager.FRESHNESS_THRESHOLDS
        
        # Property: Thresholds must be positive
        threshold = cache_manager.FRESHNESS_THRESHOLDS[cache_type]
        assert threshold > 0
        
        # Property: Thresholds must be reasonable (between 1 minute and 7 days)
        assert 60 <= threshold <= 604800


class TestEventDrivenInvalidation:
    """Additional tests for event-driven invalidation"""
    
    @pytest.mark.asyncio
    @given(
        num_events=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=10, deadline=None)
    async def test_multiple_events_handled(self, num_events):
        """Test that multiple events are handled correctly"""
        cache_manager = CacheManager(use_memory_fallback=True)
        publisher = EventPublisher()
        subscriber = EventSubscriber(cache_manager, publisher)
        
        tenant_id = uuid4()
        
        # Publish multiple events
        for i in range(num_events):
            event = DataEvent(
                event_type=DataEventType.PRODUCT_UPDATED,
                tenant_id=tenant_id,
                entity_id=f"product_{i}"
            )
            await publisher.publish(event)
        
        # Property: All events must be logged
        event_log = publisher.get_event_log()
        assert len(event_log) >= num_events
        
        # Property: All events must trigger invalidation
        invalidation_log = subscriber.get_invalidation_log()
        assert len(invalidation_log) >= num_events
