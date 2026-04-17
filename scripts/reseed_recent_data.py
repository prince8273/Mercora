"""
Reseed all time-sensitive data with dates spread across the last 90 days.
Covers: reviews, sales_records, price_history
Does NOT delete existing data — only updates created_at / date columns.
"""
import asyncio, sys, random
sys.path.insert(0, '.')
from datetime import datetime, timedelta
from sqlalchemy import text
from src.database import AsyncSessionLocal

TODAY = datetime.utcnow()
DAYS_90 = TODAY - timedelta(days=90)


def rand_date(start: datetime, end: datetime) -> datetime:
    delta = end - start
    return start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))


async def reseed():
    async with AsyncSessionLocal() as db:

        # ── 1. REVIEWS ──────────────────────────────────────────────
        print("Reseeding reviews...")
        r = await db.execute(text("SELECT id FROM reviews"))
        review_ids = [row[0] for row in r.fetchall()]
        print(f"  Found {len(review_ids)} reviews")

        for rid in review_ids:
            new_date = rand_date(DAYS_90, TODAY)
            await db.execute(
                text("UPDATE reviews SET created_at = :d, updated_at = :d WHERE id = :id"),
                {"d": new_date, "id": rid}
            )
        await db.commit()
        print(f"  ✅ Updated {len(review_ids)} reviews")

        # ── 2. SALES RECORDS ────────────────────────────────────────
        print("Reseeding sales_records...")
        r = await db.execute(text("SELECT id FROM sales_records"))
        sale_ids = [row[0] for row in r.fetchall()]
        print(f"  Found {len(sale_ids)} sales records")

        for sid in sale_ids:
            new_date = rand_date(DAYS_90, TODAY).date()
            await db.execute(
                text("UPDATE sales_records SET date = :d WHERE id = :id"),
                {"d": new_date, "id": sid}
            )
        await db.commit()
        print(f"  ✅ Updated {len(sale_ids)} sales records")

        # ── 3. PRICE HISTORY ────────────────────────────────────────
        print("Reseeding price_history...")
        r = await db.execute(text("SELECT id FROM price_history"))
        ph_ids = [row[0] for row in r.fetchall()]
        print(f"  Found {len(ph_ids)} price history records")

        for pid in ph_ids:
            new_date = rand_date(DAYS_90, TODAY).date()
            await db.execute(
                text("UPDATE price_history SET price_date = :d WHERE id = :id"),
                {"d": new_date, "id": pid}
            )
        await db.commit()
        print(f"  ✅ Updated {len(ph_ids)} price history records")

        # ── VERIFY ──────────────────────────────────────────────────
        print("\nVerification:")
        for table, col in [("reviews", "created_at"), ("sales_records", "date"), ("price_history", "price_date")]:
            r = await db.execute(text(f"SELECT COUNT(*), MIN({col}), MAX({col}) FROM {table}"))
            row = r.fetchone()
            print(f"  {table:<20} count={row[0]:>6}  {str(row[1])[:19]} → {str(row[2])[:19]}")

        # Reviews per time window
        print("\nReviews per time window (all tenants):")
        for label, days in [("7d", 7), ("30d", 30), ("90d", 90)]:
            cutoff = TODAY - timedelta(days=days)
            r = await db.execute(text("SELECT COUNT(*) FROM reviews WHERE created_at >= :c"), {"c": cutoff})
            print(f"  {label}: {r.scalar()}")

asyncio.run(reseed())
