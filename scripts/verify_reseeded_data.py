import asyncio, sys
sys.path.insert(0, '.')
from sqlalchemy import text
from src.database import AsyncSessionLocal
from datetime import datetime, timedelta

async def check():
    async with AsyncSessionLocal() as db:
        today = datetime.utcnow()
        
        checks = [
            ('reviews',       'created_at', 'REVIEWS'),
            ('sales_records', 'date',       'SALES'),
            ('price_history', 'price_date', 'PRICE HISTORY'),
        ]
        
        print(f"Today: {today.date()}\n")
        
        for table, col, label in checks:
            r = await db.execute(text(f"SELECT COUNT(*), MIN({col}), MAX({col}) FROM {table}"))
            row = r.fetchone()
            total, mn, mx = row[0], row[1], row[2]
            
            # Count per window
            counts = {}
            for days in [7, 30, 90]:
                if 'date' in col and col != 'created_at':
                    cutoff = (today - timedelta(days=days)).date()
                else:
                    cutoff = today - timedelta(days=days)
                r2 = await db.execute(text(f"SELECT COUNT(*) FROM {table} WHERE {col} >= :c"), {"c": cutoff})
                counts[days] = r2.scalar()
            
            print(f"{label}")
            print(f"  Total: {total}  |  Range: {str(mn)[:10]} -> {str(mx)[:10]}")
            print(f"  7d: {counts[7]}  |  30d: {counts[30]}  |  90d: {counts[90]}")
            print()

asyncio.run(check())
