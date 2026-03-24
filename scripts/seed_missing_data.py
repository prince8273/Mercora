"""
Seed missing sales records and reviews for tenants that lack them.

Missing:
  0bb41987 (FitLife,  30 products) - needs reviews
  54d459ab (TechGear, 20 products) - needs reviews
  8713902c (Premium,   8 products) - needs sales
  c4b61431 (Various,  10 products) - needs reviews
"""
import asyncio, sys, random, uuid
from datetime import date, timedelta
sys.path.insert(0, '.')

from src.database import AsyncSessionLocal
from src.models.product import Product
from src.models.sales_record import SalesRecord
from src.models.review import Review
from sqlalchemy import select

random.seed(42)

# ── Review templates per category ────────────────────────────────────────────
REVIEWS = {
    'Sports & Fitness': [
        (5, "Excellent quality, exactly what I needed for my workouts. Highly recommend!"),
        (5, "Great product, very durable and well made. Using it daily with no issues."),
        (4, "Good value for money. Does the job well, delivery was fast too."),
        (4, "Solid build quality. Slightly smaller than expected but works perfectly."),
        (3, "Decent product. Nothing special but gets the job done for the price."),
        (3, "Average quality. Works fine but packaging could be better."),
        (2, "Not as described. Material feels cheap and started showing wear quickly."),
        (5, "Absolutely love this! Transformed my home workout routine completely."),
        (4, "Really happy with this purchase. Good quality and arrived quickly."),
        (5, "Perfect for what I needed. Great quality and fast shipping."),
        (4, "Very pleased with this. Sturdy construction and easy to use."),
        (3, "It's okay. Does what it says but nothing exceptional about it."),
        (5, "Brilliant product! Exactly as described and great quality."),
        (4, "Good product overall. Minor issue with packaging but product itself is fine."),
        (2, "Disappointed. Feels flimsy and not worth the price in my opinion."),
    ],
    'Electronics': [
        (5, "Fantastic product! Works perfectly and setup was incredibly easy."),
        (5, "Excellent build quality. Exactly as described, very happy with purchase."),
        (4, "Great product. Works as expected, good value for the price."),
        (4, "Happy with this purchase. Good quality and arrived well packaged."),
        (3, "Decent but not outstanding. Does the job but nothing special."),
        (3, "Works fine. A bit fiddly to set up but once going it's good."),
        (2, "Had issues from day one. Customer service was helpful but product is poor."),
        (5, "Superb quality! Exceeded my expectations in every way."),
        (4, "Really good product. Minor software quirk but overall very satisfied."),
        (5, "Love it! Works flawlessly and looks great too."),
        (4, "Solid product. Does exactly what it says on the tin."),
        (3, "Average. Works but feels a bit cheap for the price point."),
        (5, "Outstanding! Best purchase I've made this year without a doubt."),
        (4, "Very good. Slight learning curve but once you get it, it's brilliant."),
        (1, "Stopped working after two weeks. Very disappointed with the quality."),
    ],
    'Home & Kitchen': [
        (5, "Love this! Great quality and looks exactly as pictured. Very happy."),
        (5, "Excellent product. Well made, easy to use and great value for money."),
        (4, "Really pleased with this. Good quality and arrived quickly."),
        (4, "Nice product. Does what it should and looks good in the kitchen."),
        (3, "It's fine. Nothing special but does the job for everyday use."),
        (3, "Okay product. A bit smaller than I expected but works well enough."),
        (2, "Not great. Feels cheap and the finish isn't as good as photos suggest."),
        (5, "Brilliant! Exactly what I was looking for. Great quality and fast delivery."),
        (4, "Good purchase. Solid build and easy to clean. Would buy again."),
        (5, "Perfect! Exactly as described and arrived in perfect condition."),
        (4, "Very happy with this. Good quality for the price, works well."),
        (3, "Decent enough. Does the job but nothing to write home about."),
        (5, "Absolutely love it! Great quality and makes such a difference."),
        (4, "Good product. Minor cosmetic issue but functionally perfect."),
        (2, "Disappointed. Broke after a month of normal use. Poor quality."),
    ],
    'Beauty & Personal Care': [
        (5, "Amazing product! Noticed a difference within days. Will definitely repurchase."),
        (5, "Love this! Great quality, lovely scent and lasts a long time."),
        (4, "Really good. Works as described and good value for money."),
        (4, "Happy with this. Good quality product, packaging was nice too."),
        (3, "It's okay. Does what it says but didn't wow me personally."),
        (3, "Average. Works fine but I've used better products at this price."),
        (2, "Not for me. Caused slight irritation and scent was overpowering."),
        (5, "Absolutely brilliant! My skin has never looked better. Highly recommend."),
        (4, "Very pleased. Good quality and a little goes a long way."),
        (5, "Fantastic! Exactly what I needed and the results speak for themselves."),
        (4, "Good product. Subtle scent and works well. Would buy again."),
        (3, "Decent but not life-changing. Does the job for the price."),
        (5, "Incredible product! Can't imagine my routine without it now."),
        (4, "Really nice. Good quality and arrived quickly. Happy customer."),
        (1, "Allergic reaction unfortunately. Product itself may be fine for others."),
    ],
    'Clothing': [
        (5, "Perfect fit! Great quality fabric and looks exactly as pictured."),
        (5, "Love this! Comfortable, well made and great value for money."),
        (4, "Really happy with this. Good quality and true to size."),
        (4, "Nice item. Good material and stitching. Washes well too."),
        (3, "It's okay. Sizing runs a bit small but quality is decent."),
        (3, "Average. Material is thinner than expected but wearable."),
        (2, "Not great quality. Stitching came loose after a few washes."),
        (5, "Brilliant! Exactly as described and fits perfectly. Very happy."),
        (4, "Good purchase. Comfortable and looks smart. Would recommend."),
        (5, "Absolutely love it! Great quality and so comfortable to wear."),
        (4, "Very pleased. Good quality for the price, fits well."),
        (3, "Decent enough. Does the job but nothing exceptional."),
        (5, "Perfect! Great quality, fast delivery and exactly as described."),
        (4, "Good item. Minor colour difference from photos but otherwise great."),
        (2, "Disappointed with the quality. Fabric feels cheap and thin."),
    ],
    'Books': [
        (5, "Couldn't put it down! Absolutely gripping from start to finish."),
        (5, "Excellent read. Well written, informative and thoroughly enjoyable."),
        (4, "Really good book. Learned a lot and kept me engaged throughout."),
        (4, "Good read. Well structured and easy to follow. Would recommend."),
        (3, "Decent book. Some interesting parts but drags in the middle."),
        (3, "Average. Has its moments but overall a bit disappointing."),
        (2, "Not what I expected. Poorly written and hard to follow."),
        (5, "Brilliant! One of the best books I've read in years. A must-read."),
        (4, "Very enjoyable. Great content and well presented throughout."),
        (5, "Fantastic book! Highly recommend to anyone interested in the topic."),
        (4, "Good book. Comprehensive coverage and easy to understand."),
        (3, "It's okay. Some useful information but could be more concise."),
        (5, "Outstanding! Changed the way I think about the subject entirely."),
        (4, "Really good. Well researched and written in an engaging style."),
        (2, "Disappointing. Lots of filler content and not much substance."),
    ],
    'Toys': [
        (5, "Kids absolutely love it! Great quality and keeps them entertained for hours."),
        (5, "Brilliant toy! Well made, safe and great value for money."),
        (4, "Really good. Kids enjoy it and it's held up well to rough play."),
        (4, "Good toy. Well made and age appropriate. Happy with purchase."),
        (3, "Decent. Kids like it but it's not as exciting as the pictures suggest."),
        (3, "Average. Works fine but a few pieces feel a bit flimsy."),
        (2, "Not great. Broke within a week of normal play. Poor quality."),
        (5, "Fantastic! My child hasn't put it down since it arrived. Brilliant."),
        (4, "Very happy with this. Good quality and great educational value."),
        (5, "Perfect gift! Great quality and my kids are obsessed with it."),
    ],
    'General': [
        (5, "Great product! Exactly as described and arrived quickly."),
        (4, "Good value for money. Happy with the purchase overall."),
        (3, "Decent product. Does what it says, nothing more nothing less."),
        (4, "Pleased with this. Good quality and fast delivery."),
        (5, "Excellent! Would definitely buy again and recommend to others."),
        (3, "Average. Works fine but not exceptional for the price."),
        (2, "Bit disappointed. Not quite as good as the description suggested."),
        (4, "Good product. Minor issue but overall satisfied with purchase."),
        (5, "Really happy with this! Great quality and great value."),
        (4, "Solid product. Does the job well and looks good too."),
    ],
}

