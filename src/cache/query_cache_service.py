"""Query caching service for Quick Mode optimization"""
import hashlib
import json
import logging
from typing import Optional, Dict, Any
from uuid import UUID

from src.cache.cache_manager import CacheManager

logger = logging.getLogger(__name__)


class QueryCacheService:
    """
    Service for caching query results to optimize Quick Mode performance.
    
    Handles:
    - Query result caching with tenant isolation
    - Agent-specific result caching (pricing, sentiment, forecast)
    - Cache key generation from query parameters
    - Automatic cache invalidation on data updates
    """
    
    def __init__(self, cache_manager: CacheManager):
        """
        Initialize query cache service.
        
        Args:
            cache_manager: CacheManager instance
        """
        self.cache = cache_manager
    
    def _generate_query_hash(self, query: str, params: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate deterministic hash for query caching.
        
        Args:
            query: Query string
            params: Optional query parameters
            
        Returns:
            Hash string for cache key
        """
        # Normalize query
        normalized_query = query.lower().strip()
        
        # Include params in hash if provided
        if params:
            # Sort params for deterministic hashing
            params_str = json.dumps(params, sort_keys=True, default=str)
            cache_input = f"{normalized_query}:{params_str}"
        else:
            cache_input = normalized_query
        
        # Generate SHA256 hash
        return hashlib.sha256(cache_input.encode()).hexdigest()[:16]
    
    async def get_query_result(
        self,
        tenant_id: UUID,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached query result.
        
        Args:
            tenant_id: Tenant UUID
            query: Query string
            params: Optional query parameters
            
        Returns:
            Cached result or None if not found/stale
        """
        query_hash = self._generate_query_hash(query, params)
        
        result = await self.cache.get(
            cache_type='query_result',
            tenant_id=tenant_id,
            identifier=query_hash,
            check_freshness=True
        )
        
        if result:
            logger.info(f"Query cache hit for tenant {tenant_id}")
        
        return result
    
    async def set_query_result(
        self,
        tenant_id: UUID,
        query: str,
        result: Dict[str, Any],
        params: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache query result.
        
        Args:
            tenant_id: Tenant UUID
            query: Query string
            result: Query result to cache
            params: Optional query parameters
            ttl: Optional TTL override (seconds)
            
        Returns:
            True if cached successfully
        """
        query_hash = self._generate_query_hash(query, params)
        
        success = await self.cache.set(
            cache_type='query_result',
            tenant_id=tenant_id,
            identifier=query_hash,
            data=result,
            ttl=ttl
        )
        
        if success:
            logger.info(f"Query result cached for tenant {tenant_id}")
        
        return success
    
    async def get_pricing_analysis(
        self,
        tenant_id: UUID,
        product_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached pricing analysis for a product.
        
        Args:
            tenant_id: Tenant UUID
            product_id: Product UUID
            
        Returns:
            Cached pricing analysis or None
        """
        return await self.cache.get(
            cache_type='pricing',
            tenant_id=tenant_id,
            identifier=str(product_id),
            check_freshness=True
        )
    
    async def set_pricing_analysis(
        self,
        tenant_id: UUID,
        product_id: UUID,
        analysis: Dict[str, Any]
    ) -> bool:
        """
        Cache pricing analysis for a product.
        
        Args:
            tenant_id: Tenant UUID
            product_id: Product UUID
            analysis: Pricing analysis result
            
        Returns:
            True if cached successfully
        """
        return await self.cache.set(
            cache_type='pricing',
            tenant_id=tenant_id,
            identifier=str(product_id),
            data=analysis
        )
    
    async def get_sentiment_analysis(
        self,
        tenant_id: UUID,
        product_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached sentiment analysis for a product.
        
        Args:
            tenant_id: Tenant UUID
            product_id: Product UUID
            
        Returns:
            Cached sentiment analysis or None
        """
        return await self.cache.get(
            cache_type='sentiment',
            tenant_id=tenant_id,
            identifier=str(product_id),
            check_freshness=True
        )
    
    async def set_sentiment_analysis(
        self,
        tenant_id: UUID,
        product_id: UUID,
        analysis: Dict[str, Any]
    ) -> bool:
        """
        Cache sentiment analysis for a product.
        
        Args:
            tenant_id: Tenant UUID
            product_id: Product UUID
            analysis: Sentiment analysis result
            
        Returns:
            True if cached successfully
        """
        return await self.cache.set(
            cache_type='sentiment',
            tenant_id=tenant_id,
            identifier=str(product_id),
            data=analysis
        )
    
    async def get_demand_forecast(
        self,
        tenant_id: UUID,
        product_id: UUID,
        horizon_days: int = 30
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached demand forecast for a product.
        
        Args:
            tenant_id: Tenant UUID
            product_id: Product UUID
            horizon_days: Forecast horizon
            
        Returns:
            Cached forecast or None
        """
        identifier = f"{product_id}:{horizon_days}"
        
        return await self.cache.get(
            cache_type='forecast',
            tenant_id=tenant_id,
            identifier=identifier,
            check_freshness=True
        )
    
    async def set_demand_forecast(
        self,
        tenant_id: UUID,
        product_id: UUID,
        forecast: Dict[str, Any],
        horizon_days: int = 30
    ) -> bool:
        """
        Cache demand forecast for a product.
        
        Args:
            tenant_id: Tenant UUID
            product_id: Product UUID
            forecast: Forecast result
            horizon_days: Forecast horizon
            
        Returns:
            True if cached successfully
        """
        identifier = f"{product_id}:{horizon_days}"
        
        return await self.cache.set(
            cache_type='forecast',
            tenant_id=tenant_id,
            identifier=identifier,
            data=forecast
        )
    
    async def invalidate_product_cache(
        self,
        tenant_id: UUID,
        product_id: UUID
    ) -> int:
        """
        Invalidate all cached data for a product.
        
        This should be called when product data is updated.
        
        Args:
            tenant_id: Tenant UUID
            product_id: Product UUID
            
        Returns:
            Number of cache entries invalidated
        """
        total_invalidated = 0
        
        # Invalidate pricing cache
        total_invalidated += await self.cache.invalidate_pattern(
            cache_type='pricing',
            tenant_id=tenant_id,
            pattern=f"{product_id}*"
        )
        
        # Invalidate sentiment cache
        total_invalidated += await self.cache.invalidate_pattern(
            cache_type='sentiment',
            tenant_id=tenant_id,
            pattern=f"{product_id}*"
        )
        
        # Invalidate forecast cache
        total_invalidated += await self.cache.invalidate_pattern(
            cache_type='forecast',
            tenant_id=tenant_id,
            pattern=f"{product_id}*"
        )
        
        logger.info(f"Invalidated {total_invalidated} cache entries for product {product_id}")
        
        return total_invalidated
    
    async def invalidate_query_cache(
        self,
        tenant_id: UUID
    ) -> int:
        """
        Invalidate all query result caches for a tenant.
        
        This should be called when significant data updates occur.
        
        Args:
            tenant_id: Tenant UUID
            
        Returns:
            Number of cache entries invalidated
        """
        return await self.cache.invalidate_pattern(
            cache_type='query_result',
            tenant_id=tenant_id,
            pattern='*'
        )
