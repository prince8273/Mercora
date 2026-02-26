"""Analytics API endpoints"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models.product import Product
from src.models.review import Review

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("")
async def get_analytics(
    time_range: str = Query("7d", regex="^(24h|7d|30d|90d)$"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get analytics data including:
    - Query volume over time
    - Response time metrics
    - Top queries
    - System metrics
    """
    try:
        # Parse time range
        time_ranges = {
            "24h": timedelta(hours=24),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30),
            "90d": timedelta(days=90),
        }
        delta = time_ranges.get(time_range, timedelta(days=7))
        start_date = datetime.utcnow() - delta
        
        # Generate query volume data (mock for now - would come from query_history table)
        query_volume = _generate_query_volume(start_date, time_range)
        
        # Generate response time data (mock for now)
        response_time = _generate_response_time(start_date, time_range)
        
        # Get top queries (mock for now - would come from query_history table)
        top_queries = [
            {"query": "revenue trends", "count": 89},
            {"query": "customer churn", "count": 67},
            {"query": "product performance", "count": 54},
            {"query": "inventory status", "count": 43},
            {"query": "sales forecast", "count": 38},
        ]
        
        # Get real system metrics from database
        from sqlalchemy import select
        
        # Total products
        result = await db.execute(select(func.count(Product.id)))
        total_products = result.scalar() or 0
        
        # Total reviews
        result = await db.execute(select(func.count(Review.id)))
        total_reviews = result.scalar() or 0
        
        # Products with reviews
        result = await db.execute(
            select(func.count(func.distinct(Review.product_id)))
        )
        products_with_reviews = result.scalar() or 0
        
        # Calculate metrics
        review_coverage = (products_with_reviews / total_products * 100) if total_products > 0 else 0
        avg_reviews_per_product = (total_reviews / total_products) if total_products > 0 else 0
        
        return {
            "query_volume": query_volume,
            "response_time": response_time,
            "top_queries": top_queries,
            "system_metrics": {
                "cache_hit_rate": 78.5,  # Mock - would come from cache layer
                "avg_confidence_score": 0.87,  # Mock - would come from query_history
                "active_users_24h": 142,  # Mock - would come from auth/session tracking
                "error_rate": 0.3,  # Mock - would come from error logging
                "total_products": total_products,
                "total_reviews": total_reviews,
                "review_coverage": round(review_coverage, 1),
                "avg_reviews_per_product": round(avg_reviews_per_product, 1),
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch analytics: {str(e)}")


def _generate_query_volume(start_date: datetime, time_range: str) -> List[Dict[str, Any]]:
    """Generate mock query volume data"""
    data = []
    
    if time_range == "24h":
        # Hourly data for last 24 hours
        for i in range(24):
            date = start_date + timedelta(hours=i)
            count = 40 + (i % 12) * 3 + (i % 5) * 2  # Simulate variation
            data.append({
                "date": date.strftime("%Y-%m-%d %H:00"),
                "count": count
            })
    else:
        # Daily data
        days = {"7d": 7, "30d": 30, "90d": 90}.get(time_range, 7)
        for i in range(days):
            date = start_date + timedelta(days=i)
            # Simulate weekly pattern with some randomness
            base = 45
            weekly_variation = 10 if date.weekday() < 5 else -5  # Higher on weekdays
            count = base + weekly_variation + (i % 7) * 2
            data.append({
                "date": date.strftime("%Y-%m-%d"),
                "count": count
            })
    
    return data


def _generate_response_time(start_date: datetime, time_range: str) -> List[Dict[str, Any]]:
    """Generate mock response time data"""
    data = []
    
    if time_range == "24h":
        # Hourly data for last 24 hours
        for i in range(24):
            date = start_date + timedelta(hours=i)
            avg = 2.0 + (i % 6) * 0.1  # Simulate variation
            p95 = avg * 1.8
            data.append({
                "date": date.strftime("%Y-%m-%d %H:00"),
                "avg": round(avg, 2),
                "p95": round(p95, 2)
            })
    else:
        # Daily data
        days = {"7d": 7, "30d": 30, "90d": 90}.get(time_range, 7)
        for i in range(days):
            date = start_date + timedelta(days=i)
            avg = 2.2 + (i % 5) * 0.1
            p95 = avg * 1.8
            data.append({
                "date": date.strftime("%Y-%m-%d"),
                "avg": round(avg, 2),
                "p95": round(p95, 2)
            })
    
    return data


@router.get("/product-performance")
async def get_product_performance(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get top performing products based on reviews and ratings"""
    try:
        from sqlalchemy import select
        
        # Get products with their review stats
        result = await db.execute(
            select(
                Product.id,
                Product.name,
                Product.sku,
                Product.price,
                func.count(Review.id).label("review_count"),
                func.avg(Review.rating).label("avg_rating")
            )
            .outerjoin(Review, Product.id == Review.product_id)
            .group_by(Product.id, Product.name, Product.sku, Product.price)
            .order_by(desc("avg_rating"), desc("review_count"))
            .limit(limit)
        )
        
        products = []
        for row in result:
            products.append({
                "product_id": str(row.id),
                "name": row.name,
                "sku": row.sku,
                "price": float(row.price),
                "review_count": row.review_count or 0,
                "avg_rating": round(float(row.avg_rating), 2) if row.avg_rating else 0.0,
            })
        
        return products
        
    except Exception as e:
        logger.error(f"Error fetching product performance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch product performance: {str(e)}")
