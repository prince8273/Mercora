"""
Import Mock Data from Amazon Sellers Mock API into PostgreSQL Database

This script fetches data from the mock API (port 3001) and imports it into
the real PostgreSQL database via the backend models.

Usage:
    python scripts/import_mock_data.py

Requirements:
    - Mock API running on http://localhost:3001
    - PostgreSQL database running
    - Backend dependencies installed
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import requests
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.database import get_db, engine
from src.models.user import User
from src.models.tenant import Tenant
from src.models.product import Product
from src.models.sales_record import SalesRecord
from src.models.review import Review


MOCK_API_URL = "http://localhost:3001"

# Map mock tenant IDs to actual UUIDs (will be generated on first run)
TENANT_UUID_MAP = {}

TENANTS = [
    {"id": "tenant-001", "name": "TechGear Pro", "type": "Electronics"},
    {"id": "tenant-002", "name": "HomeStyle Living", "type": "Home & Kitchen"},
    {"id": "tenant-003", "name": "FitLife Sports", "type": "Sports & Outdoors"},
    {"id": "tenant-004", "name": "BookWorm Treasures", "type": "Books"},
]


def fetch_mock_data(endpoint: str, tenant_id: str) -> dict:
    """Fetch data from mock API"""
    url = f"{MOCK_API_URL}{endpoint}?tenantId={tenant_id}"
    print(f"Fetching: {url}")
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


async def create_tenant(db: AsyncSession, tenant_data: dict) -> Tenant:
    """Create or get tenant"""
    # Check if tenant exists by slug
    slug = tenant_data["name"].lower().replace(" ", "-")
    result = await db.execute(
        select(Tenant).where(Tenant.slug == slug)
    )
    tenant = result.scalar_one_or_none()
    
    if tenant:
        print(f"  X Tenant {tenant_data['name']} already exists (UUID: {tenant.id})")
        # Store mapping for later use - convert UUID to string properly
        from uuid import UUID
        if isinstance(tenant.id, UUID):
            TENANT_UUID_MAP[tenant_data["id"]] = str(tenant.id)
        else:
            TENANT_UUID_MAP[tenant_data["id"]] = tenant.id
        return tenant
    
    # Create new tenant with auto-generated UUID
    tenant = Tenant(
        name=tenant_data["name"],
        slug=slug,
        contact_email=f"contact@{slug}.com",
        plan="pro",
        max_products=1000,
        max_users=10,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    
    # Store mapping for later use
    from uuid import UUID
    if isinstance(tenant.id, UUID):
        TENANT_UUID_MAP[tenant_data["id"]] = str(tenant.id)
    else:
        TENANT_UUID_MAP[tenant_data["id"]] = tenant.id
    
    print(f"  X Created tenant: {tenant_data['name']} (UUID: {tenant.id})")
    return tenant


async def create_user(db: AsyncSession, tenant_id: str, tenant_name: str, tenant_uuid: str) -> User:
    """Create or get user for tenant"""
    email = f"seller@{tenant_id}.com"
    
    # Check if user exists
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()
    
    if user:
        print(f"  X User {email} already exists")
        return user
    
    # Create new user with tenant UUID
    from uuid import UUID
    user = User(
        email=email,
        hashed_password="$2b$12$dummy_hash_for_testing",  # Dummy hash
        full_name=f"{tenant_name} Seller",
        tenant_id=UUID(tenant_uuid),
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    print(f"  X Created user: {email}")
    return user


async def import_products(db: AsyncSession, tenant_id: str, tenant_uuid: str):
    """Import products from inventory endpoint"""
    print(f"\nImporting products for {tenant_id}...")
    
    try:
        from uuid import UUID
        data = fetch_mock_data("/fba/inventory/v1/summaries", tenant_id)
        summaries = data.get("payload", {}).get("inventorySummaries", [])
        
        imported_count = 0
        for item in summaries:
            # Check if product exists
            result = await db.execute(
                select(Product).where(
                    Product.sku == item["sellerSku"],
                    Product.tenant_id == UUID(tenant_uuid)
                )
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                # Update inventory
                existing.inventory_level = item["inventoryDetails"]["fulfillableQuantity"]
                existing.updated_at = datetime.utcnow()
            else:
                # Create new product
                product = Product(
                    tenant_id=UUID(tenant_uuid),
                    sku=item["sellerSku"],
                    normalized_sku=item["sellerSku"].lower(),
                    name=f"Product {item['asin']}",
                    category="General",
                    price=Decimal("29.99"),  # Default price
                    cost=Decimal("20.00"),  # Default cost
                    currency="USD",
                    marketplace="Amazon.com",
                    inventory_level=item["inventoryDetails"]["fulfillableQuantity"],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(product)
                imported_count += 1
        
        await db.commit()
        print(f"  X Imported {imported_count} products, updated {len(summaries) - imported_count}")
        
    except Exception as e:
        print(f"  X Error importing products: {e}")
        await db.rollback()


async def import_orders(db: AsyncSession, tenant_id: str, tenant_uuid: str):
    """Import orders from orders endpoint"""
    print(f"\nImporting orders for {tenant_id}...")
    
    try:
        from uuid import UUID
        data = fetch_mock_data("/orders/v0/orders", tenant_id)
        orders = data.get("payload", {}).get("Orders", [])
        
        imported_count = 0
        for order in orders:
            order_id = order["AmazonOrderId"]
            
            # Get order items
            try:
                items_data = fetch_mock_data(f"/orders/v0/orders/{order_id}/orderItems", tenant_id)
                order_items = items_data.get("payload", {}).get("OrderItems", [])
            except:
                order_items = []
            
            # Create sales record for each item
            for item in order_items:
                # Find product by SKU
                result = await db.execute(
                    select(Product).where(
                        Product.sku == item["SellerSKU"],
                        Product.tenant_id == UUID(tenant_uuid)
                    )
                )
                product = result.scalar_one_or_none()
                
                if not product:
                    continue
                
                # Parse amounts
                item_price = Decimal(str(item["ItemPrice"]["Amount"]))
                quantity = item["QuantityOrdered"]
                sale_date = datetime.fromisoformat(order["PurchaseDate"].replace("Z", "+00:00")).date()
                
                # Check if sales record already exists for this product and date
                result = await db.execute(
                    select(SalesRecord).where(
                        SalesRecord.product_id == product.id,
                        SalesRecord.date == sale_date,
                        SalesRecord.tenant_id == UUID(tenant_uuid)
                    )
                )
                existing = result.scalar_one_or_none()
                
                if existing:
                    # Update existing record
                    existing.quantity += quantity
                    existing.revenue += item_price
                else:
                    # Create new sales record
                    sales_record = SalesRecord(
                        tenant_id=UUID(tenant_uuid),
                        product_id=product.id,
                        date=sale_date,
                        quantity=quantity,
                        revenue=item_price,
                        marketplace=order.get("MarketplaceName", "Amazon.com"),
                        extra_data={"order_id": order_id, "order_item_id": item["OrderItemId"]},
                        created_at=datetime.utcnow()
                    )
                    db.add(sales_record)
                    imported_count += 1
        
        await db.commit()
        print(f"  OK Imported {imported_count} sales records from {len(orders)} orders")
        
    except Exception as e:
        print(f"  X Error importing orders: {e}")
        await db.rollback()


async def import_tenant_data(db: AsyncSession, tenant_data: dict):
    """Import all data for a single tenant"""
    print(f"\n{'='*60}")
    print(f"Importing data for: {tenant_data['name']} ({tenant_data['id']})")
    print(f"{'='*60}")
    
    try:
        # Create tenant and user
        tenant = await create_tenant(db, tenant_data)
        tenant_uuid = TENANT_UUID_MAP[tenant_data["id"]]
        print(f"  X Using tenant UUID: {tenant_uuid}")
        
        user = await create_user(db, tenant_data["id"], tenant_data["name"], tenant_uuid)
        
        # Import products first (needed for orders)
        await import_products(db, tenant_data["id"], tenant_uuid)
        
        # Import orders and sales records
        await import_orders(db, tenant_data["id"], tenant_uuid)
        
        print(f"\nX Completed import for {tenant_data['name']}")
    except Exception as e:
        import traceback
        print(f"\nX Error importing {tenant_data['name']}: {e}")
        print(f"  Traceback: {traceback.format_exc()}")
        await db.rollback()


async def main():
    """Main import function"""
    print("\n" + "="*60)
    print("MOCK DATA IMPORT SCRIPT")
    print("="*60)
    print(f"Mock API: {MOCK_API_URL}")
    print(f"Tenants to import: {len(TENANTS)}")
    print("="*60)
    
    # Test mock API connection
    try:
        response = requests.get(MOCK_API_URL)
        response.raise_for_status()
        print("OK Mock API is accessible")
    except Exception as e:
        print(f"X Cannot connect to mock API: {e}")
        print("  Make sure mock API is running on http://localhost:3001")
        return
    
    # Import data for each tenant
    async for db in get_db():
        for tenant_data in TENANTS:
            try:
                await import_tenant_data(db, tenant_data)
            except Exception as e:
                print(f"\nX Error importing {tenant_data['name']}: {e}")
                continue
    
    print("\n" + "="*60)
    print("IMPORT COMPLETE")
    print("="*60)
    print("\nYou can now:")
    print("1. Start the backend: python -m uvicorn src.main:app --reload --port 8000")
    print("2. Login with any tenant email:")
    for tenant in TENANTS:
        print(f"   - seller@{tenant['id']}.com (password: any)")
    print("3. View data in the dashboard")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())


