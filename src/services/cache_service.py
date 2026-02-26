"""
Cache Service - Helper functions for Redis caching with tenant isolation
"""
import json
import logging
from typing import Any, Optional, Dict
from src.cache.instance import get_cache_manager

logger = logging.getLogger(__name__)


def make_cache_key(prefix: str, tenant_id: str, **params) -> str:
    """
    Build a cache key with tenant isolation.
    
    Format: {prefix}:{tenant_id}:{param1}:{param2}...
    
    Args:
        prefix: Cache key prefix (e.g., "dashboard", "products", "pricing")
        tenant_id: Tenant UUID for isolation
        **params: Additional parameters to include in key (e.g., page=1, days=30)
    
    Returns:
        Cache key string
    
    Examples:
        make_cache_key("dashboard", "tenant-001") 
        → "dashboard:tenant-001"
        
        make_cache_key("products", "tenant-001", page=1, limit=20)
        → "products:tenant-001:page:1:limit:20"
        
        make_cache_key("forecast", "tenant-001", horizon=30)
        → "forecast:tenant-001:horizon:30"
    """
    key_parts = [prefix, tenant_id]
    
    # Add sorted params for consistent key generation
    if params:
        for param_key in sorted(params.keys()):
            param_value = params[param_key]
            key_parts.extend([param_key, str(param_value)])
    
    return ":".join(key_parts)


async def get_cached(key: str) -> Optional[Any]:
    """
    Retrieve data from Redis cache.
    
    Args:
        key: Cache key to retrieve
    
    Returns:
        Cached data if found and valid, None otherwise
    """
    cache_manager = get_cache_manager()
    
    if not cache_manager:
        logger.warning(f"Cache manager not available for key: {key}")
        return None
    
    if not cache_manager._redis:
        logger.warning(f"Redis not connected for key: {key}")
        return None
    
    try:
        # Use simple API pattern with full key
        cached_json = await cache_manager._redis.get(key)
        
        if cached_json is None:
            logger.info(f"❌ Cache MISS: {key}")
            return None
        
        # Parse JSON
        import json
        cached_data = json.loads(cached_json)
        
        logger.info(f"✅ Cache HIT: {key}")
        return cached_data
    
    except Exception as e:
        logger.warning(f"Cache retrieval error for {key}: {e}")
        return None


async def set_cached(key: str, data: Any, ttl: int) -> bool:
    """
    Store data in Redis cache with TTL.
    
    Args:
        key: Cache key
        data: Data to cache (must be JSON serializable)
        ttl: Time-to-live in seconds
    
    Returns:
        True if successful, False otherwise
    """
    cache_manager = get_cache_manager()
    
    if not cache_manager:
        logger.warning(f"Cache manager not available, skipping cache set for: {key}")
        return False
    
    if not cache_manager._redis:
        logger.warning(f"Redis not connected, skipping cache set for: {key}")
        return False
    
    try:
        # Serialize to JSON
        import json
        cached_json = json.dumps(data)
        
        # Store in Redis with TTL
        await cache_manager._redis.set(key, cached_json, ex=ttl)
        
        logger.info(f"💾 Cache SET: {key} (TTL: {ttl}s)")
        return True
    
    except Exception as e:
        logger.warning(f"Cache set error for {key}: {e}")
        return False


async def invalidate_cache(key: str) -> bool:
    """
    Invalidate a specific cache key.
    
    Args:
        key: Cache key to invalidate
    
    Returns:
        True if successful, False otherwise
    """
    cache_manager = get_cache_manager()
    
    if not cache_manager:
        return False
    
    try:
        if cache_manager._redis:
            await cache_manager._redis.delete(key)
            logger.info(f"🗑️  Cache INVALIDATED: {key}")
            return True
        return False
    
    except Exception as e:
        logger.warning(f"Cache invalidation error for {key}: {e}")
        return False


async def invalidate_tenant_cache(tenant_id: str, prefix: Optional[str] = None) -> int:
    """
    Invalidate all cache keys for a specific tenant.
    
    Args:
        tenant_id: Tenant UUID
        prefix: Optional prefix to limit invalidation (e.g., "dashboard", "products")
    
    Returns:
        Number of keys invalidated
    """
    cache_manager = get_cache_manager()
    
    if not cache_manager or not cache_manager._redis:
        return 0
    
    try:
        # Build pattern to match tenant keys
        if prefix:
            pattern = f"{prefix}:{tenant_id}:*"
        else:
            pattern = f"*:{tenant_id}:*"
        
        # Find all matching keys
        keys = []
        async for key in cache_manager._redis.scan_iter(match=pattern):
            keys.append(key)
        
        # Delete all matching keys
        if keys:
            deleted = await cache_manager._redis.delete(*keys)
            logger.info(f"🗑️  Cache INVALIDATED: {deleted} keys for tenant {tenant_id} (pattern: {pattern})")
            return deleted
        
        return 0
    
    except Exception as e:
        logger.warning(f"Tenant cache invalidation error for {tenant_id}: {e}")
        return 0


# Cache TTL constants (in seconds)
CACHE_TTL = {
    "dashboard": 300,           # 5 minutes
    "dashboard_kpis": 300,      # 5 minutes
    "dashboard_trends": 300,    # 5 minutes
    "dashboard_alerts": 300,    # 5 minutes
    "dashboard_insights": 300,  # 5 minutes
    "dashboard_stats": 300,     # 5 minutes
    "dashboard_activity": 300,  # 5 minutes
    "products": 600,            # 10 minutes
    "metrics": 300,             # 5 minutes
    "competitor_matrix": 180,   # 3 minutes
    "pricing_trends": 600,      # 10 minutes
    "pricing_recommendations": 900,  # 15 minutes
    "pricing_promotions": 600,  # 10 minutes
    "sentiment_overview": 900,  # 15 minutes
    "sentiment_themes": 900,    # 15 minutes
    "sentiment_reviews": 600,   # 10 minutes
    "sentiment_complaints": 900,  # 15 minutes
    "forecast_demand": 1800,    # 30 minutes
    "forecast_inventory": 300,  # 5 minutes
    "forecast_sales": 600,      # 10 minutes
}


def get_ttl(cache_type: str) -> int:
    """
    Get TTL for a cache type.
    
    Args:
        cache_type: Type of cache (e.g., "dashboard", "products")
    
    Returns:
        TTL in seconds (defaults to 300 if not found)
    """
    return CACHE_TTL.get(cache_type, 300)
