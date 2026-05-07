#!/usr/bin/env python3
"""
System integration test script
Tests all major endpoints and functionality
"""

import requests
import time
import json
import sys

BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:8080"

def test_health():
    """Test health endpoints"""
    print("\n=== Testing Health Endpoints ===")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✓ Health check: {response.status_code}")
        return True
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False

def test_login():
    """Test login endpoint"""
    print("\n=== Testing Login ===")
    try:
        # Test with correct credentials
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login-json",
            json={"email": "admin@laos.gov.in", "password": "Admin@123456"}
        )
        print(f"Status: {response.status_code}")
        data = response.json()
        
        if response.status_code == 200:
            print(f"✓ Login successful")
            print(f"  - Access Token: {data['access_token'][:20]}...")
            print(f"  - Token Type: {data['token_type']}")
            print(f"  - Expires In: {data['expires_in_seconds']}s")
            return data['access_token']
        else:
            print(f"✗ Login failed: {data}")
            return None
    except Exception as e:
        print(f"✗ Login test failed: {e}")
        return None

def test_get_current_user(token):
    """Test getting current user"""
    print("\n=== Testing Get Current User ===")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/api/v1/auth/me",
            headers=headers
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Current user retrieved")
            print(f"  - Email: {data['email']}")
            print(f"  - Full Name: {data['full_name']}")
            print(f"  - Role: {data['role']}")
            return True
        else:
            print(f"✗ Failed to get user: {response.json()}")
            return False
    except Exception as e:
        print(f"✗ Get current user failed: {e}")
        return False

def test_dashboard(token):
    """Test dashboard endpoint"""
    print("\n=== Testing Dashboard ===")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/api/v1/dashboard/summary",
            headers=headers
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Dashboard data retrieved")
            print(f"  - Keys: {list(data.keys())}")
            return True
        else:
            print(f"✗ Failed to get dashboard: {response.json()}")
            return False
    except Exception as e:
        print(f"✗ Dashboard test failed: {e}")
        return False

def test_documents(token):
    """Test documents endpoint"""
    print("\n=== Testing Documents ===")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/api/v1/documents",
            headers=headers
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Documents retrieved")
            print(f"  - Count: {len(data.get('documents', []))}")
            return True
        else:
            print(f"✗ Failed to get documents: {response.json()}")
            return False
    except Exception as e:
        print(f"✗ Documents test failed: {e}")
        return False

def main():
    print("=" * 50)
    print("LAOS System Integration Tests")
    print("=" * 50)
    
    # Test health
    if not test_health():
        print("\n✗ Backend is not running!")
        print(f"Make sure the backend is running on {BASE_URL}")
        sys.exit(1)
    
    # Test login
    token = test_login()
    if not token:
        print("\n✗ Login failed!")
        sys.exit(1)
    
    # Test authenticated endpoints
    test_get_current_user(token)
    test_dashboard(token)
    test_documents(token)
    
    print("\n" + "=" * 50)
    print("✓ All tests completed!")
    print("=" * 50)
    print("\nNext steps:")
    print(f"1. Open frontend: {FRONTEND_URL}")
    print("2. Login with:")
    print("   - Email: admin@laos.gov.in")
    print("   - Password: Admin@123456")

if __name__ == "__main__":
    main()
