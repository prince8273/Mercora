"""API endpoints for generating intelligent insights"""
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from pydantic import BaseModel

from src.database import get_db
from src.models.product import Product
from src.models.review import Review

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/insights", tags=["insights"])


class Insight(BaseModel):
    """Single insight model"""
    type: str  # warning, info, success, error
    title: str
    description: str
    timestamp: datetime
    priority: int  # 1-5, 5 being highest
    metadata: Dict[str, Any] = {}


class InsightsResponse(BaseModel):
    """Response containing multiple insights"""
    insights: List[Insight]
    total_count: int
    generated_at: datetime


@router.get("/generate", response_model=InsightsResponse)
async def generate_insights(
    tenant_id: str = None,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate intelligent insights from current data.
    
    Analyzes:
    - Inventory levels
    - Review coverage
    - Customer engagement
    - Sentiment trends
    - Pricing anomalies
    """
    try:
        insights = []
        
        # Get tenant (use first if not specified)
        if not tenant_id:
            from src.models.tenant import Tenant
            result = await db.execute(select(Tenant).limit(1))
            tenant = result.scalar_one_or_none()
            if tenant:
                tenant_id = str(tenant.id)
        
        if not tenant_id:
            return InsightsResponse(
                insights=[],
                total_count=0,
                generated_at=datetime.utcnow()
            )
        
        # Insight 1: Low Inventory Alert
        result = await db.execute(
            select(Product.sku, Product.name, Product.inventory_level)
            .where(
                and_(
                    Product.tenant_id == tenant_id,
                    Product.inventory_level < 20
                )
            )
            .order_by(Product.inventory_level.asc())
        )
        low_inventory_products = result.all()
        low_inventory_count = len(low_inventory_products)
        
        if low_inventory_count > 0:
            products_list = [
                {
                    "sku": p.sku,
                    "name": p.name,
                    "inventory_level": p.inventory_level
                }
                for p in low_inventory_products
            ]
            
            insights.append(Insight(
                type="warning",
                title="Low Inventory Alert",
                description=f"{low_inventory_count} product{'s' if low_inventory_count != 1 else ''} {'have' if low_inventory_count != 1 else 'has'} low inventory levels",
                timestamp=datetime.utcnow(),
                priority=5,
                metadata={
                    "count": low_inventory_count,
                    "threshold": 20,
                    "products": products_list
                }
            ))
        
        # Insight 2: Products Without Reviews
        result = await db.execute(
            select(Product.sku, Product.name)
            .outerjoin(Review, Product.id == Review.product_id)
            .where(
                and_(
                    Product.tenant_id == tenant_id,
                    Review.id == None
                )
            )
        )
        products_without_reviews = result.all()
        no_review_count = len(products_without_reviews)
        
        if no_review_count > 0:
            products_list = [
                {
                    "sku": p.sku,
                    "name": p.name
                }
                for p in products_without_reviews
            ]
            
            insights.append(Insight(
                type="info",
                title="Products Need Reviews",
                description=f"{no_review_count} product{'s' if no_review_count != 1 else ''} {'have' if no_review_count != 1 else 'has'} no customer reviews",
                timestamp=datetime.utcnow(),
                priority=3,
                metadata={
                    "count": no_review_count,
                    "products": products_list
                }
            ))
        
        # Insight 3: Customer Engagement
        result = await db.execute(
            select(
                func.count(Review.id).label('review_count'),
                func.count(func.distinct(Review.product_id)).label('product_count')
            )
            .where(Review.tenant_id == tenant_id)
        )
        engagement_data = result.first()
        
        if engagement_data and engagement_data.product_count > 0:
            avg_reviews = engagement_data.review_count / engagement_data.product_count
            
            if avg_reviews >= 10:
                insights.append(Insight(
                    type="success",
                    title="Strong Customer Engagement",
                    description=f"Average of {avg_reviews:.1f} reviews per product",
                    timestamp=datetime.utcnow(),
                    priority=2,
                    metadata={"average_reviews": round(avg_reviews, 1)}
                ))
            elif avg_reviews < 5:
                insights.append(Insight(
                    type="warning",
                    title="Low Customer Engagement",
                    description=f"Only {avg_reviews:.1f} reviews per product on average",
                    timestamp=datetime.utcnow(),
                    priority=4,
                    metadata={"average_reviews": round(avg_reviews, 1)}
                ))
        
        # Insight 4: Sentiment Analysis
        result = await db.execute(
            select(
                Review.sentiment,
                func.count(Review.id).label('count')
            )
            .where(Review.tenant_id == tenant_id)
            .group_by(Review.sentiment)
        )
        sentiment_data = result.all()
        
        if sentiment_data:
            sentiment_dict = {row.sentiment: row.count for row in sentiment_data}
            total_reviews = sum(sentiment_dict.values())
            
            if total_reviews > 0:
                negative_pct = (sentiment_dict.get('negative', 0) / total_reviews) * 100
                positive_pct = (sentiment_dict.get('positive', 0) / total_reviews) * 100
                
                if negative_pct > 30:
                    insights.append(Insight(
                        type="error",
                        title="High Negative Sentiment",
                        description=f"{negative_pct:.1f}% of reviews are negative",
                        timestamp=datetime.utcnow(),
                        priority=5,
                        metadata={
                            "negative_percentage": round(negative_pct, 1),
                            "negative_count": sentiment_dict.get('negative', 0)
                        }
                    ))
                elif positive_pct > 70:
                    insights.append(Insight(
                        type="success",
                        title="Excellent Customer Satisfaction",
                        description=f"{positive_pct:.1f}% of reviews are positive",
                        timestamp=datetime.utcnow(),
                        priority=1,
                        metadata={
                            "positive_percentage": round(positive_pct, 1),
                            "positive_count": sentiment_dict.get('positive', 0)
                        }
                    ))
        
        # Insight 5: New Products
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        result = await db.execute(
            select(Product.sku, Product.name, Product.created_at)
            .where(
                and_(
                    Product.tenant_id == tenant_id,
                    Product.created_at >= thirty_days_ago
                )
            )
            .order_by(Product.created_at.desc())
        )
        new_products = result.all()
        new_products_count = len(new_products)
        
        if new_products_count > 0:
            products_list = [
                {
                    "sku": p.sku,
                    "name": p.name,
                    "created_at": p.created_at.isoformat()
                }
                for p in new_products
            ]
            
            insights.append(Insight(
                type="info",
                title="New Products Added",
                description=f"{new_products_count} new product{'s' if new_products_count != 1 else ''} added in the last 30 days",
                timestamp=datetime.utcnow(),
                priority=2,
                metadata={
                    "count": new_products_count,
                    "period_days": 30,
                    "products": products_list
                }
            ))
        
        # Insight 6: Price Range Analysis
        result = await db.execute(
            select(
                func.min(Product.price).label('min_price'),
                func.max(Product.price).label('max_price'),
                func.avg(Product.price).label('avg_price')
            )
            .where(Product.tenant_id == tenant_id)
        )
        price_data = result.first()
        
        if price_data and price_data.max_price:
            price_range = float(price_data.max_price) - float(price_data.min_price)
            if price_range > 1000:
                insights.append(Insight(
                    type="info",
                    title="Wide Price Range",
                    description=f"Products range from ${price_data.min_price:.2f} to ${price_data.max_price:.2f}",
                    timestamp=datetime.utcnow(),
                    priority=1,
                    metadata={
                        "min_price": float(price_data.min_price),
                        "max_price": float(price_data.max_price),
                        "avg_price": float(price_data.avg_price)
                    }
                ))
        
        # Insight 7: Category Distribution
        result = await db.execute(
            select(
                Product.category,
                func.count(Product.id).label('count')
            )
            .where(Product.tenant_id == tenant_id)
            .group_by(Product.category)
            .order_by(func.count(Product.id).desc())
            .limit(1)
        )
        top_category = result.first()
        
        if top_category:
            insights.append(Insight(
                type="info",
                title="Top Product Category",
                description=f"{top_category.category} has {top_category.count} products",
                timestamp=datetime.utcnow(),
                priority=1,
                metadata={
                    "category": top_category.category,
                    "count": top_category.count
                }
            ))
        
        # Sort insights by priority (highest first)
        insights.sort(key=lambda x: x.priority, reverse=True)
        
        # Limit results
        insights = insights[:limit]
        
        return InsightsResponse(
            insights=insights,
            total_count=len(insights),
            generated_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Failed to generate insights: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate insights: {str(e)}")


@router.get("/summary")
async def get_insights_summary(
    tenant_id: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Get a quick summary of key metrics for insights"""
    try:
        # Get tenant
        if not tenant_id:
            from src.models.tenant import Tenant
            result = await db.execute(select(Tenant).limit(1))
            tenant = result.scalar_one_or_none()
            if tenant:
                tenant_id = str(tenant.id)
        
        if not tenant_id:
            return {
                "total_products": 0,
                "total_reviews": 0,
                "avg_rating": 0,
                "low_inventory_count": 0
            }
        
        # Get metrics
        result = await db.execute(
            select(func.count(Product.id))
            .where(Product.tenant_id == tenant_id)
        )
        total_products = result.scalar() or 0
        
        result = await db.execute(
            select(func.count(Review.id))
            .where(Review.tenant_id == tenant_id)
        )
        total_reviews = result.scalar() or 0
        
        result = await db.execute(
            select(func.avg(Review.rating))
            .where(Review.tenant_id == tenant_id)
        )
        avg_rating = result.scalar() or 0
        
        result = await db.execute(
            select(func.count(Product.id))
            .where(
                and_(
                    Product.tenant_id == tenant_id,
                    Product.inventory_level < 20
                )
            )
        )
        low_inventory_count = result.scalar() or 0
        
        return {
            "total_products": total_products,
            "total_reviews": total_reviews,
            "avg_rating": round(float(avg_rating), 2) if avg_rating else 0,
            "low_inventory_count": low_inventory_count
        }
        
    except Exception as e:
        logger.error(f"Failed to get insights summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
