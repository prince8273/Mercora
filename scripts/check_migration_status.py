"""Check what data changes were made today vs pre-existing."""
import asyncio, sys
sys.path.insert(0, '.')
from sqlalchemy import text
from src.database import AsyncSessionLocal
from datetime import datetime, date

TODAY = date.today()

async def check():
    async with AsyncSessionLocal() as db:
        print(f"Checking Postgres as of {TODAY}\n")

        # 1. Sentiment labels — were they fixed?
        r = await db.execute(text("SELECT sentiment, COUNT(*) FROM reviews GROUP BY sentiment ORDER BY COUNT(*) DESC"))
        rows = r.fetchall()
        print("=== SENTIMENT LABELS ===")
        for row in rows:
            print(f"  '{row[0]}': {row[1]}")
        float_labels = [r for r in rows if r[0] not in ('positive','neutral','negative') and r[0] is not None]
        print(f"  Float-string labels remaining: {len(float_labels)} {'CLEAN' if not float_labels else 'NEEDS FIX'}")

        # 2. Date distribution — was reseed applied?
        print("\n=== DATE DISTRIBUTION ===")
        for table, col in [("reviews","created_at"), ("sales_records","date"), ("price_history","price_date")]:
            r = await db.execute(text(f"SELECT COUNT(*) FROM {table} WHERE {col} >= :d"), {"d": date(2026,1,17)})
            in_range = r.scalar()
            r = await db.execute(text(f"SELECT COUNT(*) FROM {table}"))
            total = r.scalar()
            r = await db.execute(text(f"SELECT COUNT(*) FROM {table} WHERE {col} >= :d"), {"d": date(2026,4,10)})
            last7 = r.scalar()
            print(f"  {table:<20} total={total}  last7d={last7}  {'RESEEDED' if last7 > 0 else 'NOT RESEEDED'}")

        # 3. Null sentiment columns
        print("\n=== NULL SENTIMENT COLUMNS ===")
        for col in ['sentiment','sentiment_confidence','review_text','sentiment_label','sentiment_score']:
            r = await db.execute(text(f"SELECT COUNT(*) FROM reviews WHERE {col} IS NULL"))
            nulls = r.scalar()
            print(f"  {col:<25} {'OK' if nulls == 0 else str(nulls) + ' nulls'}")

        # 4. Indexes
        print("\n=== KEY INDEXES ===")
        r = await db.execute(text("""
            SELECT indexname FROM pg_indexes 
            WHERE tablename IN ('reviews','price_history','sales_records')
            ORDER BY tablename, indexname
        """))
        for row in r.fetchall():
            print(f"  {row[0]}")

asyncio.run(check())
