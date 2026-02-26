"""Add real-time data to demonstrate dashboard updates"""
import asyncio
import random
from datetime import datetime, timedelta
from uuid import uuid4
from decimal import Decimal

from src.database import AsyncSessionLocal
from src.models.product import Product
from src.models.review import Review
from src.models.sales_record import SalesRecord


async def add_more_products(tenant_id: str, count: int = 20):
    """Add more products to the database"""
    async with AsyncSessionLocal() as session:
        try:
            categories = ['Electronics', 'Clothing', 'Home & Garden', 'Sports', 'Books', 'Toys']
            marketplaces = ['Amazon', 'eBay', 'Walmart', 'Etsy']
            
            product_templates = [
                ('Wireless Mouse', 'Electronics', 29.99, 150),
                ('USB-C Cable', 'Electronics', 12.99, 300),
                ('Bluetooth Speaker', 'Electronics', 79.99, 85),
                ('Running Shoes', 'Sports', 89.99, 60),
                ('Yoga Mat', 'Sports', 34.99, 120),
                ('Coffee Maker', 'Home & Garden', 149.99, 45),
                ('LED Desk Lamp', 'Home & Garden', 39.99, 90),
                ('Backpack', 'Clothing', 49.99, 75),
                ('T-Shirt Pack', 'Clothing', 24.99, 200),
                ('Novel Book', 'Books', 14.99, 180),
                ('Cookbook', 'Books', 19.99, 95),
                ('Board Game', 'Toys', 34.99, 55),
                ('Action Figure', 'Toys', 24.99, 110),
                ('Water Bottle', 'Sports', 19.99, 250),
                ('Phone Case', 'Electronics', 15.99, 400),
                ('Headphones', 'Electronics', 129.99, 70),
                ('Fitness Tracker', 'Electronics', 99.99, 80),
                ('Sunglasses', 'Clothing', 39.99, 140),
                ('Kitchen Knife Set', 'Home & Garden', 79.99, 50),
                ('Throw Pillow', 'Home & Garden', 24.99, 160),
            ]
            
            products = []
            for i, (name, category, base_price, base_inventory) in enumerate(product_templates[:count]):
                # Add some randomness
                price_variation = random.uniform(0.9, 1.1)
                inventory_variation = random.randint(-20, 20)
                
                product = Product(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    sku=f"SKU-{1000 + i}",
                    normalized_sku=f"sku-{1000 + i}",
                    name=name,
                    category=category,
                    price=Decimal(str(round(base_price * price_variation, 2))),
                    currency="USD",
                    marketplace=random.choice(marketplaces),
                    inventory_level=max(0, base_inventory + inventory_variation),
                    created_at=datetime.utcnow() - timedelta(days=random.randint(1, 60)),
                    updated_at=datetime.utcnow()
                )
                session.add(product)
                products.append(product)
            
            await session.flush()
            print(f"✅ Added {len(products)} new products")
            
            # Add reviews for some products
            review_count = 0
            sentiments = ['positive', 'positive', 'positive', 'neutral', 'negative']  # Weighted
            review_templates = {
                'positive': [
                    "Great product! Highly recommend.",
                    "Excellent quality and fast shipping.",
                    "Love it! Exactly what I needed.",
                    "Best purchase I've made this year.",
                    "Amazing value for the price."
                ],
                'neutral': [
                    "It's okay, does the job.",
                    "Average product, nothing special.",
                    "Decent quality for the price.",
                    "Works as expected."
                ],
                'negative': [
                    "Not what I expected.",
                    "Poor quality, disappointed.",
                    "Broke after a week.",
                    "Would not recommend."
                ]
            }
            
            for product in products:
                # 70% chance of having reviews
                if random.random() < 0.7:
                    num_reviews = random.randint(1, 8)
                    for _ in range(num_reviews):
                        sentiment = random.choice(sentiments)
                        rating = 5 if sentiment == 'positive' else (3 if sentiment == 'neutral' else random.randint(1, 2))
                        
                        review = Review(
                            id=uuid4(),
                            tenant_id=tenant_id,
                            product_id=product.id,
                            rating=rating,
                            text=random.choice(review_templates[sentiment]),
                            sentiment=sentiment,
                            sentiment_confidence=random.uniform(0.75, 0.95),
                            is_spam=False,
                            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                            source=product.marketplace
                        )
                        session.add(review)
                        review_count += 1
            
            print(f"✅ Added {review_count} reviews")
            
            # Add sales records for some products
            sales_count = 0
            for product in products:
                # 60% chance of having sales
                if random.random() < 0.6:
                    num_sales = random.randint(1, 10)
                    for _ in range(num_sales):
                        sale = SalesRecord(
                            id=uuid4(),
                            tenant_id=tenant_id,
                            product_id=product.id,
                            quantity=random.randint(1, 5),
                            revenue=product.price * random.randint(1, 5),
                            date=(datetime.utcnow() - timedelta(days=random.randint(1, 90))).date(),
                            marketplace=product.marketplace,
                            created_at=datetime.utcnow()
                        )
                        session.add(sale)
                        sales_count += 1
            
            print(f"✅ Added {sales_count} sales records")
            
            await session.commit()
            
            print("\n" + "="*60)
            print("DATA ADDED SUCCESSFULLY!")
            print("="*60)
            print(f"\nTotal Products: {len(products)}")
            print(f"Total Reviews: {review_count}")
            print(f"Total Sales: {sales_count}")
            print("\nRefresh your dashboard to see the new data!")
            print("="*60)
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error adding data: {e}")
            raise


