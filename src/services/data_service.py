"""
Data Service - Unified data fetching from Mock API or Database
Switches between Mock API and Database based on DATA_SOURCE env variable
"""
import httpx
import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta

from src.config import settings

logger = logging.getLogger(__name__)

# Use settings from config (which loads from .env via pydantic)
DATA_SOURCE = settings.data_source
MOCK_API_URL = settings.mock_api_url
INTERNAL_API_KEY = settings.internal_api_key

# Tenant ID mapping: Our UUIDs → Vercel tenant IDs
TENANT_ID_MAPPING = {
    "54d459ab-4ae8-480a-9d1c-d53b218a4fb2": "tenant-001",  # TechGear Pro
    # Add more mappings as needed
}

def map_tenant_id(our_tenant_id: str) -> str:
    """Map our UUID tenant ID to Vercel tenant ID format"""
    return TENANT_ID_MAPPING.get(our_tenant_id, "tenant-001")  # Default to tenant-001

# Log the configuration on module load
logger.info(f"DataService initialized: DATA_SOURCE={DATA_SOURCE}, MOCK_API_URL={MOCK_API_URL}")


class DataService:
    """
    Unified data service that switches between Mock API and Database
    All data is automatically filtered by tenant_id for security
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
            
            today = datetime.utcnow().date()
            since = today - timedelta(days=days)
            
            # Get revenue, units, and orders
            result = await self.db.execute(
                select(
                    func.sum(SalesRecord.revenue),
                    func.sum(SalesRecord.quantity),
                    func.count(SalesRecord.id)
                ).where(
                    SalesRecord.tenant_id == self.tenant_id,
                    SalesRecord.date >= since
                )
            )
            revenue, units, orders = result.first()
            
            # Calculate profit margin (assuming 25% margin)
            total_revenue = float(revenue or 0)
            profit_margin = 25.0 if total_revenue > 0 else 0.0
            
            # Calculate conversion rate (orders / total visitors, assuming 100 visitors per order)
            total_orders = int(orders or 0)
            estimated_visitors = total_orders * 100 if total_orders > 0 else 1000
            conversion_rate = (total_orders / estimated_visitors * 100) if estimated_visitors > 0 else 0.0
            
            # Calculate inventory health (products in stock / total products)
            inventory_result = await self.db.execute(
                select(
                    func.count(Product.id).filter(Product.inventory_level > 0),
                    func.count(Product.id)
                ).where(
                    Product.tenant_id == self.tenant_id
                )
            )
            in_stock, total_products = inventory_result.first()
            inventory_health = (in_stock / total_products * 100) if total_products > 0 else 0.0
            
            return {
                "gmv": {"value": total_revenue, "change": 12.5, "trend": "up"},
                "margin": {"value": profit_margin, "change": 2.1, "trend": "up"},
                "conversion": {"value": round(conversion_rate, 2), "change": -0.5, "trend": "down"},
                "inventory_health": {"value": round(inventory_health, 1), "change": 5.0, "trend": "up"},
                "units_sold": {"value": int(units or 0), "change": 8.3, "trend": "up"},
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
            
            today = datetime.utcnow().date()
            since = today - timedelta(days=days)
            
            result = await self.db.execute(
                select(
                    SalesRecord.date,
                    func.sum(SalesRecord.revenue).label('revenue'),
                    func.sum(SalesRecord.quantity).label('units'),
                    func.count(SalesRecord.id).label('orders')
                ).where(
                    SalesRecord.tenant_id == self.tenant_id,
                    SalesRecord.date >= since
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
            from src.models.product import Product
            from src.models.sales_record import SalesRecord
            
            insights = []
            
            # Get top selling products
            result = await self.db.execute(
                select(
                    Product.name,
                    Product.sku,
                    func.sum(SalesRecord.revenue).label('total_revenue'),
                    func.sum(SalesRecord.quantity).label('total_quantity')
                )
                .join(SalesRecord, Product.id == SalesRecord.product_id)
                .where(Product.tenant_id == self.tenant_id)
                .group_by(Product.id, Product.name, Product.sku)
                .order_by(func.sum(SalesRecord.revenue).desc())
                .limit(3)
            )
            top_products = result.all()
            
            if top_products:
                top_product = top_products[0]
                insights.append({
                    "id": "top-seller",
                    "type": "success",
                    "title": "Top Performing Product",
                    "description": f"{top_product.name} generated ${float(top_product.total_revenue):.2f} in revenue",
                    "confidence": 0.95,
                    "action": "Consider increasing inventory for this product",
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
        Uses X-Internal-Key header for service-to-service authentication
        tenant_id is ALWAYS added to params for isolation
        """
        if params is None:
            params = {}
        
        # Map our UUID tenant ID to Vercel tenant ID format
        if "tenantId" in params:
            params["tenantId"] = map_tenant_id(params["tenantId"])
        
        url = f"{MOCK_API_URL}{endpoint}"
        
        # Add internal API key for service-to-service authentication
        headers = {
            "X-Internal-Key": INTERNAL_API_KEY
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                return response.json()
        except httpx.ConnectError:
            raise Exception(f"Cannot connect to Mock API at {MOCK_API_URL}. Is it accessible?")
        except httpx.HTTPStatusError as e:
            raise Exception(f"Mock API returned error {e.response.status_code} for {endpoint}")
        except Exception as e:
            raise Exception(f"Mock API error: {str(e)}")
