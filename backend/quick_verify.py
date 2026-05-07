#!/usr/bin/env python3
"""LAOS Backend - Quick Verification Script"""

import httpx
import json
import time

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

print("=" * 80)
print(" LAOS BACKEND - QUICK VERIFICATION")
print("=" * 80)
print()

# Test 1: Health check
print("[1] Health Check")
print("-" * 80)
try:
    with httpx.Client(timeout=5.0) as client:
        # Try with trailing slash
        response = client.get(f"{BASE_URL}/health/", follow_redirects=True)
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Response: {json.dumps(data, indent=2)[:200]}...")
        else:
            print(f"  Error: {response.text[:200]}")
except Exception as e:
    print(f"  ERROR: {e}")

print()

# Test 2: Root endpoint
print("[2] Root Endpoint")
print("-" * 80)
try:
    with httpx.Client(timeout=5.0) as client:
        response = client.get(f"{BASE_URL}/")
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  App: {data.get('app')}")
            print(f"  Version: {data.get('version')}")
        else:
            print(f"  Error: {response.text[:100]}")
except Exception as e:
    print(f"  ERROR: {e}")

print()

# Test 3: Login with correct form encoding
print("[3] Login (Form-encoded)")
print("-" * 80)
try:
    with httpx.Client(timeout=5.0) as client:
        # Use form data instead of JSON
        response = client.post(
            f"{API_BASE}/auth/login",
            data={"username": "admin@laos.gov.in", "password": "Admin@123456"}
        )
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token", "")
            print(f"  Token: {token[:40]}...")
            print(f"  Token Type: {data.get('token_type')}")
        else:
            print(f"  Error: {response.text[:300]}")
except Exception as e:
    print(f"  ERROR: {e}")

print()

# Test 4: Swagger docs
print("[4] Swagger Docs")
print("-" * 80)
try:
    with httpx.Client(timeout=5.0) as client:
        response = client.get(f"{BASE_URL}/docs")
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            print(f"  [OK] Swagger UI accessible")
        else:
            print(f"  Error: {response.status_code}")
except Exception as e:
    print(f"  ERROR: {e}")

print()

# Test 5: OpenAPI schema
print("[5] OpenAPI Schema")
print("-" * 80)
try:
    with httpx.Client(timeout=5.0) as client:
        response = client.get(f"{BASE_URL}/openapi.json")
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            num_paths = len(data.get("paths", {}))
            print(f"  Endpoints documented: {num_paths}")
        else:
            print(f"  Error: {response.status_code}")
except Exception as e:
    print(f"  ERROR: {e}")

print()

# Test 6: Ollama
print("[6] Ollama Service")
print("-" * 80)
try:
    with httpx.Client(timeout=5.0) as client:
        response = client.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            data = response.json()
            models = [m.get("name") for m in data.get("models", [])]
            print(f"  Status: RUNNING")
            print(f"  Models: {models}")
        else:
            print(f"  Error: {response.status_code}")
except Exception as e:
    print(f"  ERROR: {e}")

print()
print("=" * 80)
