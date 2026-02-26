"""Check system status and data connectivity"""
import asyncio
import requests
from datetime import datetime

def check_backend():
    """Check if backend is running"""
    try:
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Backend Server: RUNNING")
            print(f"   - App: {data.get('app_name')}")
            print(f"   - Version: {data.get('version')}")
            return True
        else:
            print(f"❌ Backend Server: ERROR (Status {response.status_code})")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Backend Server: NOT RUNNING")
        print("   → Start with: python -m uvicorn src.main:app --reload")
        return False
    except Exception as e:
        print(f"❌ Backend Server: ERROR - {e}")
        return False


def check_frontend():
    """Check if frontend is running"""
    try:
        response = requests.get('http://localhost:3000', timeout=5)
        if response.status_code == 200:
            print("✅ Frontend Server: RUNNING")
            print("   - URL: http://localhost:3000")
            return True
        else:
            print(f"⚠️  Frontend Server: UNEXPECTED STATUS ({response.status_code})")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Frontend Server: NOT RUNNING")
        print("   → Start with: cd frontend && npm run dev")
        return False
    except Exception as e:
        print(f"❌ Frontend Server: ERROR - {e}")
        return False


def check_api_endpoints():
    """Check if API endpoints are working"""
    print("\n📡 API Endpoints:")
    
    endpoints = [
        ('/api/v1/dashboard/stats', 'Dashboard Stats'),
        ('/api/v1/products', 'Products List'),
        ('/api/v1/ingestion/jobs', 'Ingestion Jobs'),
        ('/api/v1/ingestion/scheduled/jobs', 'Scheduled Jobs'),
    ]
    
    working = 0
    for endpoint, name in endpoints:
        try:
            response = requests.get(f'http://localhost:8000{endpoint}', timeout=5)
            if response.status_code == 200:
                print(f"   ✅ {name}: OK")
                working += 1
            else:
                print(f"   ❌ {name}: ERROR ({response.status_code})")
        except Exception as e:
            print(f"   ❌ {name}: FAILED - {e}")
    
    return working == len(endpoints)


def check_database():
    """Check database status"""
    import os
    
    db_file = "ecommerce_intelligence.db"
    if os.path.exists(db_file):
        size = os.path.getsize(db_file)
        print(f"✅ Database: EXISTS ({size:,} bytes)")
        return True
    else:
        print("❌ Database: NOT FOUND")
        print("   → Create with: python init_database.py")
        return False


async def check_database_data():
    """Check database contents"""
    try:
        from src.database import AsyncSessionLocal
        from src.models.product import Product
        from src.models.review import Review
        from src.models.tenant import Tenant
        from src.models.user import User
        from sqlalchemy import select, func
        
        async with AsyncSessionLocal() as session:
            # Count tenants
            result = await session.execute(select(func.count(Tenant.id)))
            tenant_count = result.scalar()
            
            # Count users
            result = await session.execute(select(func.count(User.id)))
            user_count = result.scalar()
            
            # Count products
            result = await session.execute(select(func.count(Product.id)))
            product_count = result.scalar()
            
            # Count reviews
            result = await session.execute(select(func.count(Review.id)))
            review_count = result.scalar()
            
            print("\n📊 Database Contents:")
            print(f"   - Tenants: {tenant_count}")
            print(f"   - Users: {user_count}")
            print(f"   - Products: {product_count}")
            print(f"   - Reviews: {review_count}")
            
            if product_count == 0:
                print("\n   ⚠️  No products found!")
                print("   → Add data with: python add_realtime_data.py")
            
            return product_count > 0
            
    except Exception as e:
        print(f"\n❌ Database Query Error: {e}")
        return False


def check_dashboard_data():
    """Check dashboard API data"""
    try:
        response = requests.get('http://localhost:8000/api/v1/dashboard/stats', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("\n📈 Dashboard Data:")
            print(f"   - Total Products: {data.get('total_products', 0)}")
            print(f"   - Active Products: {data.get('active_products', 0)}")
            print(f"   - Total Reviews: {data.get('total_reviews', 0)}")
            print(f"   - Recent Insights: {len(data.get('recent_insights', []))}")
            return True
        else:
            print(f"\n❌ Dashboard API: ERROR ({response.status_code})")
            return False
    except Exception as e:
        print(f"\n❌ Dashboard API: ERROR - {e}")
        return False


def check_proxy():
    """Check if frontend proxy is working"""
    try:
        response = requests.get('http://localhost:3000/api/v1/dashboard/stats', timeout=5)
        if response.status_code == 200:
            print("\n✅ Frontend Proxy: WORKING")
            print("   - Dashboard can fetch data from backend")
            return True
        else:
            print(f"\n❌ Frontend Proxy: ERROR ({response.status_code})")
            return False
    except Exception as e:
        print(f"\n❌ Frontend Proxy: ERROR - {e}")
        return False


async def main():
    """Main status check"""
    print("="*60)
    print("SYSTEM STATUS CHECK")
    print("="*60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check servers
    print("🖥️  Servers:")
    backend_ok = check_backend()
    frontend_ok = check_frontend()
    
    if not backend_ok:
        print("\n❌ Backend is not running. Cannot proceed with other checks.")
        print("\nTo start backend:")
        print("  python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000")
        return
    
    # Check database
    print("\n💾 Database:")
    db_exists = check_database()
    
    if db_exists:
        db_has_data = await check_database_data()
    else:
        db_has_data = False
    
    # Check API endpoints
    api_ok = check_api_endpoints()
    
    # Check dashboard data
    dashboard_ok = check_dashboard_data()
    
    # Check proxy
    if frontend_ok:
        proxy_ok = check_proxy()
    else:
        proxy_ok = False
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    all_checks = [
        ("Backend Server", backend_ok),
        ("Frontend Server", frontend_ok),
        ("Database File", db_exists),
        ("Database Data", db_has_data),
        ("API Endpoints", api_ok),
        ("Dashboard API", dashboard_ok),
        ("Frontend Proxy", proxy_ok),
    ]
    
    passed = sum(1 for _, ok in all_checks if ok)
    total = len(all_checks)
    
    for name, ok in all_checks:
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\nScore: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 All systems operational!")
        print("\n📱 Access Dashboard: http://localhost:3000/dashboard")
        print("📚 API Documentation: http://localhost:8000/docs")
    else:
        print("\n⚠️  Some issues detected. See above for details.")
        
        if not db_has_data:
            print("\n💡 Quick Fix:")
            print("   python add_realtime_data.py")
    
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
