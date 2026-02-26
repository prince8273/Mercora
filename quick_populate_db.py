"""
Quick script to populate database with sample data for testing
Run this to see data on the dashboard immediately!
"""
import asyncio
from uuid import uuid4
from datetime import datetime, timedelta
import random

from src.database import AsyncSessionLocal, init_db
from src.models.product import Product
from src.models.review import Review
from src.models.tenant import Tenant
from src.models.user import User
from src.auth.security import get_password_hash


async def quick_populate():
    """Quickly populate database with sample data"""
    
    print("=" * 60)
    print("QUICK DATABASE POPULATION")
    print("=" * 60)
    print()
    
    # Initialize database
    print("1. Initializing database...")
    await init_db()
    print("   ✓ Database initialized")
    print()
    
    async with AsyncSessionLocal() as session:
        try:
            # Create demo tenant
            print("2. Creating demo tenant...")
            demo_tenant_id = uuid4()
            tenant = Tenant(
                id=demo_tenant_id,
                name="Demo Company",
                slug="demo-company",
                contact_email="demo@example.com",
                plan="free",
                is_active=True
            )
            session.add(tenant)
            await session.flush()
            print(f"   ✓ Tenant created: {tenant.name}")
            print()
            
            # Create demo user (with simple password for demo mode)
            print("3. Creating demo user...")
            demo_user_id = uuid4()
            user = User(
                id=demo_user_id,
                tenant_id=demo_tenant_id,
                email="demo@example.com",
                hashed_password="demo123",  # In DEMO_MODE, password is not hashed
                full_name="Demo User",
                is_active=True,
                is_superuser=False
            )
            session.add(user)
            await session.flush()
            print(f"   ✓ User created: {user.email}")
            print(f"   ✓ Password: demo123 (DEMO_MODE enabled)")
            print()
            
            # Create products
            print("4. Creating products...")
            categories = ["Electronics", "Clothing", "Home & Garden", "Sports", "Books"]
            products = []
            
            for i in range(30):
                category = random.choice(categories)
                product = Product(
                    id=uuid4(),
                    tenant_id=demo_tenant_id,
                    sku=f"PROD-{i+1:03d}",
                    normalized_sku=f"PROD-{i+1:03d}",
                    name=f"Sample Product {i+1}",
                    category=category,
                    price=round(random.uniform(9.99, 199.99), 2),
                    currency="USD",
                    marketplace=random.choice(["amazon", "ebay", "walmart"]),
                    inventory_level=random.randint(0, 200),
                    created_at=datetime.utcnow() - timedelta(days=random.randint(0, 30)),
                    updated_at=datetime.utcnow()
                )
                products.append(product)
                session.add(product)
            
            await session.flush()
            print(f"   ✓ Created {len(products)} products")
            print()
            
            # Create reviews
            print("5. Creating reviews...")
            reviews = []
            review_texts = [
                "Great product! Highly recommend.",
                "Good quality for the price.",
                "Average product, nothing special.",
                "Not what I expected.",
                "Excellent! Will buy again.",
                "Fast shipping, good packaging.",
                "Product works as described.",
                "Could be better.",
                "Love it! Perfect for my needs.",
                "Disappointed with quality."
            ]
            
            for product in products[:20]:  # Add reviews to first 20 products
                num_reviews = random.randint(1, 10)
                for _ in range(num_reviews):
                    rating = random.randint(1, 5)
                    review = Review(
                        id=uuid4(),
                        tenant_id=demo_tenant_id,
                        product_id=product.id,
                        rating=rating,
                        text=random.choice(review_texts),
                        source=random.choice(["amazon", "ebay", "website"]),
                        is_spam=False,
                        created_at=datetime.utcnow() - timedelta(days=random.randint(0, 60))
                    )
                    reviews.append(review)
                    session.add(review)
            
            await session.flush()
            print(f"   ✓ Created {len(reviews)} reviews")
            print()
            
            # Commit all changes
            await session.commit()
            
            print("=" * 60)
            print("✅ DATABASE POPULATED SUCCESSFULLY!")
            print("=" * 60)
            print()
            print("📊 Summary:")
            print(f"   • Tenant: {tenant.name}")
            print(f"   • User: {user.email} (password: demo123)")
            print(f"   • Products: {len(products)}")
            print(f"   • Reviews: {len(reviews)}")
            print()
            print("🚀 You can now:")
            print("   1. Login with: demo@example.com / demo123")
            print("   2. View dashboard with real data")
            print("   3. Run queries on the data")
            print("   4. Upload more data via CSV")
            print()
            print("🔗 Tenant ID (for API calls):")
            print(f"   {demo_tenant_id}")
            print()
            
            return demo_tenant_id, demo_user_id
            
        except Exception as e:
            await session.rollback()
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            raise


if __name__ == "__main__":
    try:
        asyncio.run(quick_populate())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        exit(1)
