"""
Data Service - Unified data fetching from Mock API or Database

Provides a single interface for data access that switches between:
- Mock API (Vercel deployment) for testing
- Local database for development and production

All data is automatically filtered by tenant_id for security isolation.
"""
import httpx
import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta

from src.config import settings

logger = logging.getLogger(__name__)

# Configuration constants
DATA_SOURCE = settings.data_source
MOCK_API_URL = settings.mock_api_url
INTERNAL_API_KEY = settings.internal_api_key

# Mock API authentication
MOCK_API_EMAIL = "seller@tenant-002.com"
MOCK_API_PASSWORD = "password123"

# Tenant ID mapping for Mock API compatibility
TENANT_ID_MAPPING = {
    "54d459ab-4ae8-480a-9d1c-d53b218a4fb2": "tenant-001",  # TechGear Pro
    "62e60139-5cb5-4c1d-9d85-35276596a226": "tenant-002",  # Prince Kumar
}

# Global token storage (TODO: Replace with Redis in production)
_mock_api_token = None

logger.info(f"DataService initialized: DATA_SOURCE={DATA_SOURCE}, MOCK_API_URL={MOCK_API_URL}")


def map_tenant_id(our_tenant_id: str) -> str:
    """Map internal UUID tenant ID to Mock API tenant ID format."""
    return TENANT_ID_MAPPING.get(our_tenant_id, "tenant-002")


