"""Redis-based cache manager for Quick Mode optimization"""
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Any, Dict
from uuid import UUID

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Manages Redis caching with freshness guarantees for Quick Mode.
    
    Cache Freshness Thresholds:
    - Pricing data: 1 hour
    - Review/Sentiment data: 24 hours
    - Forecast outputs: 12 hours
    
    LRU Eviction:
    - Redis handles LRU eviction automatically when maxmemory is reached
    - Configure Redis with: maxmemory-policy allkeys-lru
    """
    
    # Cache freshness thresholds (in seconds)
    FRESHNESS_THRESHOLDS = {
        'pricing': 3600,        # 1 hour
        'sentiment': 86400,     # 24 hours
        'forecast': 43200,      # 12 hours
        'query_result': 3600,   # 1 hour for full query results
    }
    
    # Default cache size limits (in MB)
    DEFAULT_MAX_MEMORY_MB = 256
    DEFAULT_TTL = 3600  # 1 hour default TTL
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        max_memory_mb: int = DEFAULT_MAX_MEMORY_MB,
        default_ttl: int = DEFAULT_TTL,
        eviction_policy: str = "allkeys-lru",
        use_memory_fallback: bool = False
    ):
        """
        Initialize cache manager with Redis connection.
        
        Args:
            redis_url: Redis connection URL
            max_memory_mb: Maximum memory for cache in MB
            default_ttl: Default TTL for cache entries in seconds
            eviction_policy: Redis eviction policy (default: allkeys-lru)
            use_memory_fallback: Use in-memory dict fallback if Redis unavailable
        """
        if not REDIS_AVAILABLE:
            logger.warning("Redis package not installed. Cache will be disabled.")
        
        self.redis_url = redis_url
        self.max_memory_mb = max_memory_mb
        self.default_ttl = default_ttl
        self.eviction_policy = eviction_policy
        self.use_memory_fallback = use_memory_fallback
        self._redis: Optional[redis.Redis] = None
        self._memory_cache: Dict[str, Any] = {}  # In-memory fallback
        self._metrics = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'invalidations': 0,
            'evictions': 0
        }
    
    async def connect(self):
        """Establish Redis connection and configure LRU eviction"""
        if not REDIS_AVAILABLE:
            if self.use_memory_fallback:
                logger.warning("Redis package not available. Using in-memory fallback.")
                return
            logger.warning("Redis package not available. Cache disabled.")
            return
        
        if self._redis is None:
            try:
                # Add connection timeout to prevent hanging
                self._redis = await redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=5,  # 5 second connection timeout
                    socket_timeout=5,  # 5 second operation timeout
                    retry_on_timeout=False
                )
                
                # Test connection with timeout
                import asyncio
                await asyncio.wait_for(self._redis.ping(), timeout=5.0)
                
                # Configure Redis for LRU eviction
                await self._configure_lru_eviction()
                
                logger.info("Redis cache connected successfully with LRU eviction")
            except asyncio.TimeoutError:
                logger.error(f"Redis connection timeout - server not reachable at {self.redis_url}")
                if self.use_memory_fallback:
                    logger.warning("Using in-memory cache fallback")
                else:
                    logger.warning("Continuing without cache")
                self._redis = None
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                if self.use_memory_fallback:
                    logger.warning("Using in-memory cache fallback")
                else:
                    logger.warning("Continuing without cache")
                self._redis = None
    
    async def _configure_lru_eviction(self):
        """Configure Redis for LRU eviction policy"""
        try:
            # Set max memory
            max_memory_bytes = self.max_memory_mb * 1024 * 1024
            await self._redis.config_set('maxmemory', max_memory_bytes)
            
            # Set eviction policy to LRU
            await self._redis.config_set('maxmemory-policy', self.eviction_policy)
            
            logger.info(f"Redis configured: maxmemory={self.max_memory_mb}MB, policy={self.eviction_policy}")
        
        except Exception as e:
            logger.warning(f"Could not configure Redis LRU eviction: {e}")
            logger.warning("Redis may need manual configuration for production use")
    
    async def disconnect(self):
        """Close Redis connection"""
        if self._redis:
            await self._redis.aclose()
            self._redis = None
            logger.info("Redis cache disconnected")
    
    def _build_cache_key(
        self,
        cache_type: str,
        tenant_id: UUID,
        key: str
    ) -> str:
        """
        Build cache key with tenant isolation and cache type.
        
        Args:
            cache_type: Type of cached data (pricing, sentiment, forecast, etc.)
            tenant_id: Tenant UUID for isolation
            key: Unique identifier for the cached item
            
        Returns:
            Namespaced cache key string in format: cache_type:tenant_id:key
        """
        return f"{cache_type}:{tenant_id}:{key}"
    
    async def get(
        self,
        cache_type: Optional[str] = None,
        tenant_id: Optional[UUID] = None,
        identifier: Optional[str] = None,
        check_freshness: bool = True,
        key: Optional[str] = None
    ) -> Optional[Any]:
        """
        Retrieve cached data.
        
        Supports two calling patterns:
        1. Structured: get(cache_type, tenant_id, identifier, check_freshness)
        2. Simple: get(key=full_key)
        
        Args:
            cache_type: Type of cached data (pricing, sentiment, forecast, etc.)
            tenant_id: Tenant UUID for isolation
            identifier: Unique identifier for the cached item
            check_freshness: Whether to check if data is still fresh
            key: Full cache key (alternative to cache_type/tenant_id/identifier)
            
        Returns:
            Cached data or None if not found or stale
        """
        if not self._redis:
            await self.connect()
        
        # Determine which API pattern is being used
        if key is not None:
            # Simple API: key is provided directly
            full_key = key
            # Extract cache_type from key for freshness check (format: cache_type:tenant_id:identifier)
            cache_type_for_freshness = key.split(':')[0] if ':' in key else None
        elif cache_type is not None and tenant_id is not None and identifier is not None:
            # Structured API: build key from components
            full_key = self._build_cache_key(cache_type, tenant_id, identifier)
            cache_type_for_freshness = cache_type
        else:
            raise ValueError("Must provide either 'key' or all of (cache_type, tenant_id, identifier)")
        
        # Use memory fallback if Redis unavailable
        if not self._redis and self.use_memory_fallback:
            cached_json = self._memory_cache.get(full_key)
            if cached_json is None:
                self._metrics['misses'] += 1
                return None
            
            cached_data = json.loads(cached_json)
            
            # Check freshness if requested and cache_type is known
            if check_freshness and cache_type_for_freshness and not self._is_fresh(cache_type_for_freshness, cached_data):
                self._metrics['misses'] += 1
                return None
            
            self._metrics['hits'] += 1
            return cached_data.get('data')
        
        if not self._redis:
            self._metrics['misses'] += 1
            return None
        
        try:
            # Get cached data
            cached_json = await self._redis.get(full_key)
            
            if cached_json is None:
                self._metrics['misses'] += 1
                logger.debug(f"Cache miss: {full_key}")
                return None
            
            cached_data = json.loads(cached_json)
            
            # Check freshness if requested and cache_type is known
            if check_freshness and cache_type_for_freshness and not self._is_fresh(cache_type_for_freshness, cached_data):
                self._metrics['misses'] += 1
                logger.debug(f"Cache stale: {full_key}")
                return None
            
            self._metrics['hits'] += 1
            logger.debug(f"Cache hit: {full_key}")
            return cached_data.get('data')
        
        except Exception as e:
            logger.error(f"Error retrieving from cache: {e}")
            self._metrics['misses'] += 1
            return None
    
    async def set(
        self,
        cache_type: Optional[str] = None,
        tenant_id: Optional[UUID] = None,
        identifier: Optional[str] = None,
        data: Optional[Any] = None,
        ttl: Optional[int] = None,
        key: Optional[str] = None,
        value: Optional[Any] = None
    ) -> bool:
        """
        Store data in cache with TTL.
        
        Supports two calling patterns:
        1. Structured: set(cache_type, tenant_id, identifier, data, ttl)
        2. Simple: set(key=full_key, value=data, ttl=ttl)
        
        Args:
            cache_type: Type of cached data (pricing, sentiment, forecast, etc.)
            tenant_id: Tenant UUID for isolation
            identifier: Unique identifier for the cached item
            data: Data to cache (must be JSON serializable)
            ttl: Time-to-live in seconds (defaults to cache_type threshold)
            key: Full cache key (alternative to cache_type/tenant_id/identifier)
            value: Data to cache (alternative to 'data' parameter)
            
        Returns:
            True if successful, False otherwise
        """
        if not self._redis:
            await self.connect()
        
        # Determine which API pattern is being used
        if key is not None:
            # Simple API: key and value provided directly
            full_key = key
            cache_data = value if value is not None else data
            # Extract cache_type from key for TTL default (format: cache_type:tenant_id:identifier)
            cache_type_for_ttl = key.split(':')[0] if ':' in key else None
        elif cache_type is not None and tenant_id is not None and identifier is not None:
            # Structured API: build key from components
            full_key = self._build_cache_key(cache_type, tenant_id, identifier)
            cache_data = data
            cache_type_for_ttl = cache_type
            logger.debug(f"Structured API set - cache_type: {cache_type}, tenant_id: {tenant_id}, identifier: {identifier}, full_key: {full_key}")
        else:
            raise ValueError("Must provide either 'key' and 'value' or all of (cache_type, tenant_id, identifier, data)")
        
        # Use cache type threshold as default TTL if not specified
        if ttl is None:
            if cache_type_for_ttl:
                ttl = self.FRESHNESS_THRESHOLDS.get(cache_type_for_ttl, self.default_ttl)
            else:
                ttl = self.default_ttl
        
        # Wrap data with metadata
        cache_entry = {
            'data': cache_data,
            'cached_at': datetime.utcnow().isoformat()
        }
        
        # Use memory fallback if Redis unavailable
        if not self._redis and self.use_memory_fallback:
            self._memory_cache[full_key] = json.dumps(cache_entry, default=str)
            self._metrics['sets'] += 1
            logger.debug(f"Cache set (memory): {full_key}")
            return True
        
        # Guard against Redis being None
        if not self._redis:
            logger.warning(f"Cannot set cache: Redis unavailable and no fallback enabled")
            return False
        
        try:
            # Store in Redis with TTL
            await self._redis.setex(
                full_key,
                ttl,
                json.dumps(cache_entry, default=str)
            )
            
            self._metrics['sets'] += 1
            logger.debug(f"Cache set: {full_key} (TTL: {ttl}s)")
            return True
        
        except Exception as e:
            logger.error(f"Error setting cache: {e}")
            return False
    
    async def delete(
        self,
        cache_type: Optional[str] = None,
        tenant_id: Optional[UUID] = None,
        identifier: Optional[str] = None,
        key: Optional[str] = None
    ) -> bool:
        """
        Delete cached entry.
        
        Supports two calling patterns:
        1. Structured: delete(cache_type, tenant_id, identifier)
        2. Simple: delete(key=full_key)
        
        Args:
            cache_type: Type of cached data (pricing, sentiment, forecast, etc.)
            tenant_id: Tenant UUID for isolation
            identifier: Unique identifier for the cached item
            key: Full cache key (alternative to cache_type/tenant_id/identifier)
            
        Returns:
            True if deleted, False otherwise
        """
        if not self._redis:
            await self.connect()
        
        # Determine which API pattern is being used
        if key is not None:
            # Simple API: key provided directly
            full_key = key
        elif cache_type is not None and tenant_id is not None and identifier is not None:
            # Structured API: build key from components
            full_key = self._build_cache_key(cache_type, tenant_id, identifier)
        else:
            raise ValueError("Must provide either 'key' or all of (cache_type, tenant_id, identifier)")
        
        # Use memory fallback if Redis unavailable
        if not self._redis and self.use_memory_fallback:
            if full_key in self._memory_cache:
                del self._memory_cache[full_key]
                self._metrics['invalidations'] += 1
                logger.info(f"Cache invalidated (memory): {full_key}")
                return True
            return False
        
        # Guard against Redis being None
        if not self._redis:
            return False
        
        try:
            result = await self._redis.delete(full_key)
            if result > 0:
                self._metrics['invalidations'] += 1
                logger.info(f"Cache invalidated: {full_key}")
                return True
            return False
        
        except Exception as e:
            logger.error(f"Error deleting from cache: {e}")
            return False
    
    async def invalidate_pattern(
        self,
        cache_type: Optional[str] = None,
        tenant_id: Optional[UUID] = None,
        pattern: str = "*"
    ) -> int:
        """
        Invalidate multiple cache entries matching a pattern.
        
        Supports two calling patterns:
        1. Simple: invalidate_pattern(full_pattern_string) - pattern as first arg
        2. Structured: invalidate_pattern(cache_type, tenant_id, pattern)
        
        Args:
            cache_type: Type of cached data OR full pattern string (if tenant_id is None)
            tenant_id: Tenant UUID (None if using simple API)
            pattern: Pattern to match (default: all entries of type)
            
        Returns:
            Number of entries invalidated
        """
        if not self._redis:
            await self.connect()
        
        # Determine which API pattern is being used
        if tenant_id is None and cache_type is not None:
            # Simple API: cache_type is actually the full pattern string
            search_pattern = cache_type
        elif cache_type is not None and tenant_id is not None:
            # Structured API: build pattern from components
            search_pattern = f"{cache_type}:{tenant_id}:{pattern}"
        else:
            raise ValueError("Must provide either a pattern string or (cache_type, tenant_id, pattern)")
        
        # Use memory fallback if Redis unavailable
        if not self._redis and self.use_memory_fallback:
            # Convert Redis-style pattern to regex for memory cache
            # Redis patterns use * for any characters, we need to convert to regex
            import re
            # Escape special regex characters except *
            regex_pattern = re.escape(search_pattern).replace(r'\*', '.*')
            regex = re.compile(f'^{regex_pattern}$')
            
            keys_to_delete = [k for k in self._memory_cache.keys() if regex.match(k)]
            deleted = 0
            for key in keys_to_delete:
                del self._memory_cache[key]
                deleted += 1
            
            if deleted > 0:
                self._metrics['invalidations'] += deleted
                logger.info(f"Cache pattern invalidated (memory): {search_pattern} ({deleted} entries)")
            return deleted
        
        # Guard against Redis being None
        if not self._redis:
            logger.warning(f"Cannot invalidate pattern: Redis not connected and no fallback")
            return 0
        
        try:
            # Find matching keys
            keys = []
            logger.debug(f"Scanning Redis for pattern: {search_pattern}")
            async for key in self._redis.scan_iter(match=search_pattern):
                keys.append(key)
                logger.debug(f"Found matching key: {key}")
            
            # Delete all matching keys
            if keys:
                deleted = await self._redis.delete(*keys)
                self._metrics['invalidations'] += deleted
                logger.info(f"Cache pattern invalidated: {search_pattern} ({deleted} entries)")
                return deleted
            
            logger.debug(f"No keys found matching pattern: {search_pattern}")
            return 0
        
        except Exception as e:
            logger.error(f"Error invalidating cache pattern: {e}")
            return 0
    
    def _is_fresh(self, cache_type: str, cached_data: Dict[str, Any]) -> bool:
        """
        Check if cached data is still fresh.
        
        Args:
            cache_type: Type of cached data
            cached_data: Cached data with metadata
            
        Returns:
            True if fresh, False if stale (age >= threshold is stale)
        """
        threshold = self.FRESHNESS_THRESHOLDS.get(cache_type, 3600)
        cached_at_str = cached_data.get('cached_at')
        
        if not cached_at_str:
            return False
        
        try:
            cached_at = datetime.fromisoformat(cached_at_str)
            age = (datetime.utcnow() - cached_at).total_seconds()
            # Stale if age >= threshold (boundary case: exactly at threshold is stale)
            if age >= threshold:
                return False
            return True
        
        except Exception as e:
            logger.error(f"Error checking cache freshness: {e}")
            return False
    
    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get cache performance metrics including evictions.
        
        Returns:
            Dictionary with cache metrics
        """
        total_requests = self._metrics['hits'] + self._metrics['misses']
        hit_rate = (self._metrics['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        metrics = {
            **self._metrics,
            'total_requests': total_requests,
            'hit_rate_percent': round(hit_rate, 2)
        }
        
        # Get Redis info if connected
        if self._redis:
            try:
                info = await self._redis.info('stats')
                metrics['redis_keyspace_hits'] = info.get('keyspace_hits', 0)
                metrics['redis_keyspace_misses'] = info.get('keyspace_misses', 0)
                metrics['redis_evicted_keys'] = info.get('evicted_keys', 0)
                
                # Get memory info
                memory_info = await self._redis.info('memory')
                metrics['used_memory_mb'] = round(memory_info.get('used_memory', 0) / (1024 * 1024), 2)
                metrics['max_memory_mb'] = self.max_memory_mb
                metrics['memory_usage_percent'] = round(
                    (metrics['used_memory_mb'] / self.max_memory_mb * 100), 2
                ) if self.max_memory_mb > 0 else 0
                
                # Update evictions metric from Redis
                self._metrics['evictions'] = metrics['redis_evicted_keys']
            
            except Exception as e:
                logger.error(f"Error getting Redis metrics: {e}")
        
        return metrics
    
    async def clear_tenant_cache(self, tenant_id: UUID) -> int:
        """
        Clear all cache entries for a tenant.
        
        Args:
            tenant_id: Tenant UUID
            
        Returns:
            Number of entries cleared
        """
        if not self._redis:
            await self.connect()
        
        pattern = f"*:{tenant_id}:*"
        
        # Use memory fallback if Redis unavailable
        if not self._redis and self.use_memory_fallback:
            import fnmatch
            keys_to_delete = [k for k in self._memory_cache.keys() if fnmatch.fnmatch(k, pattern)]
            deleted = 0
            for key in keys_to_delete:
                del self._memory_cache[key]
                deleted += 1
            
            if deleted > 0:
                logger.info(f"Cleared cache for tenant {tenant_id} (memory): {deleted} entries")
            return deleted
        
        # Guard against Redis being None
        if not self._redis:
            return 0
        
        try:
            keys = []
            async for key in self._redis.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                deleted = await self._redis.delete(*keys)
                logger.info(f"Cleared cache for tenant {tenant_id}: {deleted} entries")
                return deleted
            
            return 0
        
        except Exception as e:
            logger.error(f"Error clearing tenant cache: {e}")
            return 0
    
    async def health_check(self) -> bool:
        """
        Check if Redis is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            if not self._redis:
                await self.connect()
            
            # If still no Redis after connect attempt, return False
            if not self._redis:
                return False
            
            await self._redis.ping()
            return True
        
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
