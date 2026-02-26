"""Test if frontend proxy is working"""
import requests

try:
    # Test through the frontend proxy (port 3000)
    print("Testing through frontend proxy (http://localhost:3000/api/v1/dashboard/stats)...")
    response = requests.get('http://localhost:3000/api/v1/dashboard/stats', timeout=10)
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("✅ Frontend proxy is working!")
        print(f"Response: {response.json()}")
    else:
        print(f"❌ Proxy returned error: {response.status_code}")
        print(response.text)
        
except requests.exceptions.Timeout:
    print("❌ Request timed out - proxy might not be forwarding requests")
except requests.exceptions.ConnectionError:
    print("❌ Connection error - frontend server might not be running")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*60)

try:
    # Test direct backend (port 8000)
    print("\nTesting direct backend (http://localhost:8000/api/v1/dashboard/stats)...")
    response = requests.get('http://localhost:8000/api/v1/dashboard/stats', timeout=10)
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("✅ Backend is working!")
    else:
        print(f"❌ Backend returned error: {response.status_code}")
        
except Exception as e:
    print(f"❌ Error: {e}")
