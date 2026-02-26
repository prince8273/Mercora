"""Clean up old tenant records with invalid UUIDs"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from sqlalchemy import text
from src.database import get_db

async def clean():
    async for db in get_db():
        # Delete old tenants with string IDs
        await db.execute(text("DELETE FROM tenants WHERE slug IN ('techgear-pro', 'homestyle-living', 'fitlife-sports', 'bookworm-treasures')"))
        await db.commit()
        print("Cleaned old tenants")
        break

if __name__ == "__main__":
    asyncio.run(clean())
