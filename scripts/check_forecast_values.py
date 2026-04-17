import asyncio, asyncpg, sys
sys.path.insert(0, '.')
from src.agents.demand_forecast_agent import DemandForecastAgent
from uuid import UUID

URL = "postgresql://postgres.zjfcqwkinbjzjmrtguhz:Nd6mZ3SbF4Pen6ML@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"

async def main():
    conn = await asyncpg.connect(URL, statement_cache_size=0, timeout=15)
    row = await conn.fetchrow("""
        SELECT p.id, p.name, p.tenant_id
        FROM products p
        JOIN sales_records s ON s.product_id = p.id
        WHERE p.name ILIKE '%floral%' OR p.name ILIKE '%dress%'
        GROUP BY p.id, p.name, p.tenant_id
        HAVING COUNT(s.id) > 5
        LIMIT 1
    """)
    pid = row['id']
    tid = row['tenant_id']
    print(f"Product: {row['name']}")

    sales = await conn.fetch(
        "SELECT date, quantity FROM sales_records WHERE product_id = $1 ORDER BY date ASC",
        pid
    )
    print(f"Sales records: {len(sales)}")
    sales_history = [{"date": str(r["date"]), "quantity": r["quantity"]} for r in sales]

    agent = DemandForecastAgent(tenant_id=tid)
    result = agent.forecast_demand(
        product_id=pid,
        product_name=row['name'],
        sales_history=sales_history,
        forecast_horizon_days=30,
        current_inventory=None
    )
    d = result.to_dict()
    pts = d["forecast_points"]
    print(f"Forecast points: {len(pts)}")
    print("First 5 predicted_quantity values:")
    for p in pts[:5]:
        print(f"  {p['date']}  predicted={p['predicted_quantity']}  lower={p['lower_bound']}  upper={p['upper_bound']}")

    await conn.close()

asyncio.run(main())
