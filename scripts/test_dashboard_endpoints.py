"""Test dashboard endpoints with authentication"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# Login credentials
LOGIN_DATA = {
    "email": "seller@tenant-001.com",
    "password": "password123"
}

def test_login():
    """Test login and get token"""
    print("Testing login...")
    response = requests.post(f"{BASE_URL}/auth/login", json=LOGIN_DATA)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Login successful! Token: {data['access_token'][:50]}...")
        return data['access_token']
    else:
        print(f"Login failed: {response.text}")
        return None

def test_dashboard_endpoints(token):
    """Test all dashboard endpoints"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    endpoints = [
        "/dashboard/kpis",
        "/dashboard/insights",
        "/dashboard/alerts",
        "/dashboard/trends"
    ]
    
    for endpoint in endpoints:
        print(f"\n{'='*60}")
        print(f"Testing: {endpoint}")
        print('='*60)
        
        response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)[:500]}...")
        else:
            print(f"Error: {response.text}")

if __name__ == "__main__":
    # Login first
    token = test_login()
    
    if token:
        # Test dashboard endpoints
        test_dashboard_endpoints(token)
    else:
        print("Cannot test endpoints without authentication token")
