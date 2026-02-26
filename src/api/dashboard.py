"""Dashboard API endpoints"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models.product import Product
from src.models.review import Review
from src.services.data_service import DataService
from src.services.cache_service import (
    make_cache_key,
    get_cached,
    set_cached,
    get_ttl
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def get_tenant_id_from_request(request: Request) -> UUID:
    """Extract tenant_id from request state (set by middleware)"""
    if not hasattr(request.state, "tenant_id"):
        raise HTTPException(status_code=401, detail="Tenant context not found")
    return request.state.tenant_id


def get_user_email_from_request(request: Request) -> str:
    """Extract user email from request state"""
    if not hasattr(request.state, "user_id"):
        return "demo@example.com"  # Fallback for demo mode
    # In production, fetch from database using user_id
    return "seller@tenant-001.com"


@router.get("/stats")
async def get_dashboard_stats(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get dashboard statistics
    Uses DataService to fetch from Mock API or Database
    WITH REDIS CACHING
    """
    try:
        tenant_id = str(get_tenant_id_from_request(request))
        email = get_user_email_from_request(request)
        
        # Step 1: Build cache key
        cache_key = make_cache_key("dashboard_stats", tenant_id)
        
        # Step 2: Check cache
        cached_data = await get_cached(cache_key)
        if cached_data is not None:
            return cached_data
        
        # Step 3: Cache miss - fetch from DataService
        logger.info(f"Fetching dashboard stats from Mock API for tenant {tenant_id}")
        data_service = DataService(tenant_id=tenant_id, email=email, db=db)
        stats = await data_service.get_dashboard_stats()
        
        # Step 4: Store in cache
        await set_cached(cache_key, stats, ttl=get_ttl("dashboard_stats"))
        
        # Step 5: Return
        return stats
        
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch dashboard stats: {str(e)}")


@router.get("/recent-activity")
async def get_recent_activity(
    request: Request,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get recent activity
    Uses DataService to fetch from Mock API or Database
    WITH REDIS CACHING
    """
    try:
        tenant_id = str(get_tenant_id_from_request(request))
        email = get_user_email_from_request(request)
        
        # Step 1: Build cache key with limit parameter
        cache_key = make_cache_key("dashboard_activity", tenant_id, limit=limit)
        
        # Step 2: Check cache
        cached_data = await get_cached(cache_key)
        if cached_data is not None:
            return cached_data
        
        # Step 3: Cache miss - fetch from DataService
        logger.info(f"Fetching recent activity from Mock API for tenant {tenant_id} (limit={limit})")
        data_service = DataService(tenant_id=tenant_id, email=email, db=db)
        activities = await data_service.get_recent_activity(limit=limit)
        
        # Step 4: Store in cache
        await set_cached(cache_key, activities, ttl=get_ttl("dashboard_activity"))
        
        # Step 5: Return
        return activities
        
    except Exception as e:
        logger.error(f"Error fetching recent activity: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch recent activity: {str(e)}")



@router.get("/kpis")
async def get_dashboard_kpis(
    request: Request,
    days: int = 30,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get key performance indicators for the dashboard
    Uses DataService to fetch from Mock API or Database
    WITH REDIS CACHING
    """
    try:
        tenant_id = str(get_tenant_id_from_request(request))
        email = get_user_email_from_request(request)
        
        # Step 1: Build cache key with days parameter
        cache_key = make_cache_key("dashboard_kpis", tenant_id, days=days)
        
        # Step 2: Check cache
        cached_data = await get_cached(cache_key)
        if cached_data is not None:
            return {"payload": cached_data}
        
        # Step 3: Cache miss - fetch from DataService
        logger.info(f"Fetching dashboard KPIs from Mock API for tenant {tenant_id} (days={days})")
        data_service = DataService(tenant_id=tenant_id, email=email, db=db)
        kpis = await data_service.get_dashboard_kpis(days=days)
        
        # Step 4: Store in cache
        await set_cached(cache_key, kpis, ttl=get_ttl("dashboard_kpis"))
        
        # Step 5: Return
        return {"payload": kpis}
        
    except Exception as e:
        logger.error(f"Error fetching dashboard KPIs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch KPIs: {str(e)}")


@router.get("/insights")
async def get_dashboard_insights(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get AI-generated insights for the dashboard
    Uses DataService to fetch from Mock API or Database
    WITH REDIS CACHING
    """
    try:
        tenant_id = str(get_tenant_id_from_request(request))
        email = get_user_email_from_request(request)
        
        # Step 1: Build cache key
        cache_key = make_cache_key("dashboard_insights", tenant_id)
        
        # Step 2: Check cache
        cached_data = await get_cached(cache_key)
        if cached_data is not None:
            return {"payload": cached_data}
        
        # Step 3: Cache miss - fetch from DataService
        logger.info(f"Fetching dashboard insights from Mock API for tenant {tenant_id}")
        data_service = DataService(tenant_id=tenant_id, email=email, db=db)
        insights_data = await data_service.get_dashboard_insights()
        
        # Step 4: Store in cache
        await set_cached(cache_key, insights_data, ttl=get_ttl("dashboard_insights"))
        
        # Step 5: Return
        return {"payload": insights_data}
        
    except Exception as e:
        logger.error(f"Error fetching dashboard insights: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch insights: {str(e)}")


@router.get("/alerts")
async def get_dashboard_alerts(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get critical alerts for the dashboard
    Uses DataService to fetch from Mock API or Database
    WITH REDIS CACHING
    """
    try:
        tenant_id = str(get_tenant_id_from_request(request))
        email = get_user_email_from_request(request)
        
        # Step 1: Build cache key
        cache_key = make_cache_key("dashboard_alerts", tenant_id)
        
        # Step 2: Check cache
        cached_data = await get_cached(cache_key)
        if cached_data is not None:
            return {"payload": cached_data}
        
        # Step 3: Cache miss - fetch from DataService
        logger.info(f"Fetching dashboard alerts from Mock API for tenant {tenant_id}")
        data_service = DataService(tenant_id=tenant_id, email=email, db=db)
        alerts_data = await data_service.get_dashboard_alerts()
        
        # Step 4: Store in cache
        await set_cached(cache_key, alerts_data, ttl=get_ttl("dashboard_alerts"))
        
        # Step 5: Return
        return {"payload": alerts_data}
        
    except Exception as e:
        logger.error(f"Error fetching dashboard alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch alerts: {str(e)}")


@router.get("/trends")
async def get_dashboard_trends(
    request: Request,
    days: int = 30,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get sales trends over time
    Uses DataService to fetch from Mock API or Database
    WITH REDIS CACHING
    """
    try:
        tenant_id = str(get_tenant_id_from_request(request))
        email = get_user_email_from_request(request)
        
        # Step 1: Build cache key with days parameter
        cache_key = make_cache_key("dashboard_trends", tenant_id, days=days)
        
        # Step 2: Check cache
        cached_data = await get_cached(cache_key)
        if cached_data is not None:
            return {"payload": cached_data}
        
        # Step 3: Cache miss - fetch from DataService
        logger.info(f"Fetching dashboard trends from Mock API for tenant {tenant_id} (days={days})")
        data_service = DataService(tenant_id=tenant_id, email=email, db=db)
        trends = await data_service.get_dashboard_trends(days=days)
        
        # Step 4: Store in cache
        await set_cached(cache_key, trends, ttl=get_ttl("dashboard_trends"))
        
        # Step 5: Return
        return {"payload": trends}
        
    except Exception as e:
        logger.error(f"Error fetching dashboard trends: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch trends: {str(e)}")
