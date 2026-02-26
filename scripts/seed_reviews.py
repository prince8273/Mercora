"""Seed review data for HomeStyle Living tenant"""
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.models.review import Review
from src.models.product import Product
from uuid import UUID, uuid4
from datetime import datetime, timedelta
import random

# HomeStyle Living tenant ID (from database check)
TENANT_ID = UUID('9b00dc26-cec5-4eeb-ba9e-cf6b65cdaeb6')

# Realistic review templates with varying sentiments
SAMPLE_REVIEWS = [
    # 5-star reviews (sentiment 0.85-0.95)
    {"rating": 5, "sentiment": 0.95, "text": "Absolutely love this product! Exceeded all my expectations."},
    {"rating": 5, "sentiment": 0.92, "text": "Outstanding quality! Will definitely buy again."},
    {"rating": 5, "sentiment": 0.90, "text": "Perfect! Exactly what I was looking for."},
    {"rating": 5, "sentiment": 0.88, "text": "Excellent product, fast shipping, highly recommend!"},
    {"rating": 5, "sentiment": 0.87, "text": "Best purchase I've made this year. Five stars!"},
    
    # 4-star reviews (sentiment 0.70-0.85)
    {"rating": 4, "sentiment": 0.82, "text": "Great quality, very satisfied with my purchase."},
    {"rating": 4, "sentiment": 0.80, "text": "Good product, fast shipping. Would recommend."},
    {"rating": 4, "sentiment": 0.78, "text": "Nice quality, meets expectations. Happy with it."},
    {"rating": 4, "sentiment": 0.75, "text": "Solid product, good value for money."},
    {"rating": 4, "sentiment": 0.72, "text": "Pretty good overall, minor issues but nothing major."},
    
    # 3-star reviews (sentiment 0.45-0.60)
    {"rating": 3, "sentiment": 0.58, "text": "Decent product, does the job. Nothing special."},
    {"rating": 3, "sentiment": 0.55, "text": "It's okay. Average quality for the price."},
    {"rating": 3, "sentiment": 0.50, "text": "Meets basic expectations but could be better."},
    {"rating": 3, "sentiment": 0.48, "text": "Not bad, not great. Just average."},
    
    # 2-star reviews (sentiment 0.20-0.40)
    {"rating": 2, "sentiment": 0.35, "text": "Disappointed. Quality not as described."},
    {"rating": 2, "sentiment": 0.30, "text": "Not what I expected. Considering returning it."},
    {"rating": 2, "sentiment": 0.25, "text": "Below average quality. Not worth the price."},
    
    # 1-star reviews (sentiment 0.05-0.20)
    {"rating": 1, "sentiment": 0.15, "text": "Very disappointed. Poor quality, waste of money."},
    {"rating": 1, "sentiment": 0.10, "text": "Terrible product. Do not recommend."},
    {"rating": 1, "sentiment": 0.08, "text": "Worst purchase ever. Completely unsatisfied."},
]

# Weight distribution for realistic review patterns
# Most products should have mostly positive reviews
RATING_WEIGHTS = {
    5: 0.45,  # 45% 5-star
    4: 0.30,  # 30% 4-star
    3: 0.15,  # 15% 3-star
    2: 0.07,  # 7% 2-star
    1: 0.03,  # 3% 1-star
}


