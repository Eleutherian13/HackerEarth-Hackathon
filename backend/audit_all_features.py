#!/usr/bin/env python3
"""LAOS Backend - Complete Feature Audit"""

import httpx
import json
import time
import sys
from typing import Tuple, Dict, List

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"
OLLAMA_URL = "http://localhost:11434"

# Test results
results = {
    "PASS": [],
    "FAIL": [],
    "SKIP": [],
    "TOTAL": 0
}

def test(name: str, method: str, url: str, headers: Dict = None, json_data: Dict = None, 
         expected_status: int = 200, success_check=None) -> bool:
    """Test an endpoint"""
    results["TOTAL"] += 1
    
    try:
        with httpx.Client(timeout=10.0) as client:
            if method == "GET":
                response = client.get(url, headers=headers)
            elif method == "POST":
                response = client.post(url, headers=headers, json=json_data)
            else:
                return False
            
            # Check status
            if isinstance(expected_status, list):
                status_ok = response.status_code in expected_status
            else:
                status_ok = response.status_code == expected_status
            
            # Check success condition if provided
            if success_check and status_ok:
                try:
                    data = response.json()
                    success = success_check(data)
                except:
                    success = False
            else:
                success = status_ok
            
            if success:
                results["PASS"].append(name)
                print(f"  [PASS] {name}")
                return True
            else:
                results["FAIL"].append(f"{name} (HTTP {response.status_code})")
                print(f"  [FAIL] {name} (HTTP {response.status_code})")
                if response.status_code >= 400:
                    try:
                        print(f"         Response: {response.text[:200]}")
                    except:
                        pass
                return False
                
    except httpx.ConnectError:
        results["FAIL"].append(f"{name} (Connection refused)")
        print(f"  [FAIL] {name} (Connection refused)")
        return False
    except Exception as e:
        results["FAIL"].append(f"{name} ({str(e)[:50]})")
        print(f"  [FAIL] {name} ({str(e)[:50]})")
        return False

def get_token() -> str:
    """Get auth token"""
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                f"{API_BASE}/auth/login",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                content="username=admin@laos.gov.in&password=Admin@123456"
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("access_token", "")
    except:
        pass
    return ""

print("=" * 80)
print(" LAOS BACKEND - COMPLETE FEATURE AUDIT")
print("=" * 80)
print()

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1: HEALTH & CONNECTIVITY
# ─────────────────────────────────────────────────────────────────────────────

print("[1] HEALTH & CONNECTIVITY")
print("-" * 80)

test("Health Endpoint", "GET", f"{BASE_URL}/health", expected_status=200)

# Try with different timeouts to see if service is truly running
time.sleep(2)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2: AUTHENTICATION
# ─────────────────────────────────────────────────────────────────────────────

print()
print("[2] AUTHENTICATION")
print("-" * 80)

# Get token for subsequent tests
token = get_token()
if token:
    print(f"  [INFO] Token obtained: {token[:30]}...")
    auth_header = {"Authorization": f"Bearer {token}"}
else:
    print(f"  [SKIP] Could not obtain auth token")
    auth_header = None

# Test 2.1: Login
test("Login Endpoint", "POST", f"{API_BASE}/auth/login",
     headers={"Content-Type": "application/x-www-form-urlencoded"},
     json_data=None,
     expected_status=200,
     success_check=lambda d: "access_token" in d and "token_type" in d)

# Test 2.2: User Registration
test("User Registration", "POST", f"{API_BASE}/auth/register",
     json_data={
         "email": f"test_{int(time.time())}@laos.gov.in",
         "full_name": "Test User",
         "password": "Test@123456",
         "role": "REVIEWER"
     },
     expected_status=[200, 201],
     success_check=lambda d: "id" in d or "email" in d)

# Test 2.3: Get Current User (requires token)
if auth_header:
    test("Get Current User", "GET", f"{API_BASE}/auth/me",
         headers=auth_header,
         expected_status=200,
         success_check=lambda d: "email" in d)
else:
    results["SKIP"].append("Get Current User")

# Test 2.4: Token Refresh
if auth_header:
    test("Token Refresh", "POST", f"{API_BASE}/auth/refresh",
         headers=auth_header,
         expected_status=200,
         success_check=lambda d: "access_token" in d)
else:
    results["SKIP"].append("Token Refresh")

# Test 2.5: Invalid Login (should return 401)
test("Invalid Login Rejection", "POST", f"{API_BASE}/auth/login",
     headers={"Content-Type": "application/x-www-form-urlencoded"},
     json_data=None,
     expected_status=401)

# Test 2.6: Protected Route Without Token (should return 401)
test("Protected Route Without Auth", "GET", f"{API_BASE}/documents/",
     expected_status=401)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3: PDF UPLOAD & DOCUMENT MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────

print()
print("[3] PDF UPLOAD & DOCUMENT MANAGEMENT")
print("-" * 80)

if not auth_header:
    print("  [SKIP] Skipping - no authentication token")
