"""Cache management API endpoints"""
from uuid import UUID
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.models.user import User
from src.auth.dependencies import get_current_active_user, get_tenant_id
from src.cache.instance import get_cache_manager

router = APIRouter(prefix="/cache", tags=["cache"])


class CacheMetricsResponse(BaseModel):
    """Cache metrics response"""
    enabled: bool
    metrics: Dict[str, Any]


class CacheInvalidationResponse(BaseModel):
    """Cache invalidation response"""
    success: bool
    entries_invalidated: int
    message: str


@router.get("/metrics", response_model=CacheMetricsResponse)
async def get_cache_metrics(
    current_user: User = Depends(get_current_active_user)
) -> CacheMetricsResponse:
    """
    Get cache performance metrics.
    
    Returns:
        Cache metrics including hit rate, total requests, etc.
    """
    cache = get_cache_manager()
    
    if not cache:
        return CacheMetricsResponse(
            enabled=False,
            metrics={"message": "Cache is disabled"}
        )
    
    try:
        metrics = await cache.get_metrics()
        return CacheMetricsResponse(
            enabled=True,
            metrics=metrics
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving cache metrics: {str(e)}"
        )


@router.get("/health")
async def cache_health_check(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Check cache health status.
    
    Returns:
        Health status of the cache
    """
    cache = get_cache_manager()
    
    if not cache:
        return {
            "enabled": False,
            "healthy": False,
            "message": "Cache is disabled"
        }
    
    try:
        is_healthy = await cache.health_check()
        return {
            "enabled": True,
            "healthy": is_healthy,
            "message": "Cache is healthy" if is_healthy else "Cache is unhealthy"
        }
    except Exception as e:
        return {
            "enabled": True,
            "healthy": False,
            "message": f"Health check failed: {str(e)}"
        }


@router.delete("/tenant", response_model=CacheInvalidationResponse)
async def clear_tenant_cache(
    current_user: User = Depends(get_current_active_user),
    tenant_id: UUID = Depends(get_tenant_id)
) -> CacheInvalidationResponse:
    """
    Clear all cache entries for the current tenant.
    
    This is useful when you want to force fresh data retrieval.
    
    Returns:
        Number of cache entries cleared
    """
    cache = get_cache_manager()
    
    if not cache:
        return CacheInvalidationResponse(
            success=False,
            entries_invalidated=0,
            message="Cache is disabled"
        )
    
    try:
        entries_cleared = await cache.clear_tenant_cache(tenant_id)
        return CacheInvalidationResponse(
            success=True,
            entries_invalidated=entries_cleared,
            message=f"Cleared {entries_cleared} cache entries for tenant"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error clearing cache: {str(e)}"
        )


@router.delete("/product/{product_id}", response_model=CacheInvalidationResponse)
async def invalidate_product_cache(
    product_id: UUID,
    current_user: User = Depends(get_current_active_user),
    tenant_id: UUID = Depends(get_tenant_id)
) -> CacheInvalidationResponse:
    """
    Invalidate all cached data for a specific product.
    
    This should be called when product data is updated.
    
    Args:
        product_id: Product UUID
        
    Returns:
        Number of cache entries invalidated
    """
    cache = get_cache_manager()
    
    if not cache:
        return CacheInvalidationResponse(
            success=False,
            entries_invalidated=0,
            message="Cache is disabled"
        )
    
    try:
        from src.cache.query_cache_service import QueryCacheService
        cache_service = QueryCacheService(cache)
        
        entries_invalidated = await cache_service.invalidate_product_cache(
            tenant_id=tenant_id,
            product_id=product_id
        )
        
        return CacheInvalidationResponse(
            success=True,
            entries_invalidated=entries_invalidated,
            message=f"Invalidated {entries_invalidated} cache entries for product {product_id}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error invalidating product cache: {str(e)}"
        )
