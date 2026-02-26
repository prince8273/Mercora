"""Competitor Price Dashboard API endpoints"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from decimal import Decimal

from src.database import get_db
from src.models.product import Product
from src.models.user import User
from src.auth.dependencies import get_current_active_user, get_tenant_id

router = APIRouter(prefix="/competitor-dashboard", tags=["competitor-dashboard"])


class CompetitorPrice(BaseModel):
    """Competitor price information"""
    competitor_name: str
    price: float
    currency: str
    last_updated: datetime
    price_change_7d: Optional[float] = None
    price_change_30d: Optional[float] = None
    is_on_sale: bool = False
    original_price: Optional[float] = None


class ProductPriceComparison(BaseModel):
    """Price comparison for a single product"""
    product_id: str
    sku: str
    name: str
    our_price: float
    currency: str
    competitor_prices: List[CompetitorPrice]
    min_competitor_price: float
    max_competitor_price: float
    avg_competitor_price: float
    price_position: str  # "lowest", "competitive", "highest"
    price_gap_percentage: float
    recommendation: str


class PriceAlert(BaseModel):
    """Price alert for significant changes"""
    product_id: str
    sku: str
    name: str
    alert_type: str  # "price_drop", "price_increase", "underpriced", "overpriced"
    severity: str  # "low", "medium", "high"
    message: str
    current_price: float
    competitor_avg: float
    created_at: datetime


class MarketOverview(BaseModel):
    """Market overview statistics"""
    total_products_tracked: int
    products_competitively_priced: int
    products_underpriced: int
    products_overpriced: int
    avg_price_gap: float
    total_potential_revenue_gain: float
    active_competitor_promotions: int


class DashboardResponse(BaseModel):
    """Complete dashboard response"""
    market_overview: MarketOverview
    price_comparisons: List[ProductPriceComparison]
    price_alerts: List[PriceAlert]
    top_opportunities: List[ProductPriceComparison]
    generated_at: datetime


@router.get("/overview", response_model=DashboardResponse)
async def get_competitor_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    tenant_id: UUID = Depends(get_tenant_id),
    limit: int = Query(default=20, le=100),
    category: Optional[str] = None
) -> DashboardResponse:
    """
    Get comprehensive competitor price dashboard data (TENANT-ISOLATED).
    
    Args:
        db: Database session
        current_user: Authenticated user
        tenant_id: Tenant ID from JWT token
        limit: Maximum number of products to return
        category: Optional category filter
        
    Returns:
        Complete dashboard with market overview, comparisons, and alerts
    """
    # Fetch our products (TENANT-FILTERED)
    query = select(Product).where(Product.tenant_id == tenant_id)
    
    if category:
        query = query.where(Product.category == category)
    
    query = query.limit(limit)
    result = await db.execute(query)
    products = result.scalars().all()
    
    # Generate mock competitor data for each product
    price_comparisons = []
    price_alerts = []
    
    total_products = len(products)
    products_competitive = 0
    products_underpriced = 0
    products_overpriced = 0
    total_price_gap = 0.0
    total_revenue_gain = 0.0
    active_promotions = 0
    
    for product in products:
        # Generate mock competitor prices
        competitor_prices = _generate_mock_competitor_prices(product)
        
        # Calculate statistics
        competitor_price_values = [cp.price for cp in competitor_prices]
        min_price = min(competitor_price_values)
        max_price = max(competitor_price_values)
        avg_price = sum(competitor_price_values) / len(competitor_price_values)
        
        our_price = float(product.price)
        price_gap = ((our_price - avg_price) / avg_price) * 100
        total_price_gap += abs(price_gap)
        
        # Determine price position
        if our_price <= min_price:
            price_position = "lowest"
            products_underpriced += 1
        elif our_price >= max_price:
            price_position = "highest"
            products_overpriced += 1
        else:
            price_position = "competitive"
            products_competitive += 1
        
        # Generate recommendation
        recommendation = _generate_price_recommendation(
            our_price, avg_price, min_price, max_price, price_position
        )
        
        # Calculate potential revenue gain
        if price_position == "underpriced" and our_price < avg_price:
            potential_gain = (avg_price - our_price) * 0.8  # Conservative estimate
            total_revenue_gain += potential_gain
        
        # Count promotions
        active_promotions += sum(1 for cp in competitor_prices if cp.is_on_sale)
        
        comparison = ProductPriceComparison(
            product_id=str(product.id),
            sku=product.sku,
            name=product.name,
            our_price=our_price,
            currency=product.currency,
            competitor_prices=competitor_prices,
            min_competitor_price=min_price,
            max_competitor_price=max_price,
            avg_competitor_price=avg_price,
            price_position=price_position,
            price_gap_percentage=price_gap,
            recommendation=recommendation
        )
        price_comparisons.append(comparison)
        
        # Generate alerts for significant price gaps
        alert = _generate_price_alert(product, our_price, avg_price, price_position, price_gap)
        if alert:
            price_alerts.append(alert)
    
    # Calculate market overview
    avg_price_gap = total_price_gap / total_products if total_products > 0 else 0.0
    
    market_overview = MarketOverview(
        total_products_tracked=total_products,
        products_competitively_priced=products_competitive,
        products_underpriced=products_underpriced,
        products_overpriced=products_overpriced,
        avg_price_gap=round(avg_price_gap, 2),
        total_potential_revenue_gain=round(total_revenue_gain, 2),
        active_competitor_promotions=active_promotions
    )
    
    # Sort by price gap to find top opportunities
    top_opportunities = sorted(
        [pc for pc in price_comparisons if pc.price_position == "underpriced"],
        key=lambda x: abs(x.price_gap_percentage),
        reverse=True
    )[:5]
    
    # Sort alerts by severity
    severity_order = {"high": 0, "medium": 1, "low": 2}
    price_alerts.sort(key=lambda x: severity_order.get(x.severity, 3))
    
    return DashboardResponse(
        market_overview=market_overview,
        price_comparisons=price_comparisons,
        price_alerts=price_alerts[:10],  # Top 10 alerts
        top_opportunities=top_opportunities,
        generated_at=datetime.utcnow()
    )


def _generate_mock_competitor_prices(product: Product) -> List[CompetitorPrice]:
    """Generate mock competitor prices for demonstration"""
    import random
    
    base_price = float(product.price)
    competitors = ["Amazon", "Walmart", "Target", "Best Buy", "eBay"]
    
    competitor_prices = []
    for competitor in competitors:
        # Generate price variation (-20% to +30%)
        variation = random.uniform(-0.20, 0.30)
        price = base_price * (1 + variation)
        
        # Random price changes
        price_change_7d = random.uniform(-5, 5) if random.random() > 0.3 else None
        price_change_30d = random.uniform(-10, 10) if random.random() > 0.3 else None
        
        # Random promotions
        is_on_sale = random.random() > 0.7
        original_price = price * 1.15 if is_on_sale else None
        
        competitor_prices.append(CompetitorPrice(
            competitor_name=competitor,
            price=round(price, 2),
            currency=product.currency,
            last_updated=datetime.utcnow() - timedelta(hours=random.randint(1, 24)),
            price_change_7d=round(price_change_7d, 2) if price_change_7d else None,
            price_change_30d=round(price_change_30d, 2) if price_change_30d else None,
            is_on_sale=is_on_sale,
            original_price=round(original_price, 2) if original_price else None
        ))
    
    return competitor_prices


def _generate_price_recommendation(
    our_price: float,
    avg_price: float,
    min_price: float,
    max_price: float,
    price_position: str
) -> str:
    """Generate pricing recommendation"""
    if price_position == "underpriced":
        suggested_price = (avg_price + our_price) / 2
        return f"Consider increasing price to ${suggested_price:.2f} (closer to market average)"
    elif price_position == "overpriced":
        suggested_price = (avg_price + our_price) / 2
        return f"Consider decreasing price to ${suggested_price:.2f} to be more competitive"
    else:
        return "Price is competitive - maintain current pricing"


def _generate_price_alert(
    product: Product,
    our_price: float,
    avg_price: float,
    price_position: str,
    price_gap: float
) -> Optional[PriceAlert]:
    """Generate price alert if significant gap exists"""
    if abs(price_gap) < 10:
        return None  # No alert for small gaps
    
    if price_position == "underpriced" and price_gap < -15:
        return PriceAlert(
            product_id=str(product.id),
            sku=product.sku,
            name=product.name,
            alert_type="underpriced",
            severity="high",
            message=f"Significantly underpriced by {abs(price_gap):.1f}% - potential revenue loss",
            current_price=our_price,
            competitor_avg=avg_price,
            created_at=datetime.utcnow()
        )
    elif price_position == "overpriced" and price_gap > 15:
        return PriceAlert(
            product_id=str(product.id),
            sku=product.sku,
            name=product.name,
            alert_type="overpriced",
            severity="high",
            message=f"Significantly overpriced by {price_gap:.1f}% - may lose sales",
            current_price=our_price,
            competitor_avg=avg_price,
            created_at=datetime.utcnow()
        )
    elif abs(price_gap) > 10:
        return PriceAlert(
            product_id=str(product.id),
            sku=product.sku,
            name=product.name,
            alert_type="price_gap",
            severity="medium",
            message=f"Price gap of {price_gap:.1f}% detected",
            current_price=our_price,
            competitor_avg=avg_price,
            created_at=datetime.utcnow()
        )
    
    return None


@router.get("/categories")
async def get_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    tenant_id: UUID = Depends(get_tenant_id)
) -> List[str]:
    """Get list of product categories for filtering (TENANT-ISOLATED)"""
    result = await db.execute(
        select(Product.category)
        .where(Product.tenant_id == tenant_id)
        .distinct()
    )
    categories = [row[0] for row in result.all() if row[0]]
    return sorted(categories)
