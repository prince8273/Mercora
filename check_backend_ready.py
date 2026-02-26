#!/usr/bin/env python3
"""
Quick script to check if the backend is ready for data population.
"""

import requests
import sys

BASE_URL = "http://localhost:8000"

def check_backend():
    """Check if backend is accessible"""
    print("🔍 Checking backend status...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running")
            return True
        else:
            print(f"⚠️  Backend returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Backend is not running at http://localhost:8000")
        print("   Please start the backend server first:")
        print("   cd backend && uvicorn src.main:app --reload")
        return False
    except requests.exceptions.Timeout:
        print("❌ Backend request timed out")
        return False
    except Exception as e:
        print(f"❌ Error checking backend: {e}")
        return False

def check_auth():
    """Check if authentication endpoint works"""
    print("🔍 Checking authentication endpoint...")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data={"username": "demo@example.com", "password": "demo123"},
            timeout=5
        )
        if response.status_code == 200:
            print("✅ Authentication works")
            return True
        elif response.status_code == 401:
            print("⚠️  Demo account not found or wrong credentials")
            print("   Please create demo account first:")
            print("   Email: demo@example.com")
            print("   Password: demo123")
            return False
        else:
            print(f"⚠️  Auth endpoint returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error checking auth: {e}")
        return False

def check_csv_file():
    """Check if test_products.csv exists"""
    print("🔍 Checking for test_products.csv...")
    try:
        with open("test_products.csv", "r") as f:
            lines = sum(1 for _ in f)
            print(f"✅ test_products.csv found ({lines-1} products)")
            return True
    except FileNotFoundError:
        print("❌ test_products.csv not found")
        print("   Please ensure the file is in the current directory")
        return False

if __name__ == "__main__":
    print("="*60)
    print("🔧 BACKEND READINESS CHECK")
    print("="*60)
    
    backend_ok = check_backend()
    auth_ok = check_auth() if backend_ok else False
    csv_ok = check_csv_file()
    
    print("\n" + "="*60)
    if backend_ok and auth_ok and csv_ok:
        print("✅ ALL CHECKS PASSED - Ready to populate data!")
        print("="*60)
        print("\nRun: python populate_test_data.py")
        sys.exit(0)
    else:
        print("❌ SOME CHECKS FAILED - Please fix issues above")
        print("="*60)
        sys.exit(1)
