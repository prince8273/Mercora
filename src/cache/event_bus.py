"""Event-driven cache invalidation system"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Callable, Any, Optional, Set
from enum import Enum
from uuid import UUID
from dataclasses import dataclass, field


logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of data update events"""
    PRODUCT_UPDATED = "product_updated"
    PRODUCT_CREATED = "product_created"
    PRODUCT_DELETED = "product_deleted"
    PRICE_UPDATED = "price_updated"
    REVIEW_CREATED = "review_created"
    REVIEW_UPDATED = "review_updated"
    SALES_RECORDED = "sales_recorded"
    INVENTORY_UPDATED = "inventory_updated"
    FORECAST_GENERATED = "forecast_generated"


@dataclass
class DataEvent:
    """Data update event"""
    event_type: EventType
    tenant_id: UUID
    entity_type: str  # 'product', 'review', 'sales', etc.
    entity_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        return f"{self.event_type.value}:{self.entity_type}:{self.entity_id}"


class EventPublisher:
    """
    Publishes data update events for cache invalidation.
    
    Responsibilities:
    - Emit events when data is created/updated/deleted
    - Track event history for debugging
    - Support multiple subscribers per event type
    """
    
    def __init__(self):
        """Initialize event publisher"""
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._event_history: List[DataEvent] = []
        self._max_history = 1000
        logger.info("EventPublisher initialized")
    
    def subscribe(self, event_type: EventType, callback: Callable):
        """
        Subscribe to an event type.
        
        Args:
            event_type: Type of event to subscribe to
            callback: Async function to call when event occurs
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        self._subscribers[event_type].append(callback)
        logger.info(f"Subscribed to {event_type.value}")
    
    async def publish(self, event: DataEvent):
        """
        Publish an event to all subscribers.
        
        Args:
            event: Data event to publish
        """
        logger.info(f"Publishing event: {event}")
        
        # Add to history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
        
        # Notify subscribers
        subscribers = self._subscribers.get(event.event_type, [])
        
        if not subscribers:
            logger.debug(f"No subscribers for {event.event_type.value}")
            return
        
        # Call all subscribers concurrently
        tasks = [callback(event) for callback in subscribers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log any errors
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    f"Subscriber {i} failed for {event.event_type.value}: {result}"
                )
    
    def get_event_history(
        self,
        event_type: Optional[EventType] = None,
        limit: int = 100
    ) -> List[DataEvent]:
        """
        Get recent event history.
        
        Args:
            event_type: Filter by event type (optional)
            limit: Maximum number of events to return
            
        Returns:
            List of recent events
        """
        events = self._event_history
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        return events[-limit:]


class CacheInvalidationSubscriber:
    """
    Subscribes to data events and invalidates affected caches.
    
    Responsibilities:
    - Listen for data update events
    - Determine which caches are affected
    - Invalidate dependent caches
    - Log invalidation events
    """
    
    def __init__(self, cache_manager, event_publisher: EventPublisher):
        """
        Initialize cache invalidation subscriber.
        
        Args:
            cache_manager: CacheManager instance
            event_publisher: EventPublisher to subscribe to
        """
        self.cache_manager = cache_manager
        self.event_publisher = event_publisher
        self._invalidation_log: List[Dict[str, Any]] = []
        self._max_log_size = 1000
        
        # Define cache dependencies
        self._cache_dependencies = self._build_dependency_map()
        
        # Subscribe to relevant events
        self._subscribe_to_events()
        
        logger.info("CacheInvalidationSubscriber initialized")
    
    def _build_dependency_map(self) -> Dict[EventType, Set[str]]:
        """
        Build map of event types to affected cache types.
        
        Returns:
            Dictionary mapping event types to cache types
        """
        return {
            # Product updates affect pricing and forecast caches
            EventType.PRODUCT_UPDATED: {'pricing', 'forecast', 'product'},
            EventType.PRODUCT_CREATED: {'pricing', 'forecast', 'product'},
            EventType.PRODUCT_DELETED: {'pricing', 'forecast', 'product'},
            
            # Price updates affect pricing caches
            EventType.PRICE_UPDATED: {'pricing'},
            
            # Review updates affect sentiment caches
            EventType.REVIEW_CREATED: {'sentiment', 'review'},
            EventType.REVIEW_UPDATED: {'sentiment', 'review'},
            
            # Sales updates affect forecast caches
            EventType.SALES_RECORDED: {'forecast', 'sales'},
            
            # Inventory updates affect forecast caches
            EventType.INVENTORY_UPDATED: {'forecast', 'inventory'},
            
            # Forecast generation affects forecast caches
            EventType.FORECAST_GENERATED: {'forecast'},
        }
    
    def _subscribe_to_events(self):
        """Subscribe to all relevant event types"""
        for event_type in EventType:
            self.event_publisher.subscribe(event_type, self.handle_event)
    
    async def handle_event(self, event: DataEvent):
        """
        Handle a data update event by invalidating affected caches.
        
        Args:
            event: Data event to handle
        """
        logger.info(f"Handling event for cache invalidation: {event}")
        
        # Get affected cache types
        affected_caches = self._cache_dependencies.get(event.event_type, set())
        
        if not affected_caches:
            logger.debug(f"No cache dependencies for {event.event_type.value}")
            return
        
        # Invalidate each affected cache type
        invalidated_keys = []
        
        for cache_type in affected_caches:
            try:
                # Build cache key pattern
                pattern = self._build_invalidation_pattern(
                    cache_type, event.tenant_id, event.entity_id
                )
                
                # Invalidate matching keys
                count = await self.cache_manager.invalidate_pattern(pattern)
                
                if count > 0:
                    invalidated_keys.append({
                        'cache_type': cache_type,
                        'pattern': pattern,
                        'count': count
                    })
                    
                    logger.info(
                        f"Invalidated {count} {cache_type} cache entries "
                        f"for {event.entity_type}:{event.entity_id}"
                    )
            
            except Exception as e:
                logger.error(
                    f"Failed to invalidate {cache_type} cache for {event}: {e}"
                )
        
        # Log invalidation event
        self._log_invalidation(event, invalidated_keys)
    
    def _build_invalidation_pattern(
        self,
        cache_type: str,
        tenant_id: UUID,
        entity_id: str
    ) -> str:
        """
        Build Redis key pattern for invalidation.
        
        Args:
            cache_type: Type of cache (pricing, sentiment, forecast)
            tenant_id: Tenant UUID
            entity_id: Entity identifier
            
        Returns:
            Redis key pattern matching format: cache_type:tenant_id:*entity_id*
        """
        # Pattern matches all cache entries for this entity
        # Format: cache_type:tenant_id:*entity_id*
        return f"{cache_type}:{tenant_id}:*{entity_id}*"
    
    def _log_invalidation(
        self,
        event: DataEvent,
        invalidated_keys: List[Dict[str, Any]]
    ):
        """
        Log cache invalidation event.
        
        Args:
            event: Data event that triggered invalidation
            invalidated_keys: List of invalidated cache entries
        """
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event.event_type.value,
            'tenant_id': str(event.tenant_id),
            'entity_type': event.entity_type,
            'entity_id': event.entity_id,
            'invalidated_caches': invalidated_keys,
            'total_keys_invalidated': sum(k['count'] for k in invalidated_keys)
        }
        
        self._invalidation_log.append(log_entry)
        
        # Trim log if too large
        if len(self._invalidation_log) > self._max_log_size:
            self._invalidation_log.pop(0)
        
        logger.info(
            f"Cache invalidation logged: {log_entry['total_keys_invalidated']} "
            f"keys invalidated for {event}"
        )
    
    def get_invalidation_log(
        self,
        tenant_id: Optional[UUID] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get recent cache invalidation log.
        
        Args:
            tenant_id: Filter by tenant (optional)
            limit: Maximum number of entries to return
            
        Returns:
            List of invalidation log entries
        """
        log = self._invalidation_log
        
        if tenant_id:
            log = [
                entry for entry in log
                if entry['tenant_id'] == str(tenant_id)
            ]
        
        return log[-limit:]
    
    def get_invalidation_stats(self) -> Dict[str, Any]:
        """
        Get cache invalidation statistics.
        
        Returns:
            Dictionary with invalidation stats
        """
        total_events = len(self._invalidation_log)
        total_keys = sum(
            entry['total_keys_invalidated']
            for entry in self._invalidation_log
        )
        
        # Count by event type
        by_event_type = {}
        for entry in self._invalidation_log:
            event_type = entry['event_type']
            by_event_type[event_type] = by_event_type.get(event_type, 0) + 1
        
        return {
            'total_invalidation_events': total_events,
            'total_keys_invalidated': total_keys,
            'by_event_type': by_event_type,
            'average_keys_per_event': total_keys / total_events if total_events > 0 else 0
        }


# Global instances
_event_publisher: Optional[EventPublisher] = None
_cache_subscriber: Optional[CacheInvalidationSubscriber] = None


def get_event_publisher() -> EventPublisher:
    """Get or create global event publisher"""
    global _event_publisher
    if _event_publisher is None:
        _event_publisher = EventPublisher()
    return _event_publisher


def initialize_cache_invalidation(cache_manager):
    """
    Initialize cache invalidation system.
    
    Args:
        cache_manager: CacheManager instance
    """
    global _cache_subscriber
    
    if _cache_subscriber is None:
        publisher = get_event_publisher()
        _cache_subscriber = CacheInvalidationSubscriber(cache_manager, publisher)
        logger.info("Cache invalidation system initialized")


def get_cache_subscriber() -> Optional[CacheInvalidationSubscriber]:
    """Get global cache invalidation subscriber"""
    return _cache_subscriber