async def simulate_realtime_updates(tenant_id: str, duration_seconds: int = 60):
    """Simulate real-time price and inventory updates"""
    print(f"\n🔄 Simulating real-time updates for {duration_seconds} seconds...")
    print("Watch your dashboard for live changes!\n")
    
    from sqlalchemy import select
    
    start_time = datetime.utcnow()
    update_count = 0
    
    while (datetime.utcnow() - start_time).total_seconds() < duration_seconds:
        async with AsyncSessionLocal() as session:
            try:
                # Get random products
                result = await session.execute(
                    select(Product)
                    .where(Product.tenant_id == tenant_id)
                    .limit(5)
                )
                products = result.scalars().all()
                
                if products:
                    # Update prices and inventory
                    for product in products:
                        # Random price change (-5% to +5%)
                        price_change = random.uniform(0.95, 1.05)
                        product.price = Decimal(str(round(float(product.price) * price_change, 2)))
                        
                        # Random inventory change (-10 to +10)
                        inventory_change = random.randint(-10, 10)
                        product.inventory_level = max(0, product.inventory_level + inventory_change)
                        
                        product.updated_at = datetime.utcnow()
                        update_count += 1
                    
                    await session.commit()
                    print(f"✅ Updated {len(products)} products (Total updates: {update_count})")
                
                # Wait 5 seconds before next update
                await asyncio.sleep(5)
                
            except Exception as e:
                print(f"❌ Update error: {e}")
                await session.rollback()
    
    print(f"\n✅ Simulation complete! Made {update_count} updates.")


async def main():
    """Main function"""
    print("="*60)
    print("REAL-TIME DATA GENERATOR")
    print("="*60)
    
    # Get tenant ID from existing data
    async with AsyncSessionLocal() as session:
        from src.models.tenant import Tenant
        from sqlalchemy import select
        
        result = await session.execute(select(Tenant).limit(1))
        tenant = result.scalar_one_or_none()
        
        if not tenant:
            print("❌ No tenant found! Run init_database.py first.")
            return
        
        tenant_id = str(tenant.id)
        print(f"\nUsing Tenant: {tenant.name} (ID: {tenant_id})")
    
    print("\nWhat would you like to do?")
    print("1. Add more products, reviews, and sales data")
    print("2. Simulate real-time price/inventory updates")
    print("3. Both (add data then simulate updates)")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        count = input("How many products to add? (default: 20): ").strip()
        count = int(count) if count else 20
        await add_more_products(tenant_id, count)
    
    elif choice == "2":
        duration = input("Simulation duration in seconds? (default: 60): ").strip()
        duration = int(duration) if duration else 60
        await simulate_realtime_updates(tenant_id, duration)
    
    elif choice == "3":
        count = input("How many products to add? (default: 20): ").strip()
        count = int(count) if count else 20
        await add_more_products(tenant_id, count)
        
        print("\n" + "="*60)
        input("Press Enter to start real-time simulation...")
        
        duration = input("Simulation duration in seconds? (default: 60): ").strip()
        duration = int(duration) if duration else 60
        await simulate_realtime_updates(tenant_id, duration)
    
    else:
        print("Invalid choice!")


if __name__ == "__main__":
    asyncio.run(main())