def pick_reviews(category, product_id, tenant_id, n=60):
    pool = REVIEWS.get(category, REVIEWS['General'])
    records = []
    base_date = date(2024, 1, 1)
    for i in range(n):
        rating, text = random.choice(pool)
        # Add slight variation to text
        sentiment_score = (rating - 1) / 4.0  # 0.0 to 1.0
        records.append(Review(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            product_id=product_id,
            rating=rating,
            text=text,
            sentiment_score=sentiment_score,
            is_spam=False,
            source='Amazon',
            created_at=None,  # let DB default
        ))
    return records


def pick_sales(product_id, tenant_id, price, n=10):
    records = []
    base_date = date(2024, 1, 1)
    for i in range(n):
        qty = random.randint(1, 8)
        sale_date = base_date + timedelta(days=random.randint(0, 365))
        records.append(SalesRecord(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            product_id=product_id,
            quantity=qty,
            revenue=round(float(price) * qty, 2),
            date=sale_date,
            marketplace='Amazon',
        ))
    return records


async def seed():
    async with AsyncSessionLocal() as db:
        r = await db.execute(select(Product).order_by(Product.tenant_id))
        products = r.scalars().all()

        # Group by tenant
        by_tenant = {}
        for p in products:
            by_tenant.setdefault(str(p.tenant_id), []).append(p)

        NEEDS_REVIEWS = {
            '0bb41987-6f4b-4ed5-a63b-2ac1fd3b56b6',
            '54d459ab-4ae8-480a-9d1c-d53b218a4fb2',
            'c4b61431-3e54-4691-b9cc-77a9eb96e610',
        }
        NEEDS_SALES = {
            '8713902c-1021-47f8-9a3d-8ce298cdce4c',
        }
        SKIP = {'11111111-1111-1111-1111-111111111111'}

        total_reviews = 0
        total_sales = 0

        for tid, prods in by_tenant.items():
            if tid in SKIP:
                print(f'SKIP {tid[:8]}')
                continue

            if tid in NEEDS_REVIEWS:
                # Vary review count per product: 30-80
                for p in prods:
                    n = random.randint(30, 80)
                    reviews = pick_reviews(p.category or 'General', p.id, p.tenant_id, n)
                    db.add_all(reviews)
                    total_reviews += len(reviews)
                print(f'  Added reviews for {tid[:8]} ({len(prods)} products)')

            if tid in NEEDS_SALES:
                for p in prods:
                    n = random.randint(15, 30)
                    sales = pick_sales(p.id, p.tenant_id, p.price, n)
                    db.add_all(sales)
                    total_sales += len(sales)
                print(f'  Added sales for {tid[:8]} ({len(prods)} products)')

        await db.commit()
        print(f'\nDone. Added {total_reviews} reviews, {total_sales} sales records.')

asyncio.run(seed())
