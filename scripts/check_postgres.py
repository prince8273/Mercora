"""Direct Postgres check — bypasses pydantic settings cache."""
import asyncio
import asyncpg
from datetime import datetime, timedelta

URL = "postgresql://postgres.zjfcqwkinbjzjmrtguhz:Nd6mZ3SbF4Pen6ML@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"

async def check():
    # statement_cache_size=0 required for Supabase transaction pooler (pgbouncer)
    conn = await asyncpg.connect(URL, statement_cache_size=0, timeout=15)
    today = datetime.utcnow()
    print(f"Postgres — {today.date()}\n")

    # Check price_history column name
    ph_cols = await conn.fetch(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name='price_history' ORDER BY ordinal_position"
    )
    ph_col_names = [r['column_name'] for r in ph_cols]
    ph_date = next((c for c in ph_col_names if 'date' in c or 'recorded' in c), None)
    print(f"price_history date column: {ph_date}\n")

    for table, col, label in [
        ("reviews",       "created_at", "REVIEWS"),
        ("sales_records", "date",       "SALES"),
        ("price_history", ph_date,      "PRICE HISTORY"),
    ]:
        if not col:
            print(f"{label}: no date column found\n")
            continue

        row = await conn.fetchrow(f"SELECT COUNT(*), MIN({col}), MAX({col}) FROM {table}")
        total, mn, mx = row[0], row[1], row[2]

        counts = {}
        for days in [7, 30, 90]:
            cutoff = (today - timedelta(days=days)).date()
            r = await conn.fetchval(f"SELECT COUNT(*) FROM {table} WHERE {col} >= $1", cutoff)
            counts[days] = r

        reseeded = "RESEEDED" if counts[7] > 0 else "NOT RESEEDED"
        print(f"{label}")
        print(f"  Total: {total}  |  Range: {str(mn)[:10]} -> {str(mx)[:10]}")
        print(f"  7d: {counts[7]}  |  30d: {counts[30]}  |  90d: {counts[90]}  [{reseeded}]")
        print()

    await conn.close()

asyncio.run(check())
