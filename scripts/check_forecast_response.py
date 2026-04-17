import asyncio, asyncpg, json
URL = "postgresql://postgres.zjfcqwkinbjzjmrtguhz:Nd6mZ3SbF4Pen6ML@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"
async def main():
    conn = await asyncpg.connect(URL, statement_cache_size=0, timeout=15)
    # Find Women's Summer Floral Dress
    row = await conn.fetchrow("""
        SELECT p.id, p.name, COUNT(s.id) as cnt
        FROM products p
        JOIN sales_records s ON s.product_id = p.id
        WHERE p.name ILIKE '%floral%' OR p.name ILIKE '%dress%'
        GROUP BY p.id, p.name
        ORDER BY cnt DESC LIMIT 1
    """)
    if row:
        print(f"product: {row['name']}  sales: {row['cnt']}")
        # Sample sales records
        sales = await conn.fetch(
            "SELECT date, quantity FROM sales_records WHERE product_id = $1 ORDER BY date DESC LIMIT 5",
            row['id']
        )
        print("Recent sales:")
        for s in sales:
            print(f"  {s['date']}  qty={s['quantity']}")
    else:
        print("No matching product found")
    await conn.close()
asyncio.run(main())
