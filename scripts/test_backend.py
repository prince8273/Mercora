"""Test backend connection to Mock API and Redis cache"""
import asyncio
import httpx

BACKEND_URL = "http://localhost:8000"
TENANT_ID = "54d459ab-4ae8-480a-9d1c-d53b218a4fb2"

async def test_login():
    """Login to get JWT token"""
    print("🔐 Testing login...")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json={
                "email": "seller@tenant-001.com",
                "password": "password123"
            }
        )
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print(f"✅ Login successful! Token: {token[:20]}...")
            return token
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return None

async def test_dashboard_kpis(token: str):
    """Test dashboard KPIs endpoint (should use cache + Mock API)"""
    print("\n📊 Testing dashboard KPIs...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        # First request - should be Cache MISS
        print("   Request 1 (should be Cache MISS)...")
        response1 = await client.get(
            f"{BACKEND_URL}/api/v1/dashboard/kpis",
            headers=headers
        )
        print(f"   Status: {response1.status_code}")
        if response1.status_code == 200:
            data1 = response1.json()
            print(f"   Data: {data1}")
        else:
            print(f"   Error: {response1.text}")
        
        # Second request - should be Cache HIT
        print("\n   Request 2 (should be Cache HIT)...")
        response2 = await client.get(
            f"{BACKEND_URL}/api/v1/dashboard/kpis",
            headers=headers
        )
        print(f"   Status: {response2.status_code}")
        if response2.status_code == 200:
            data2 = response2.json()
            print(f"   Data: {data2}")
        else:
            print(f"   Error: {response2.text}")

async def main():
    print("=" * 60)
    print("BACKEND CONNECTION TEST")
    print("=" * 60)
    
    token = await test_login()
    if token:
        await test_dashboard_kpis(token)
    
    print("\n" + "=" * 60)
    print("Check backend logs for:")
    print("  - DataService initialized: DATA_SOURCE=mock_api, MOCK_API_URL=...")
    print("  - Cache MISS/HIT messages")
    print("  - Mock API fetch logs")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
