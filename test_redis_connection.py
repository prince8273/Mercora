import asyncio
import sys

try:
    import redis.asyncio as redis
except ImportError:
    print("❌ redis package not installed")
    print("Install with: pip install redis")
    sys.exit(1)

async def test_redis():
    redis_url = "redis://localhost:6379/0"
    print(f"Testing Redis connection to: {redis_url}")
    print("-" * 60)
    
    try:
        # Create client with timeout
        client = await redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        
        # Test ping
        print("Testing PING...")
        result = await asyncio.wait_for(client.ping(), timeout=5.0)
        print(f"✅ PING successful: {result}")
        
        # Test set/get
        print("\nTesting SET/GET...")
        await client.set("test_key", "test_value", ex=10)
        value = await client.get("test_key")
        print(f"✅ SET/GET successful: {value}")
        
        # Close connection
        await client.aclose()
        
        print("\n" + "=" * 60)
        print("✅ Redis connection successful!")
        print("Your backend will be able to use Redis caching.")
        return True
        
    except asyncio.TimeoutError:
        print("\n❌ Connection timeout!")
        print("Redis server is not reachable from Windows.")
        print("\nPossible solutions:")
        print("1. Check Windows Firewall settings")
        print("2. Add firewall rule: New-NetFirewallRule -DisplayName 'WSL Redis' -Direction Inbound -LocalPort 6379 -Protocol TCP -Action Allow")
        print("3. Or disable cache: Set CACHE_ENABLED=False in .env")
        return False
        
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        print("\nSet CACHE_ENABLED=False in .env to continue without cache")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_redis())
    sys.exit(0 if result else 1)
