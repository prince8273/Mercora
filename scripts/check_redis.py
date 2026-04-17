import asyncio, sys, os
sys.path.insert(0, '.')

# Read REDIS_URL directly from .env to bypass cached settings
redis_url = "redis://127.0.0.1:6379/0"
for line in open(".env"):
    line = line.strip()
    if line.startswith("REDIS_URL="):
        redis_url = line.split("=", 1)[1].strip()
        break

print(f"Testing Redis URL: {redis_url}")

from src.cache.cache_manager import CacheManager

async def check():
    cm = CacheManager(redis_url=redis_url, use_memory_fallback=False)
    await cm.connect()
    if cm._redis:
        pong = await cm._redis.ping()
        print(f"PING: {pong}")
        await cm.set(key="test:key", value="hello", ttl=30)
        val = await cm.get(key="test:key")
        print(f"Set/Get: {val}")
        info = await cm._redis.info("server")
        print(f"Redis version: {info['redis_version']}")
        print("Redis is working!")
        await cm.disconnect()
    else:
        print("Redis NOT connected")
        print("Run in WSL: sudo service redis-server start")

asyncio.run(check())
