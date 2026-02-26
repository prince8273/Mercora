"""Initialize database with tables and sample data"""
import asyncio
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from src.database import init_db, AsyncSessionLocal
from src.models.tenant import Tenant
from src.models.user import User
from src.models.product import Product
from src.models.review import Review


async def create_sample_data():
    """Create sample tenant, user, products, and reviews"""
    async with AsyncSessionLocal() as session:
        try:
            # Create a demo tenant
            tenant = Tenant(
                id=uuid4(),
                name="Demo Company",
                slug="demo-company",
                contact_email="contact@demo.example.com",
                plan="pro",
                max_products=1000,
                max_users=50,
                is_active=True
            )
            session.add(tenant)
            await session.flush()
            
            print(f"✅ Created tenant: {tenant.name} (ID: {tenant.id})")
            
            # Create a demo user (using a pre-hashed password to avoid bcrypt issues)
            # Password: demo123
            # This is a bcrypt hash of "demo123"
            user = User(
                id=uuid4(),
                tenant_id=tenant.id,
                email="demo@example.com",
                hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7qvqKQk9Zy",  # demo123
                full_name="Demo User",
                is_active=True,
                is_superuser=True
            )
            session.add(user)
            await session.flush()
            
            print(f"✅ Created user: {user.email} (password: demo123)")
            
            # Create sample products
            products_data = [
                {
                    "sku": "LAPTOP-001",
                    "name": "Premium Laptop Pro 15",
                    "category": "Electronics",
                    "price": Decimal("1299.99"),
                    "inventory_level": 45,
                    "marketplace": "Amazon"
                },
                {
                    "sku": "PHONE-002",
                    "name": "Smartphone X Plus",
                    "category": "Electronics",
                    "price": Decimal("899.99"),
                    "inventory_level": 120,
                    "marketplace": "Amazon"
                },
                {
                    "sku": "HEADPHONE-003",
                    "name": "Wireless Noise-Canceling Headphones",
                    "category": "Electronics",
                    "price": Decimal("299.99"),
                    "inventory_level": 8,
                    "marketplace": "Amazon"
                },
                {
                    "sku": "WATCH-004",
                    "name": "Smart Watch Series 5",
                    "category": "Wearables",
                    "price": Decimal("399.99"),
                    "inventory_level": 67,
                    "marketplace": "eBay"
                },
                {
                    "sku": "TABLET-005",
                    "name": "Tablet Pro 12.9",
                    "category": "Electronics",
                    "price": Decimal("799.99"),
                    "inventory_level": 34,
                    "marketplace": "Amazon"
                },
                {
                    "sku": "CAMERA-006",
                    "name": "Digital Camera 4K",
                    "category": "Electronics",
                    "price": Decimal("1499.99"),
                    "inventory_level": 5,
                    "marketplace": "eBay"
                },
                {
                    "sku": "SPEAKER-007",
                    "name": "Smart Speaker with Voice Assistant",
                    "category": "Electronics",
                    "price": Decimal("149.99"),
                    "inventory_level": 200,
                    "marketplace": "Amazon"
                },
                {
                    "sku": "KEYBOARD-008",
                    "name": "Mechanical Gaming Keyboard RGB",
                    "category": "Accessories",
                    "price": Decimal("129.99"),
                    "inventory_level": 0,
                    "marketplace": "Amazon"
                },
            ]
            
            products = []
            for prod_data in products_data:
                product = Product(
                    id=uuid4(),
                    tenant_id=tenant.id,
                    sku=prod_data["sku"],
                    normalized_sku=prod_data["sku"].lower(),
                    name=prod_data["name"],
                    category=prod_data["category"],
                    price=prod_data["price"],
                    currency="USD",
                    marketplace=prod_data["marketplace"],
                    inventory_level=prod_data["inventory_level"],
                    created_at=datetime.utcnow() - timedelta(days=30),
                    updated_at=datetime.utcnow()
                )
                session.add(product)
                products.append(product)
            
            await session.flush()
            print(f"✅ Created {len(products)} sample products")
            
            # Create sample reviews
            reviews_data = [
                {"product_idx": 0, "rating": 5, "text": "Excellent laptop! Fast and reliable.", "sentiment": "positive"},
                {"product_idx": 0, "rating": 4, "text": "Good performance but a bit pricey.", "sentiment": "positive"},
                {"product_idx": 1, "rating": 5, "text": "Best phone I've ever owned!", "sentiment": "positive"},
                {"product_idx": 1, "rating": 3, "text": "Battery life could be better.", "sentiment": "neutral"},
                {"product_idx": 2, "rating": 5, "text": "Amazing sound quality and noise cancellation.", "sentiment": "positive"},
                {"product_idx": 2, "rating": 2, "text": "Uncomfortable for long wear.", "sentiment": "negative"},
                {"product_idx": 3, "rating": 4, "text": "Great fitness tracking features.", "sentiment": "positive"},
                {"product_idx": 4, "rating": 5, "text": "Perfect for work and entertainment.", "sentiment": "positive"},
                {"product_idx": 5, "rating": 4, "text": "Excellent image quality.", "sentiment": "positive"},
                {"product_idx": 6, "rating": 5, "text": "Voice recognition works perfectly!", "sentiment": "positive"},
            ]
            
            for review_data in reviews_data:
                product = products[review_data["product_idx"]]
                review = Review(
                    id=uuid4(),
                    tenant_id=tenant.id,
                    product_id=product.id,
                    rating=review_data["rating"],
                    text=review_data["text"],
                    sentiment=review_data["sentiment"],
                    sentiment_confidence=0.85,
                    is_spam=False,
                    created_at=datetime.utcnow() - timedelta(days=15),
                    source="Amazon"
                )
                session.add(review)
            
            await session.commit()
            print(f"✅ Created {len(reviews_data)} sample reviews")
            
            print("\n" + "="*60)
            print("DATABASE INITIALIZED SUCCESSFULLY!")
            print("="*60)
            print(f"\nLogin credentials:")
            print(f"  Email: demo@example.com")
            print(f"  Password: demo123")
            print(f"\nTenant ID: {tenant.id}")
            print(f"User ID: {user.id}")
            print("="*60)
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error creating sample data: {e}")
            raise


async def main():
    """Main initialization function"""
    try:
        print("Initializing database tables...")
        await init_db()
        print("✅ Database tables created")
        
        print("\nCreating sample data...")
        await create_sample_data()
        
        return 0
    except Exception as e:
        print(f"\n❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
