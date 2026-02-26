"""Check what keys are actually in Redis"""
import asyncio
import redis.asyncio as redis


async def check_keys():
    r = await redis.from_url("redis://localhost:6379", encoding="utf-8", decode_responses=True)
    
    try:
        # Get all keys
        keys = []
        async for key in r.scan_iter(match="*"):
            keys.append(key)
        
        print(f"Found {len(keys)} keys in Redis:")
        for key in sorted(keys)[:20]:  # Show first 20
            print(f"  {key}")
            
    finally:
        await r.aclose()


if __name__ == "__main__":
    asyncio.run(check_keys())
