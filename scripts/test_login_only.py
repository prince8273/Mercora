"""Test login endpoint only"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# Test with correct credentials
print("Testing login with correct credentials...")
response = requests.post(
    f"{BASE_URL}/auth/login",
    json={
        "email": "seller@tenant-001.com",
        "password": "password123"
    }
)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

# Test with wrong credentials
print("\n" + "="*60)
print("Testing login with wrong credentials...")
response = requests.post(
    f"{BASE_URL}/auth/login",
    json={
        "email": "wrong@email.com",
        "password": "wrongpassword"
    }
)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
