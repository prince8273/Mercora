"""Test dashboard API endpoint"""
import requests
import json

try:
    print("Testing dashboard API endpoint...")
    response = requests.get('http://localhost:8000/api/v1/dashboard/stats', timeout=10)
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"\nResponse Headers:")
    for key, value in response.headers.items():
        print(f"  {key}: {value}")
    
    if response.status_code == 200:
        print(f"\n✅ API Response:")
        data = response.json()
        print(json.dumps(data, indent=2))
    else:
        print(f"\n❌ Error Response:")
        print(response.text)
        
except requests.exceptions.ConnectionError as e:
    print(f"❌ Connection Error: Cannot connect to backend server")
    print(f"   Make sure the server is running on http://localhost:8000")
except Exception as e:
    print(f"❌ Error: {e}")
