"""Reseed Postgres dates using batch SQL — fast single-query approach."""
import asyncio, random
import asyncpg
from datetime import datetime, timedelta, date

URL = "postgresql://postgres.zjfcqwkinbjzjmrtguhz:Nd6mZ3SbF4Pen6ML@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"
TODAY = datetime.utcnow()
START = TODAY - timedelta(days=90)


async def reseed():
    conn = await asyncpg.connect(URL, statement_cache_size=0, timeout=15)
    print(f"Connected. Today: {TODAY.date()}\n")

    # Use a single UPDATE with random offset per row using Postgres random()
    # This spreads dates across 90 days without N round-trips

    print("Reseeding reviews (batch)...")
    await conn.execute("""
        UPDATE reviews
        SET created_at = $1::timestamp + (random() * ($2::timestamp - $1::timestamp)),
            updated_at = $1::timestamp + (random() * ($2::timestamp - $1::timestamp))
    """, START, TODAY)
    print("  Done")

    print("Reseeding sales_records (batch)...")
    await conn.execute("""
        UPDATE sales_records
        SET date = ($1::date + (random() * ($2::date - $1::date))::int)::date
    """, START.date(), TODAY.date())
    print("  Done")

    print("Checking price_history columns...")
    cols = await conn.fetch(
        "SELECT column_name FROM information_schema.columns WHERE table_name='price_history'"
    )
    col_names = [r['column_name'] for r in cols]
    date_col = next((c for c in col_names if 'date' in c.lower() or 'recorded' in c.lower()), None)
    print(f"  Columns: {col_names}")

    if date_col:
        print(f"Reseeding price_history.{date_col} (batch)...")
        await conn.execute(f"""
            UPDATE price_history
            SET {date_col} = ($1 + (random() * ($2 - $1)))::date
        """, START.date(), TODAY.date())
        print("  Done")
    else:
        print("  No date column found — skipping")

    # Verify
    print("\nVerification:")
    for table, col in [("reviews","created_at"), ("sales_records","date")]:
        row = await conn.fetchrow(f"SELECT COUNT(*), MIN({col}), MAX({col}) FROM {table}")
        c7  = await conn.fetchval(f"SELECT COUNT(*) FROM {table} WHERE {col} >= $1", (TODAY - timedelta(days=7)).date())
        c30 = await conn.fetchval(f"SELECT COUNT(*) FROM {table} WHERE {col} >= $1", (TODAY - timedelta(days=30)).date())
        c90 = await conn.fetchval(f"SELECT COUNT(*) FROM {table} WHERE {col} >= $1", (TODAY - timedelta(days=90)).date())
        status = "RESEEDED" if c7 > 0 else "FAILED"
        print(f"  {table:<20} total={row[0]}  7d={c7}  30d={c30}  90d={c90}  [{status}]")

    await conn.close()
    print("\nDone!")

asyncio.run(reseed())
