import asyncio, asyncpg
URL = "postgresql://postgres.zjfcqwkinbjzjmrtguhz:Nd6mZ3SbF4Pen6ML@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"
async def main():
    conn = await asyncpg.connect(URL, statement_cache_size=0, timeout=15)
    # Find a product that actually has sales records
    row = await conn.fetchrow("""
        SELECT p.id, p.name, COUNT(s.id) as cnt
        FROM products p
        JOIN sales_records s ON s.product_id = p.id
        GROUP BY p.id, p.name
        ORDER BY cnt DESC
        LIMIT 1
    """)
    if row:
        print(f"product_id: {row['id']}")
        print(f"name: {row['name']}")
        print(f"sales_records: {row['cnt']}")
    else:
        total = await conn.fetchval("SELECT COUNT(*) FROM sales_records")
        print(f"No products with sales records. Total sales_records: {total}")
    await conn.close()
asyncio.run(main())
