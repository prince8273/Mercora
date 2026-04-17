import asyncio, asyncpg
URL = "postgresql://postgres.zjfcqwkinbjzjmrtguhz:Nd6mZ3SbF4Pen6ML@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"
async def main():
    conn = await asyncpg.connect(URL, statement_cache_size=0, timeout=15)
    await conn.execute("UPDATE alembic_version SET version_num = 'fix_confidence_precision_001'")
    print("Stamped -> fix_confidence_precision_001")
    await conn.close()
asyncio.run(main())