async def seed_reviews():
    """Seed review data for HomeStyle Living tenant"""
    print(f"\n{'='*60}")
    print("Seeding Review Data for HomeStyle Living Tenant")
    print(f"{'='*60}\n")
    
    # Get database session
    async for db in get_db():
        try:
            # Fetch all products for this tenant
            result = await db.execute(
                select(Product).where(Product.tenant_id == TENANT_ID)
            )
            products = result.scalars().all()
            
            if not products:
                print(f"❌ No products found for tenant {TENANT_ID}")
                return
            
            print(f"Found {len(products)} products for HomeStyle Living")
            print(f"Tenant ID: {TENANT_ID}\n")
            
            reviews_to_add = []
            product_review_counts = {}
            
            # Generate reviews for each product
            for i, product in enumerate(products, 1):
                # Vary the number of reviews per product (15-60 reviews)
                # Some products are more popular than others
                if i <= 5:
                    # Top 5 products get more reviews
                    num_reviews = random.randint(40, 60)
                elif i <= 10:
                    # Next 5 get moderate reviews
                    num_reviews = random.randint(25, 40)
                else:
                    # Rest get fewer reviews
                    num_reviews = random.randint(15, 30)
                
                product_review_counts[product.name] = num_reviews
                
                # Generate reviews with weighted distribution
                for _ in range(num_reviews):
                    # Select rating based on weights
                    rating = random.choices(
                        list(RATING_WEIGHTS.keys()),
                        weights=list(RATING_WEIGHTS.values())
                    )[0]
                    
                    # Find matching review templates for this rating
                    matching_templates = [r for r in SAMPLE_REVIEWS if r["rating"] == rating]
                    review_template = random.choice(matching_templates)
                    
                    # Create review
                    review = Review(
                        id=uuid4(),
                        tenant_id=TENANT_ID,
                        product_id=product.id,
                        rating=review_template["rating"],
                        text=review_template["text"],
                        sentiment_score=review_template["sentiment"],  # Use sentiment_score (Float) not sentiment (String)
                        sentiment_confidence=random.uniform(0.75, 0.95),
                        is_spam=False,
                        created_at=datetime.utcnow() - timedelta(days=random.randint(1, 365)),
                        source="amazon"
                    )
                    reviews_to_add.append(review)
            
            # Bulk insert all reviews
            db.add_all(reviews_to_add)
            await db.commit()
            
            print(f"✅ Successfully seeded {len(reviews_to_add)} reviews!")
            print(f"\nReview distribution by product:")
            print(f"{'-'*60}")
            
            # Show top 10 products with review counts
            sorted_products = sorted(product_review_counts.items(), key=lambda x: x[1], reverse=True)
            for product_name, count in sorted_products[:10]:
                print(f"  {product_name[:40]:40} : {count:3} reviews")
            
            if len(sorted_products) > 10:
                print(f"  ... and {len(sorted_products) - 10} more products")
            
            print(f"\n{'='*60}")
            print("Seeding Complete!")
            print(f"{'='*60}\n")
            
            # Show summary statistics
            total_reviews = len(reviews_to_add)
            avg_reviews_per_product = total_reviews / len(products)
            
            rating_counts = {}
            for review in reviews_to_add:
                rating_counts[review.rating] = rating_counts.get(review.rating, 0) + 1
            
            print("Summary Statistics:")
            print(f"  Total Products: {len(products)}")
            print(f"  Total Reviews: {total_reviews}")
            print(f"  Avg Reviews/Product: {avg_reviews_per_product:.1f}")
            print(f"\nRating Distribution:")
            for rating in sorted(rating_counts.keys(), reverse=True):
                count = rating_counts[rating]
                percentage = (count / total_reviews) * 100
                print(f"  {rating} stars: {count:4} ({percentage:5.1f}%)")
            
            print(f"\n{'='*60}\n")
            
        except Exception as e:
            print(f"❌ Error seeding reviews: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()
        finally:
            break  # Exit the async generator


async def verify_seeding():
    """Verify that reviews were seeded correctly"""
    print("Verifying seeded data...\n")
    
    async for db in get_db():
        try:
            # Count total reviews
            from sqlalchemy import func
            result = await db.execute(
                select(func.count(Review.id)).where(Review.tenant_id == TENANT_ID)
            )
            total_reviews = result.scalar()
            
            print(f"✅ Total reviews in database: {total_reviews}")
            
            # Get top 5 products by average sentiment
            result = await db.execute(
                select(
                    Product.name,
                    Product.sku,
                    func.count(Review.id).label('review_count'),
                    func.avg(Review.sentiment).label('avg_sentiment')
                )
                .join(Review, Product.id == Review.product_id)
                .where(Review.tenant_id == TENANT_ID)
                .group_by(Product.id)
                .order_by(func.avg(Review.sentiment).desc())
                .limit(5)
            )
            
            top_products = result.all()
            
            if top_products:
                print(f"\nTop 5 Products by Sentiment:")
                print(f"{'-'*80}")
                print(f"{'Product Name':<40} {'SKU':<20} {'Reviews':>8} {'Sentiment':>10}")
                print(f"{'-'*80}")
                for product in top_products:
                    print(f"{product.name[:40]:<40} {product.sku:<20} {product.review_count:>8} {product.avg_sentiment:>10.2f}")
            
            print(f"\n{'='*60}")
            print("Verification Complete!")
            print(f"{'='*60}\n")
            
        except Exception as e:
            print(f"❌ Error verifying data: {e}")
            import traceback
            traceback.print_exc()
        finally:
            break


if __name__ == "__main__":
    print("\n" + "="*60)
    print("HomeStyle Living Review Data Seeding Script")
    print("="*60 + "\n")
    
    # Run seeding
    asyncio.run(seed_reviews())
    
    # Verify seeding
    asyncio.run(verify_seeding())
    
    print("\n✅ All done! You can now run the test suite.")
    print("   Run: python test_fixes.ps1\n")
