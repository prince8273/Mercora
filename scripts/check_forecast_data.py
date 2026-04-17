import asyncio, asyncpg
URL = "postgresql://postgres.zjfcqwkinbjzjmrtguhz:Nd6mZ3SbF4Pen6ML@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"
async def main():
    conn = await asyncpg.connect(URL, statement_cache_size=0, timeout=15)
    row = await conn.fetchrow("SELECT id, name FROM products LIMIT 1")
    pid = row['id']
    print(f"product_id: {pid}  name: {row['name']}")
    count = await conn.fetchval("SELECT COUNT(*) FROM sales_records WHERE product_id = $1", pid)
    print(f"sales_records for this product: {count}")
    sample = await conn.fetch("SELECT date, quantity FROM sales_records WHERE product_id = $1 ORDER BY date DESC LIMIT 3", pid)
    for r in sample:
        print(f"  {r['date']}  qty={r['quantity']}")
    await conn.close()
asyncio.run(main())
