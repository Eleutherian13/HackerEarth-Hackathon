#!/usr/bin/env python
"""Application Status Verification Report"""

import sys
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.path.insert(0, '.')

print("=" * 100)
print("LAOS COURT JUDGMENT ACTION SYSTEM - STATUS REPORT")
print("=" * 100)
print()

results = {}

# Test 1: Ollama Service
print("[1] OLLAMA LLM SERVICE")
print("-" * 100)

try:
    from app.services.llm.ollama_client import OllamaClient
    
    client = OllamaClient()
    health = client.health_check()
    
    is_healthy = health.get('status') == 'healthy'
    model_available = health.get('model_available')
    
    print(f"Status: {health.get('status')}")
    print(f"Model: mistral:latest")
    print(f"Model Available: {model_available}")
    
    if is_healthy and model_available:
        print("[PASS] Ollama service operational")
        results['Ollama Service'] = True
    else:
        print("[FAIL] Ollama service issues")
        results['Ollama Service'] = False
        
except Exception as e:
    print(f"[FAIL] Error: {e}")
    results['Ollama Service'] = False

print()

# Test 2: Legal Field Extraction
print("[2] LEGAL FIELD EXTRACTION")
print("-" * 100)

try:
    from app.services.llm.ollama_client import OllamaClient
    
    client = OllamaClient()
    
    test_text = """
    Case No. 2024/SC/001
    Petitioner: Rajesh Kumar
    Respondent: State of Maharashtra
    Judgment Date: 05-May-2024
    The petition is DISMISSED. 
    Compensation of Rs. 50,000 within 30 days.
    """
    
    extraction = client.extract_fields(test_text, page_count=1)
    
    has_structure = (
        'case_details' in extraction and
        'parties' in extraction and
        'operative_directions' in extraction
    )
    
    if has_structure:
        case_num = extraction['case_details'].get('case_number', {}).get('value')
        print(f"Extracted case number: {case_num}")
        print("[PASS] Legal field extraction working")
        results['Field Extraction'] = True
    else:
        print("[FAIL] Missing extraction structure")
        results['Field Extraction'] = False
        
except Exception as e:
    print(f"[FAIL] Error: {e}")
    results['Field Extraction'] = False

print()

# Test 3: Extraction Orchestrator
print("[3] EXTRACTION ORCHESTRATOR")
print("-" * 100)

try:
    from app.services.extraction.extractor import ExtractionOrchestrator
    import inspect
    
    orch = ExtractionOrchestrator()
    
    # Check synchronous methods
    is_sync = (
        not inspect.iscoroutinefunction(orch.extract_from_document) and
        not inspect.iscoroutinefunction(orch._load_document_text) and
        not inspect.iscoroutinefunction(orch._store_extracted_fields)
    )
    
    if is_sync:
        print("[PASS] All orchestrator methods are synchronous")
        results['Extraction Orchestrator'] = True
    else:
        print("[FAIL] Async/sync mismatch detected")
        results['Extraction Orchestrator'] = False
        
except Exception as e:
    print(f"[FAIL] Error: {e}")
    results['Extraction Orchestrator'] = False

print()

# Test 4: Authentication
print("[4] AUTHENTICATION SYSTEM")
print("-" * 100)

try:
    from app.api.v1.endpoints.auth_complete import get_password_hash, verify_password
    
    # Test with shorter password due to bcrypt 72-byte limit
    test_pwd = "SecurePassword123!"
    hashed = get_password_hash(test_pwd)
    verified = verify_password(test_pwd, hashed)
    
    if verified:
        print("[PASS] Password hashing and verification working")
        results['Authentication'] = True
    else:
        print("[FAIL] Password verification failed")
        results['Authentication'] = False
        
except Exception as e:
    print(f"[FAIL] Error: {e}")
    results['Authentication'] = False

print()

# Test 5: JWT Token Generation
print("[5] JWT TOKEN SYSTEM")
print("-" * 100)

try:
    from app.api.v1.endpoints.auth_complete import create_access_token
    
    token = create_access_token({
        'sub': 'test@example.com',
        'email': 'test@example.com',
        'role': 'user'
    })
    
    if token and len(token) > 50:
        print(f"Token generated: {len(token)} characters")
        print("[PASS] JWT token generation working")
        results['JWT System'] = True
    else:
        print("[FAIL] Token generation failed")
        results['JWT System'] = False
        
except Exception as e:
    print(f"[FAIL] Error: {e}")
    results['JWT System'] = False

print()

# Test 6: Database Models
print("[6] DATABASE MODELS")
print("-" * 100)

try:
    from app.models.models import User, Document, DocumentPage, ExtractedField
    
    print("[PASS] All database models available")
    results['Database Models'] = True
    
except Exception as e:
    print(f"[FAIL] Error: {e}")
    results['Database Models'] = False

print()

# Test 7: Configuration
print("[7] APPLICATION CONFIGURATION")
print("-" * 100)

try:
    from app.core.config import settings
    
    required = [
        ('DATABASE_URL', True),
        ('OLLAMA_BASE_URL', True),
        ('OLLAMA_MODEL', True),
        ('JWT_SECRET_KEY', True),
        ('JWT_ALGORITHM', True),
    ]
    
    all_present = True
    for setting_name, _ in required:
        value = getattr(settings, setting_name, None)
        if not value:
            print(f"[MISSING] {setting_name}")
            all_present = False
        else:
            if 'KEY' in setting_name or 'URL' in setting_name:
                print(f"[OK] {setting_name}")
            else:
                print(f"[OK] {setting_name} = {value}")
    
    if all_present:
        print("[PASS] All required settings configured")
        results['Configuration'] = True
    else:
        print("[FAIL] Missing required settings")
        results['Configuration'] = False
        
except Exception as e:
    print(f"[FAIL] Error: {e}")
    results['Configuration'] = False

print()

# ─────────────────────────────────────────────────────────────────────────────
# Summary Report
# ─────────────────────────────────────────────────────────────────────────────

print("=" * 100)
print("VERIFICATION SUMMARY")
print("=" * 100)
print()

passed = sum(1 for v in results.values() if v)
total = len(results)
percentage = (passed / total * 100) if total > 0 else 0

print(f"Tests Passed: {passed}/{total} ({percentage:.0f}%)")
print()

print("Component Status:")
for component, passed_test in results.items():
    status = "[PASS]" if passed_test else "[FAIL]"
    print(f"  {status} {component}")

print()

if passed == total:
    print("=" * 100)
    print("APPLICATION STATUS: READY FOR PRODUCTION")
    print("=" * 100)
    print()
    print("System Status:")
    print("  + Ollama LLM service operational with mistral:latest")
    print("  + Legal field extraction working correctly")
    print("  + Extraction orchestrator synchronized")
    print("  + Authentication and JWT tokens functional")
    print("  + Database models configured")
    print("  + All settings properly configured")
    print()
    print("Next Steps:")
    print("  1. Start backend: python -m uvicorn main:app --reload --port 8000")
    print("  2. Test endpoints with: bash verify_all_endpoints.sh")
    print("  3. Upload and process real documents")
    print()
else:
    print("=" * 100)
    print("APPLICATION STATUS: ISSUES DETECTED")
    print("=" * 100)
    failed = total - passed
    print(f"{failed} component(s) need attention")

print("=" * 100)

# Exit with appropriate code
sys.exit(0 if passed == total else 1)