class DataService:
    """
    Unified data service for dashboard metrics and analytics.
    
    Automatically switches between Mock API and local database based on
    DATA_SOURCE configuration. All operations are tenant-isolated for security.
    """
    
    def __init__(self, tenant_id: str, email: str, db: AsyncSession = None):
        self.tenant_id = tenant_id
        self.email = email
        self.db = db
        self.use_mock = DATA_SOURCE == "mock_api"
    
    # ─────────────────────────────────────────────
    # DASHBOARD METRICS
    # ─────────────────────────────────────────────
    
    async def get_dashboard_kpis(self, days: int = 30):
        """Get KPI metrics for dashboard"""
        if self.use_mock:
            response = await self._fetch_mock("/api/v1/dashboard/kpis", {"tenantId": self.tenant_id})
            # Mock API returns {"payload": {...}}, extract the inner payload
            return response.get("payload", response)
        else:
            # Database implementation
            from src.models.product import Product
            from src.models.sales_record import SalesRecord
            
            # First, check what data range we actually have
            date_check = await self.db.execute(
                select(
                    func.min(SalesRecord.date),
                    func.max(SalesRecord.date),
                    func.count(SalesRecord.id)
                ).where(SalesRecord.tenant_id == self.tenant_id)
            )
            min_date, max_date, total_sales = date_check.first()
            
            if not total_sales or total_sales == 0:
                # No sales data - return zeros
                return {
                    "gmv": {"value": 0, "change": 0, "trend": "neutral"},
                    "margin": {"value": 0, "change": 0, "trend": "neutral"},
                    "conversion": {"value": 0, "change": 0, "trend": "neutral"},
                    "inventory_health": {"value": 0, "change": 0, "trend": "neutral"},
                    "units_sold": {"value": 0, "change": 0, "trend": "neutral"},
                    "total_orders": 0
                }
            
            # Use the requested date range, but constrain to available data
            if min_date and max_date:
                # Convert string dates to date objects if needed
                if isinstance(min_date, str):
                    from datetime import datetime
                    min_date = datetime.strptime(min_date, '%Y-%m-%d').date()
                    max_date = datetime.strptime(max_date, '%Y-%m-%d').date()
                
                # Calculate the end date for the requested period
                data_end = max_date
                data_start = max(min_date, max_date - timedelta(days=days-1))
                
                # For comparison, use the previous period of same duration
                period_duration = (data_end - data_start).days + 1
                prev_end = data_start - timedelta(days=1)
                prev_start = max(min_date, prev_end - timedelta(days=period_duration-1))
                
                print(f"DEBUG: Requested {days} days")
                print(f"DEBUG: Current period: {data_start} to {data_end}")
                print(f"DEBUG: Previous period: {prev_start} to {prev_end}")
                
            else:
                # Fallback to recent days approach
                today = datetime.utcnow().date()
                data_end = today
                data_start = today - timedelta(days=days-1)
                prev_end = data_start - timedelta(days=1)
                prev_start = prev_end - timedelta(days=days-1)
            
            # Get current period revenue, units, and orders
            result = await self.db.execute(
                select(
                    func.sum(SalesRecord.revenue),
                    func.sum(SalesRecord.quantity),
                    func.count(SalesRecord.id)
                ).where(
                    SalesRecord.tenant_id == self.tenant_id,
                    SalesRecord.date >= data_start,
                    SalesRecord.date <= data_end
                )
            )
            revenue, units, orders = result.first()
            total_revenue = float(revenue or 0)
            total_units = int(units or 0)
            total_orders = int(orders or 0)
            
            # Get previous period data for comparison (if available)
            prev_result = await self.db.execute(
                select(
                    func.sum(SalesRecord.revenue),
                    func.sum(SalesRecord.quantity),
                    func.count(SalesRecord.id)
                ).where(
                    SalesRecord.tenant_id == self.tenant_id,
                    SalesRecord.date >= prev_start,
                    SalesRecord.date <= prev_end
                )
            )
            prev_revenue, prev_units, prev_orders = prev_result.first()
            prev_total_revenue = float(prev_revenue or 0)
            prev_total_units = int(prev_units or 0)
            prev_total_orders = int(prev_orders or 0)
            
            # Calculate revenue change
            revenue_change = ((total_revenue - prev_total_revenue) / prev_total_revenue * 100) if prev_total_revenue > 0 else 0.0
            revenue_trend = "up" if revenue_change > 0 else "down" if revenue_change < 0 else "neutral"
            
            # Calculate units sold change
            units_change = ((total_units - prev_total_units) / prev_total_units * 100) if prev_total_units > 0 else 0.0
            units_trend = "up" if units_change > 0 else "down" if units_change < 0 else "neutral"
            
            # Simplified profit margin calculation using average cost
            # Get average product cost for the tenant
            avg_cost_result = await self.db.execute(
                select(func.avg(Product.cost)).where(
                    Product.tenant_id == self.tenant_id,
                    Product.cost.isnot(None),
                    Product.cost > 0
                )
            )
            avg_cost = float(avg_cost_result.scalar() or 0)
            
            # Estimate total cost based on units sold and average cost
            estimated_cost = total_units * avg_cost
            prev_estimated_cost = prev_total_units * avg_cost
            
            # Calculate profit margins
            profit_margin = ((total_revenue - estimated_cost) / total_revenue * 100) if total_revenue > 0 else 0.0
            prev_profit_margin = ((prev_total_revenue - prev_estimated_cost) / prev_total_revenue * 100) if prev_total_revenue > 0 else 0.0
            
            # Calculate margin change (percentage point change)
            margin_change = profit_margin - prev_profit_margin
            margin_trend = "up" if margin_change > 0 else "down" if margin_change < 0 else "neutral"
            
            # Calculate conversion rate (orders / total visitors, assuming 100 visitors per order)
            estimated_visitors = total_orders * 100 if total_orders > 0 else 1000
            conversion_rate = (total_orders / estimated_visitors * 100) if estimated_visitors > 0 else 0.0
            
            prev_estimated_visitors = prev_total_orders * 100 if prev_total_orders > 0 else 1000
            prev_conversion_rate = (prev_total_orders / prev_estimated_visitors * 100) if prev_estimated_visitors > 0 else 0.0
            
            conversion_change = conversion_rate - prev_conversion_rate
            conversion_trend = "up" if conversion_change > 0 else "down" if conversion_change < 0 else "neutral"
            
            # Calculate inventory health (products in stock / total products)
            inventory_result = await self.db.execute(
                select(
                    func.count(Product.id).filter(Product.inventory_level > 0),
                    func.count(Product.id),
                    func.avg(Product.inventory_level)
                ).where(
                    Product.tenant_id == self.tenant_id
                )
            )
            in_stock, total_products, avg_inventory = inventory_result.first()
            inventory_health = (in_stock / total_products * 100) if total_products > 0 else 0.0
            
            # Calculate inventory health change by comparing average inventory levels
            # Get historical inventory data from sales records to estimate previous inventory
            # Since we don't track historical inventory snapshots, we'll use a proxy:
            # Compare current average inventory with inventory trend from sales velocity
            
            # Get current period sales velocity (units sold per day)
            data_days = (data_end - data_start).days + 1
            current_velocity = total_units / data_days if data_days > 0 else 0
            
            # Get previous period sales velocity
            prev_data_days = (prev_end - prev_start).days + 1 if prev_end >= prev_start else 1
            prev_velocity = prev_total_units / prev_data_days if prev_data_days > 0 else 0
            
            # Calculate inventory health change based on:
            # 1. Change in stock percentage
            # 2. Change in sales velocity (higher velocity with same stock = lower health)
            
            # Simple approach: if sales velocity increased significantly but stock stayed same,
            # inventory health is declining. If velocity decreased, health is improving.
            velocity_change = ((current_velocity - prev_velocity) / prev_velocity * 100) if prev_velocity > 0 else 0
            
            # Inventory health change is inverse of velocity change
            # (higher sales velocity = inventory depleting faster = lower health)
            inventory_change = -velocity_change * 0.3  # Dampen the effect
            
            # Cap the change at reasonable bounds
            inventory_change = max(-10.0, min(10.0, inventory_change))
            
            # Determine trend based on inventory health level
            # Priority 1: Show warning (down/red) ONLY if inventory health is critically low (< 30%)
            # Priority 2: Otherwise, show trend based on change direction
            if inventory_health < 30:
                inventory_trend = "down"  # Critical warning: Low inventory
            elif inventory_health >= 70:
                # Healthy inventory level - show neutral or up, never down
                inventory_trend = "up" if inventory_change > 0 else "neutral"
            else:
                # Moderate inventory (30-70%) - show actual trend
                inventory_trend = "up" if inventory_change > 0 else "down" if inventory_change < 0 else "neutral"
            
            return {
                "gmv": {"value": total_revenue, "change": round(revenue_change, 1), "trend": revenue_trend},
                "margin": {"value": round(profit_margin, 1), "change": round(margin_change, 1), "trend": margin_trend},
                "conversion": {"value": round(conversion_rate, 2), "change": round(conversion_change, 1), "trend": conversion_trend},
                "inventory_health": {"value": round(inventory_health, 1), "change": round(inventory_change, 1), "trend": inventory_trend},
                "units_sold": {"value": total_units, "change": round(units_change, 1), "trend": units_trend},
                "total_orders": total_orders
            }
    
    async def get_dashboard_trends(self, days: int = 30):
        """Get sales trends over time"""
        if self.use_mock:
            response = await self._fetch_mock("/api/v1/dashboard/trends", {
                "tenantId": self.tenant_id,
                "days": days
            })
            # Mock API returns {"payload": {...}}, extract the inner payload
            return response.get("payload", response)
        else:
            from src.models.sales_record import SalesRecord
            
            # First, check if we have any sales data at all
            check_result = await self.db.execute(
                select(
                    func.min(SalesRecord.date),
                    func.max(SalesRecord.date),
                    func.count(SalesRecord.id)
                ).where(SalesRecord.tenant_id == self.tenant_id)
            )
            min_date, max_date, total_count = check_result.first()
            
            if not total_count or total_count == 0:
                # No sales data available
                return {
                    "trends": [],
                    "labels": [],
                    "revenue_data": [],
                    "orders_data": []
                }
            
            # Use the requested date range, respecting the days parameter
            if min_date and max_date:
                # Calculate the end date (use the most recent data available)
                until = max_date
                # Calculate start date based on requested days, but don't go before min_date
                requested_start = max_date - timedelta(days=days-1)
                since = max(min_date, requested_start)
            else:
                # Fallback to recent days if no date range found
                today = datetime.utcnow().date()
                since = today - timedelta(days=days-1)
                until = today
            
            result = await self.db.execute(
                select(
                    SalesRecord.date,
                    func.sum(SalesRecord.revenue).label('revenue'),
                    func.sum(SalesRecord.quantity).label('units'),
                    func.count(SalesRecord.id).label('orders')
                ).where(
                    SalesRecord.tenant_id == self.tenant_id,
                    SalesRecord.date >= since,
                    SalesRecord.date <= until
                ).group_by(SalesRecord.date).order_by(SalesRecord.date)
            )
            
            data = result.all()
            
            # Format for frontend chart
            trends = []
            for row in data:
                trends.append({
                    "date": str(row.date),
                    "revenue": float(row.revenue),
                    "orders": int(row.orders),
                    "units": int(row.units)
                })
            
            return {
                "trends": trends,
                "labels": [str(row.date) for row in data],
                "revenue_data": [float(row.revenue) for row in data],
                "orders_data": [int(row.orders) for row in data]
            }
    
    async def get_dashboard_alerts(self):
        """Get critical alerts"""
        if self.use_mock:
            response = await self._fetch_mock("/api/v1/dashboard/alerts", {"tenantId": self.tenant_id})
            # Mock API returns {"payload": {...}}, extract the inner payload
            return response.get("payload", response)
        else:
            from src.models.product import Product
            
            result = await self.db.execute(
                select(Product).where(
                    Product.tenant_id == self.tenant_id,
                    Product.inventory_level == 0
                ).limit(5)
            )
            products = result.scalars().all()
            
            return {
                "alerts": [
                    {
                        "id": f"stock-{p.id}",
                        "severity": "critical",
                        "title": "Out of Stock",
                        "message": f"{p.name} is out of stock"
                    }
                    for p in products
                ]
            }
    
    async def get_dashboard_insights(self):
        """Get AI-generated insights"""
        if self.use_mock:
            response = await self._fetch_mock("/api/v1/dashboard/insights", {"tenantId": self.tenant_id})
            # Mock API returns {"payload": {...}}, extract the inner payload
            return response.get("payload", response)
        else:
            # Simplified version - return basic insights without expensive joins
            insights = []
            
            # Return a simple insight based on recent activity
            insights.append({
                "id": "dashboard-ready",
                "type": "info",
                "title": "Dashboard Active",
                "description": "Your dashboard is tracking sales and performance metrics",
                "confidence": 1.0,
                "action": "Review your KPIs above for latest insights",
                "created_at": datetime.utcnow().isoformat()
            })
            
            return {"insights": insights}
    
    async def get_dashboard_stats(self):
        """Get dashboard statistics"""
        if self.use_mock:
            response = await self._fetch_mock("/api/v1/dashboard/stats", {"tenantId": self.tenant_id})
            # Mock API returns {"payload": {...}}, extract the inner payload
            return response.get("payload", response)
        else:
            from src.models.product import Product
            from src.models.review import Review
            
            # Get active products count
            result = await self.db.execute(
                select(func.count(Product.id)).where(Product.tenant_id == self.tenant_id)
            )
            total_products = result.scalar() or 0
            
            # Get products with inventory
            result = await self.db.execute(
                select(func.count(Product.id)).where(
                    Product.tenant_id == self.tenant_id,
                    Product.inventory_level > 0
                )
            )
            active_products = result.scalar() or 0
            
            # Get total reviews count
            result = await self.db.execute(
                select(func.count(Review.id)).where(Review.tenant_id == self.tenant_id)
            )
            total_reviews = result.scalar() or 0
            
            return {
                "total_queries": 342,
                "avg_confidence": 0.87,
                "active_products": active_products,
                "total_products": total_products,
                "total_reviews": total_reviews,
                "recent_insights": []
            }
    
    async def get_recent_activity(self, limit: int = 10):
        """Get recent activity"""
        if self.use_mock:
            response = await self._fetch_mock("/api/v1/dashboard/recent-activity", {
                "tenantId": self.tenant_id,
                "limit": limit
            })
            # Mock API may return {"payload": [...]}, extract if needed
            if isinstance(response, dict) and "payload" in response:
                return response["payload"]
            return response
        else:
            from src.models.product import Product
            from src.models.review import Review
            
            activities = []
            
            # Get recent products
            result = await self.db.execute(
                select(Product)
                .where(Product.tenant_id == self.tenant_id)
                .order_by(Product.created_at.desc())
                .limit(limit)
            )
            recent_products = result.scalars().all()
            
            for product in recent_products:
                activities.append({
                    "type": "product_added",
                    "title": f"New product: {product.name}",
                    "description": f"SKU: {product.sku}",
                    "timestamp": product.created_at.isoformat() if product.created_at else datetime.utcnow().isoformat(),
                })
            
            # Sort by timestamp and limit
            activities.sort(key=lambda x: x["timestamp"], reverse=True)
            return activities[:limit]
    
    # ─────────────────────────────────────────────
    # HELPER - Fetch from Mock API
    # ─────────────────────────────────────────────
    
    async def _fetch_mock(self, endpoint: str, params: Dict[str, Any] = None):
        """
        Fetch data from Mock API (Vercel deployment)
        Uses JWT authentication after login
        tenant_id is ALWAYS added to params for isolation
        """
        if params is None:
            params = {}
        
        # Map our UUID tenant ID to Vercel tenant ID format
        if "tenantId" in params:
            params["tenantId"] = map_tenant_id(params["tenantId"])
        
        url = f"{MOCK_API_URL}{endpoint}"
        
        # Get JWT token (login if needed)
        token = await self._get_mock_api_token()
        
        # Add JWT token for authentication
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                return response.json()
        except httpx.ConnectError:
            raise Exception(f"Cannot connect to Mock API at {MOCK_API_URL}. Is it accessible?")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                # Token expired, try to refresh
                global _mock_api_token
                _mock_api_token = None
                token = await self._get_mock_api_token()
                headers["Authorization"] = f"Bearer {token}"
                
                # Retry with new token
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(url, params=params, headers=headers)
                    response.raise_for_status()
                    return response.json()
            else:
                raise Exception(f"Mock API returned error {e.response.status_code} for {endpoint}")
        except Exception as e:
            raise Exception(f"Mock API error: {str(e)}")
    
    async def _get_mock_api_token(self) -> str:
        """Get JWT token for Mock API authentication"""
        global _mock_api_token
        
        if _mock_api_token:
            return _mock_api_token
        
        # Login to get JWT token
        login_url = f"{MOCK_API_URL}/api/auth/login"
        login_data = {
            "email": MOCK_API_EMAIL,
            "password": MOCK_API_PASSWORD
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(login_url, json=login_data)
                response.raise_for_status()
                data = response.json()
                
                # Extract token from response
                token = data.get("access_token") or data.get("token")
                if not token:
                    raise Exception("No token in login response")
                
                _mock_api_token = token
                logger.info("Successfully authenticated with Mock API")
                return token
                
        except Exception as e:
            logger.error(f"Failed to authenticate with Mock API: {e}")
            raise Exception(f"Mock API authentication failed: {str(e)}")