else:
    # Create a test PDF
    try:
        from fpdf import FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'TEST JUDGMENT WP(C) 1234/2024', ln=True)
        pdf.set_font('Arial', '', 11)
        pdf.multi_cell(0, 8, 'Union of India vs State of Maharashtra\n\nJudgment dated: 15 June 2024\n\nThis court directs compliance within 30 days.\n\nCompensation: Rs. 50,000')
        test_pdf_path = '/tmp/test_judgment.pdf'
        pdf.output(test_pdf_path)
        print(f"  [INFO] Test PDF created at {test_pdf_path}")
        
        # Test 3.1: Upload PDF
        with open(test_pdf_path, 'rb') as f:
            files = {'file': ('test_judgment.pdf', f, 'application/pdf')}
            try:
                with httpx.Client(timeout=30.0) as client:
                    response = client.post(f"{API_BASE}/documents/upload", 
                                          headers=auth_header, files=files)
                    if response.status_code in [200, 201]:
                        data = response.json()
                        doc_id = data.get('document_id') or data.get('id')
                        if doc_id:
                            print(f"  [PASS] Upload PDF")
                            results["PASS"].append("Upload PDF")
                            print(f"         Document ID: {doc_id}")
                        else:
                            print(f"  [FAIL] Upload PDF (no document_id in response)")
                            results["FAIL"].append("Upload PDF (no document_id)")
                    else:
                        print(f"  [FAIL] Upload PDF (HTTP {response.status_code})")
                        results["FAIL"].append(f"Upload PDF (HTTP {response.status_code})")
            except Exception as e:
                print(f"  [FAIL] Upload PDF ({str(e)[:60]})")
                results["FAIL"].append(f"Upload PDF ({str(e)[:60]})")
    except ImportError:
        print("  [SKIP] fpdf not available for PDF creation")
        results["SKIP"].append("Upload PDF")
        doc_id = None
    except Exception as e:
        print(f"  [FAIL] Could not create test PDF ({str(e)})")
        results["FAIL"].append(f"Upload PDF (creation failed)")
        doc_id = None
    
    # Test 3.2: List Documents
    test("List Documents", "GET", f"{API_BASE}/documents/?page=1&per_page=10",
         headers=auth_header,
         expected_status=200,
         success_check=lambda d: "documents" in d or "items" in d or isinstance(d, list))
    
    # Test 3.3: Filter Documents
    test("Filter Documents", "GET", f"{API_BASE}/documents/?status=EXTRACTION_COMPLETE",
         headers=auth_header,
         expected_status=[200, 404])

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4: DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────

print()
print("[4] DASHBOARD")
print("-" * 80)

if auth_header:
    test("Dashboard Summary", "GET", f"{API_BASE}/dashboard/summary",
         headers=auth_header,
         expected_status=200,
         success_check=lambda d: isinstance(d, dict))
    
    test("Dashboard Actions", "GET", f"{API_BASE}/dashboard/actions?page=1&per_page=5",
         headers=auth_header,
         expected_status=[200, 404])
else:
    results["SKIP"].extend(["Dashboard Summary", "Dashboard Actions"])

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5: API DOCUMENTATION
# ─────────────────────────────────────────────────────────────────────────────

print()
print("[5] API DOCUMENTATION")
print("-" * 80)

test("Swagger UI", "GET", f"{BASE_URL}/docs", expected_status=200)
test("OpenAPI Schema", "GET", f"{BASE_URL}/openapi.json", expected_status=200)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6: OLLAMA LLM
# ─────────────────────────────────────────────────────────────────────────────

print()
print("[6] OLLAMA LLM SERVICE")
print("-" * 80)

try:
    with httpx.Client(timeout=5.0) as client:
        response = client.get(f"{OLLAMA_URL}/api/tags")
        if response.status_code == 200:
            data = response.json()
            models = data.get("models", [])
            print(f"  [PASS] Ollama Service Running")
            results["PASS"].append("Ollama Service Running")
            print(f"         Models available: {len(models)}")
            for model in models:
                print(f"           - {model.get('name')}")
        else:
            print(f"  [FAIL] Ollama Service (HTTP {response.status_code})")
            results["FAIL"].append("Ollama Service")
except httpx.ConnectError:
    print(f"  [FAIL] Ollama Service (Connection refused)")
    results["FAIL"].append("Ollama Service (Connection refused)")
except Exception as e:
    print(f"  [FAIL] Ollama Service ({str(e)})")
    results["FAIL"].append(f"Ollama Service ({str(e)})")

# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY REPORT
# ─────────────────────────────────────────────────────────────────────────────

print()
print("=" * 80)
print(" AUDIT RESULTS")
print("=" * 80)
print()

passed = len(results["PASS"])
failed = len(results["FAIL"])
skipped = len(results["SKIP"])
total = results["TOTAL"]

print(f"Total Tests: {total}")
print(f"  Passed:  {passed} ✓")
print(f"  Failed:  {failed} ✗")
print(f"  Skipped: {skipped} ⊘")
print()

if results["FAIL"]:
    print("FAILED TESTS:")
    for test_name in results["FAIL"]:
        print(f"  ✗ {test_name}")
    print()

if results["SKIP"]:
    print("SKIPPED TESTS:")
    for test_name in results["SKIP"]:
        print(f"  ⊘ {test_name}")
    print()

if failed == 0:
    print("✓ ALL TESTS PASSED")
    print("  The backend is operational!")
else:
    print(f"✗ {failed} TEST(S) FAILED")
    print("  See details above for issues to fix.")

print()
print("=" * 80)

sys.exit(0 if failed == 0 else 1)
