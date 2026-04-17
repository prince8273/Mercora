import asyncio, httpx, json, os
from dotenv import load_dotenv
load_dotenv()

BASE = "http://localhost:8000"

async def main():
    # Login first
    async with httpx.AsyncClient() as client:
        login = await client.post(f"{BASE}/api/v1/auth/login", json={
            "email": "admin@mercora.com", "password": "admin123"
        })
        if login.status_code != 200:
            # try form login
            login = await client.post(f"{BASE}/api/v1/auth/token", data={
                "username": "admin@mercora.com", "password": "admin123"
            })
        print("Login status:", login.status_code)
        token = login.json().get("access_token")
        if not token:
            print("Login response:", login.text[:500])
            return

        headers = {"Authorization": f"Bearer {token}"}

        # Get products
        products = await client.get(f"{BASE}/api/v1/products", headers=headers)
        prods = products.json()
        items = prods.get("data") or prods.get("items") or prods
        if isinstance(items, list):
            for p in items[:5]:
                print(f"  {p.get('id')} - {p.get('name')}")

asyncio.run(main())
