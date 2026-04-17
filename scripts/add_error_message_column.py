"""Add missing error_message column to query_history table."""
import asyncio
import asyncpg

URL = "postgresql://postgres.zjfcqwkinbjzjmrtguhz:Nd6mZ3SbF4Pen6ML@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"

async def main():
    conn = await asyncpg.connect(URL, statement_cache_size=0, timeout=15)

    # Check if column already exists
    exists = await conn.fetchval(
        "SELECT COUNT(*) FROM information_schema.columns "
        "WHERE table_name='query_history' AND column_name='error_message'"
    )

    if exists:
        print("Column 'error_message' already exists — nothing to do.")
    else:
        await conn.execute("ALTER TABLE query_history ADD COLUMN error_message VARCHAR")
        print("Column 'error_message' added successfully.")

    await conn.close()

asyncio.run(main())
