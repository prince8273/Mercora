"""
Quick test script to verify all API endpoints are working
Run this after starting the backend server
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_endpoint(method, endpoint, data=None, description=""):
    """Test a single endpoint"""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"{method} {endpoint}")
    print(f"{'='*60}")
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        else:
            print(f"Unsupported method: {method}")
            return False
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS")
            # Print first 500 chars of response
            response_text = json.dumps(response.json(), indent=2)
            if len(response_text) > 500:
                print(response_text[:500] + "...")
            else:
                print(response_text)
            return True
        else:
            print(f"❌ FAILED: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ FAILED: Could not connect to server. Is it running?")
        return False
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False


def main():
    print("\n" + "="*60)
    print("API ENDPOINT TESTING")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    print("Make sure the backend server is running!")
    print("="*60)
    
    results = []
    
    # Test health check
    results.append(test_endpoint(
        "GET", 
        "/health",
        description="Health Check"
    ))
    
    # Test root endpoint
    results.append(test_endpoint(
        "GET",
        "/",
        description="Root Endpoint"
    ))
    
    # Test dashboard stats
    results.append(test_endpoint(
        "GET",
        "/api/v1/dashboard/stats",
        description="Dashboard Statistics"
    ))
    
    # Test dashboard recent activity
    results.append(test_endpoint(
        "GET",
        "/api/v1/dashboard/recent-activity?limit=5",
        description="Dashboard Recent Activity"
    ))
    
    # Test analytics
    results.append(test_endpoint(
        "GET",
        "/api/v1/analytics?time_range=7d",
        description="Analytics (7 days)"
    ))
    
    # Test analytics product performance
    results.append(test_endpoint(
        "GET",
        "/api/v1/analytics/product-performance?limit=5",
        description="Product Performance"
    ))
    
    # Test query history
    results.append(test_endpoint(
        "GET",
        "/api/v1/history?limit=10",
        description="Query History"
    ))
    
    # Test products list
    results.append(test_endpoint(
        "GET",
        "/api/v1/products",
        description="Products List"
    ))
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n✅ All tests passed!")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed")
    
    print("="*60)


if __name__ == "__main__":
    main()
