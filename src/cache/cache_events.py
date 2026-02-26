"""
Cache Event System - Event-driven cache invalidation

This module provides event publishing and subscription for cache invalidation
when data is updated.
"""
import logging
from typing import Dict, Any, List, Callable, Optional, Set
from datetime import datetime
from enum import Enum
from uuid import UUID
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class DataEventType(str, Enum):
    """Types of data events that trigger cache invalidation"""
    PRODUCT_UPDATED = "product_updated"
    PRODUCT_DELETED = "product_deleted"
    PRICE_UPDATED = "price_updated"
    REVIEW_ADDED = "review_added"
    REVIEW_UPDATED = "review_updated"
    SALES_DATA_UPDATED = "sales_data_updated"
    INVENTORY_UPDATED = "inventory_updated"


@dataclass
class DataEvent:
    """Data event for cache invalidation"""
    event_type: DataEventType
    tenant_id: UUID
    entity_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        return {
            "event_type": self.event_type.value,
            "tenant_id": str(self.tenant_id),
            "entity_id": self.entity_id,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


class CacheDependency:
    """
    Defines cache dependencies for cascade invalidation.
    
    When a data entity is updated, all dependent cache entries
    should be invalidated.
    """
    
    # Map of event types to affected cache types
    DEPENDENCIES = {
        DataEventType.PRODUCT_UPDATED: ['pricing', 'sentiment', 'forecast', 'query_result'],
        DataEventType.PRODUCT_DELETED: ['pricing', 'sentiment', 'forecast', 'query_result'],
        DataEventType.PRICE_UPDATED: ['pricing', 'query_result'],
        DataEventType.REVIEW_ADDED: ['sentiment', 'query_result'],
        DataEventType.REVIEW_UPDATED: ['sentiment', 'query_result'],
        DataEventType.SALES_DATA_UPDATED: ['forecast', 'query_result'],
        DataEventType.INVENTORY_UPDATED: ['forecast', 'query_result'],
    }
    
    @classmethod
    def get_affected_cache_types(cls, event_type: DataEventType) -> List[str]:
        """Get cache types affected by an event"""
        return cls.DEPENDENCIES.get(event_type, [])


class EventPublisher:
    """
    Publishes data update events for cache invalidation.
    
    When data is updated, publish an event that triggers
    cache invalidation for dependent caches.
    """
    
    def __init__(self):
        """Initialize event publisher"""
        self._subscribers: Dict[DataEventType, List[Callable]] = {}
        self._event_log: List[DataEvent] = []
        logger.info("EventPublisher initialized")
    
    def subscribe(self, event_type: DataEventType, callback: Callable):
        """
        Subscribe to data events.
        
        Args:
            event_type: Type of event to subscribe to
            callback: Callback function to invoke on event
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        self._subscribers[event_type].append(callback)
        logger.info(f"Subscribed to {event_type.value}")
    
    async def publish(self, event: DataEvent):
        """
        Publish a data event.
        
        Args:
            event: Data event to publish
        """
        logger.info(f"Publishing event: {event.event_type.value} for {event.entity_id}")
        
        # Log event
        self._event_log.append(event)
        
        # Notify subscribers
        subscribers = self._subscribers.get(event.event_type, [])
        for callback in subscribers:
            try:
                await callback(event)
            except Exception as e:
                logger.error(f"Error in event subscriber: {e}")
    
    def get_event_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent events"""
        return [event.to_dict() for event in self._event_log[-limit:]]


class EventSubscriber:
    """
    Subscribes to data events and invalidates cache.
    
    Implements cascade invalidation based on cache dependencies.
    """
    
    def __init__(self, cache_manager, publisher: EventPublisher):
        """
        Initialize event subscriber.
        
        Args:
            cache_manager: CacheManager instance
            publisher: EventPublisher instance
        """
        self.cache_manager = cache_manager
        self.publisher = publisher
        self._invalidation_log: List[Dict[str, Any]] = []
        
        # Subscribe to all event types
        for event_type in DataEventType:
            publisher.subscribe(event_type, self._handle_event)
        
        logger.info("EventSubscriber initialized and subscribed to all events")
    
    async def _handle_event(self, event: DataEvent):
        """
        Handle data event by invalidating affected caches.
        
        Args:
            event: Data event
        """
        logger.info(f"Handling event: {event.event_type.value}")
        
        # Get affected cache types
        affected_cache_types = CacheDependency.get_affected_cache_types(event.event_type)
        
        if not affected_cache_types:
            logger.debug(f"No cache dependencies for {event.event_type.value}")
            return
        
        # Invalidate affected caches
        total_invalidated = 0
        for cache_type in affected_cache_types:
            try:
                # Invalidate cache entries for this entity
                count = await self.cache_manager.invalidate_pattern(
                    cache_type=cache_type,
                    tenant_id=event.tenant_id,
                    pattern=f"*{event.entity_id}*"
                )
                total_invalidated += count
                
                logger.info(f"Invalidated {count} {cache_type} cache entries for {event.entity_id}")
            
            except Exception as e:
                logger.error(f"Error invalidating {cache_type} cache: {e}")
        
        # Log invalidation
        self._invalidation_log.append({
            "event": event.to_dict(),
            "affected_cache_types": affected_cache_types,
            "total_invalidated": total_invalidated,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def get_invalidation_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent invalidations"""
        return self._invalidation_log[-limit:]


class CacheInvalidationTracker:
    """
    Tracks cache invalidations for monitoring and debugging.
    
    Provides insights into:
    - Which events trigger invalidations
    - How many cache entries are invalidated
    - Invalidation patterns over time
    """
    
    def __init__(self):
        """Initialize invalidation tracker"""
        self._stats = {
            "total_events": 0,
            "total_invalidations": 0,
            "by_event_type": {},
            "by_cache_type": {}
        }
    
    def record_invalidation(
        self,
        event_type: DataEventType,
        cache_type: str,
        count: int
    ):
        """
        Record a cache invalidation.
        
        Args:
            event_type: Type of event that triggered invalidation
            cache_type: Type of cache invalidated
            count: Number of entries invalidated
        """
        self._stats["total_events"] += 1
        self._stats["total_invalidations"] += count
        
        # Track by event type
        event_key = event_type.value
        if event_key not in self._stats["by_event_type"]:
            self._stats["by_event_type"][event_key] = 0
        self._stats["by_event_type"][event_key] += count
        
        # Track by cache type
        if cache_type not in self._stats["by_cache_type"]:
            self._stats["by_cache_type"][cache_type] = 0
        self._stats["by_cache_type"][cache_type] += count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get invalidation statistics"""
        return self._stats.copy()
    
    def reset_stats(self):
        """Reset statistics"""
        self._stats = {
            "total_events": 0,
            "total_invalidations": 0,
            "by_event_type": {},
            "by_cache_type": {}
        }
