#!/usr/bin/env python
"""Verify that the deployed backend is working correctly."""

import sys
sys.path.insert(0, '.')

print("=" * 60)
print("LAOS BACKEND DEPLOYMENT VERIFICATION")
print("=" * 60)
print()

# Test 1: Import deployed modules
print("[*] Testing module imports...")
try:
    from app.api.v1.endpoints import auth, documents
    print("  [OK] Auth module loaded")
    print("  [OK] Documents module loaded")
except Exception as e:
    print(f"  [FAIL] Import failed: {e}")
    sys.exit(1)

# Test 2: Load FastAPI app
print()
print("[*] Testing FastAPI app initialization...")
try:
    from main import app
    print("  [OK] FastAPI app created successfully")
except Exception as e:
    print(f"  [FAIL] App creation failed: {e}")
    sys.exit(1)

# Test 3: Verify endpoints are registered
print()
print("[*] Checking registered endpoints...")

auth_routes = [r for r in app.routes if '/auth' in str(r.path)]
doc_routes = [r for r in app.routes if '/documents' in str(r.path)]

print()
print("  Auth Endpoints Registered:")
for r in sorted(auth_routes, key=lambda x: str(x.path)):
    methods = str(r.methods - {"OPTIONS"}).replace("{", "").replace("}", "").replace("'", "")
    print(f"     {methods:20} {r.path}")

print()
print("  Document Endpoints Registered:")
for r in sorted(doc_routes, key=lambda x: str(r.path)):
    methods = str(r.methods - {"OPTIONS"}).replace("{", "").replace("}", "").replace("'", "")
    print(f"     {methods:20} {r.path}")

# Test 4: Check auth functions
print()
print("[*] Verifying auth functions...")
try:
    from app.api.v1.endpoints.auth import (
        create_access_token,
        verify_password,
        get_password_hash,
    )
    print("  [OK] create_access_token() available")
    print("  [OK] verify_password() available")
    print("  [OK] get_password_hash() available")
except Exception as e:
    print(f"  [WARN] Some auth functions missing: {e}")

# Test 5: Check document functions
print()
print("[*] Verifying document functions...")
try:
    from app.api.v1.endpoints.documents import upload_document
    print("  [OK] upload_document() available")
except Exception as e:
    print(f"  [WARN] Document functions missing: {e}")

# Test 6: Check other services
print()
print("[*] Checking supporting services...")
try:
    from app.services.llm.ollama_client import get_ollama_client
    print("  [OK] Ollama client available")
except Exception as e:
    print(f"  [WARN] Ollama client: {e}")

try:
    from app.services.ingestion.pdf_processor import process_pdf_sync
    print("  [OK] PDF processor available")
except Exception as e:
    print(f"  [WARN] PDF processor: {e}")

try:
    from app.services.ingestion.text_cleaner import TextCleaner
    print("  [OK] Text cleaner available")
except Exception as e:
    print(f"  [WARN] Text cleaner: {e}")

print()
print("=" * 60)
print("DEPLOYMENT VERIFICATION COMPLETE")
print("=" * 60)
print()
print("Next steps:")
print("  1. Start Docker services: docker compose up -d")
print("  2. Run backend: python -m uvicorn main:app --port 8000")
print("  3. Test endpoints: bash verify_all_endpoints.sh")
print()
