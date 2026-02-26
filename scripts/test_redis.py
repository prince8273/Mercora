"""Test Redis connection from Windows to WSL"""
import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import redis.asyncio as redis
from dotenv import load_dotenv

load_dotenv()

# Parse Redis URL
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
print(f"Testing Redis connection...")
print(f"Redis URL: {REDIS_URL}")
print("-" * 50)


async def test():
    try:
        # Create Redis client
        client = redis.from_url(REDIS_URL, decode_responses=True)
        
        # Test 1: Ping
        print("Test 1: Ping Redis...")
        result = await client.ping()
        print(f"✅ Redis ping successful! Result: {result}")
        
        # Test 2: Set a key
        print("\nTest 2: Set a test key...")
        await client.set("test_key", "hello_from_windows", ex=10)
        print("✅ Redis set successful!")
        
        # Test 3: Get the key
        print("\nTest 3: Get the test key...")
        val = await client.get("test_key")
        print(f"✅ Redis get successful! Value: {val}")
        
        # Test 4: Delete the key
        print("\nTest 4: Delete the test key...")
        await client.delete("test_key")
        print("✅ Redis delete successful!")
        
        # Close connection
        await client.aclose()
        
        print("\n" + "=" * 50)
        print("✅ ALL TESTS PASSED - Redis is fully working!")
        print("=" * 50)
        return True
        
    except Exception as e:
        print(f"\n❌ Redis connection failed!")
        print(f"Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure Redis is running in WSL: wsl redis-cli ping")
        print("2. Check Redis is listening on 0.0.0.0: wsl sudo ss -tlnp | grep 6379")
        print("3. Verify REDIS_URL in .env uses WSL IP (not localhost)")
        print(f"4. Current REDIS_URL: {REDIS_URL}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test())
    sys.exit(0 if success else 1)
