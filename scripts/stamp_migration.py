"""Stamp alembic_version table directly via asyncpg."""
import asyncio
import asyncpg

URL = "postgresql://postgres.zjfcqwkinbjzjmrtguhz:Nd6mZ3SbF4Pen6ML@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"

async def main():
    conn = await asyncpg.connect(URL, statement_cache_size=0, timeout=15)

    current = await conn.fetchval("SELECT version_num FROM alembic_version LIMIT 1")
    print(f"Current alembic version: {current}")

    await conn.execute(
        "UPDATE alembic_version SET version_num = $1",
        "add_error_message_001"
    )
    print("Stamped alembic_version -> add_error_message_001")

    await conn.close()

asyncio.run(main())
