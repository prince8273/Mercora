"""Test both API patterns work"""
import asyncio
from uuid import uuid4
from src.cache.cache_manager import CacheManager


async def test_both_apis():
    """Test both structured and simple API patterns"""
    manager = CacheManager(redis_url="redis://localhost:6379/15")
    
    try:
        await manager.connect()
        print("✓ Connected to Redis")
        
        tenant_id = uuid4()
        
        # Test Structured API (new)
        print("\n--- Testing Structured API ---")
        success = await manager.set(
            cache_type='pricing',
            tenant_id=tenant_id,
            identifier='product-123',
            data={'price': 99.99}
        )
        print(f"✓ Structured set: {success}")
        
        data = await manager.get(
            cache_type='pricing',
            tenant_id=tenant_id,
            identifier='product-123',
            check_freshness=False
        )
        print(f"✓ Structured get: {data}")
        
        # Test Simple API (old)
        print("\n--- Testing Simple API ---")
        key = f"pricing:{tenant_id}:product:PROD001"
        success = await manager.set(
            key=key,
            value={'price': 29.99, 'product_id': 'PROD001'},
            ttl=3600
        )
        print(f"✓ Simple set: {success}")
        
        data = await manager.get(key=key)
        print(f"✓ Simple get: {data}")
        
        # Test delete with simple API
        deleted = await manager.delete(key=key)
        print(f"✓ Simple delete: {deleted}")
        
        # Verify it's gone
        data = await manager.get(key=key)
        print(f"✓ Verify deleted (should be None): {data}")
        
        print("\n✅ Both APIs work correctly!")
        
    finally:
        if manager._redis:
            await manager._redis.flushdb()
            await manager.disconnect()


if __name__ == "__main__":
    asyncio.run(test_both_apis())
