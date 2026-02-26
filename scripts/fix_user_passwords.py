"""Fix user passwords with proper bcrypt hashes"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from passlib.context import CryptContext
from sqlalchemy import select
from src.database import get_db
from src.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def fix_passwords():
    # Create a proper bcrypt hash for password "password123"
    hashed_password = pwd_context.hash("password123")
    print(f"Generated hash: {hashed_password}")
    
    async for db in get_db():
        # Get all users
        result = await db.execute(select(User))
        users = result.scalars().all()
        
        print(f"\nUpdating {len(users)} users...")
        
        for user in users:
            user.hashed_password = hashed_password
            print(f"  - Updated {user.email}")
        
        await db.commit()
        print("\nAll users updated successfully!")
        print("\nYou can now login with:")
        print("  Email: seller@tenant-001.com (or 002, 003, 004)")
        print("  Password: password123")
        break

if __name__ == "__main__":
    asyncio.run(fix_passwords())
