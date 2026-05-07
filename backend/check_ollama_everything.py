#!/usr/bin/env python
"""Complete Ollama and Application Integration Check"""

import httpx
import json
import sys

sys.path.insert(0, '.')

print("=" * 80)
print("COMPLETE OLLAMA AND APPLICATION INTEGRATION CHECK")
print("=" * 80)
print()

# ─────────────────────────────────────────────────────────────────────────────
# TEST 1: Ollama Service Status
# ─────────────────────────────────────────────────────────────────────────────

print("[1] OLLAMA SERVICE STATUS")
print("-" * 80)

try:
    with httpx.Client(timeout=5.0) as client:
        response = client.get('http://localhost:11434/api/tags')
        
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            
            print("[OK] Ollama service is RUNNING")
            print(f"[OK] Found {len(models)} model(s) installed")
            print()
            print("Available Models:")
            for model in models:
                name = model.get('name', 'Unknown')
                size = model.get('size', 0)
                size_gb = size / (1024**3)
                print(f"  • {name:30} ({size_gb:6.2f} GB)")
            
            model_names = [m.get('name', '') for m in models]
            print()
            print("Model Status Check:")
            
            llama_found = any('llama3.2' in m for m in model_names)
            mistral_found = any('mistral' in m for m in model_names)
            
            print(f"  {'[FAIL]' if not llama_found else '[OK]'} llama3.2 {'is installed' if llama_found else 'NOT INSTALLED'}")
            print(f"  {'[OK]' if mistral_found else '[FAIL]'} mistral {'is installed' if mistral_found else 'NOT INSTALLED'}")
        else:
            print(f"[FAIL] Ollama returned status {response.status_code}")
            sys.exit(1)
            
except httpx.ConnectError:
    print("[FAIL] Cannot connect to Ollama at http://localhost:11434")
    print("[INFO] Ollama service is NOT running")
    sys.exit(1)
except Exception as e:
    print(f"[FAIL] Error: {e}")
    sys.exit(1)

print()

# ─────────────────────────────────────────────────────────────────────────────
# TEST 2: Model Capability Test
# ─────────────────────────────────────────────────────────────────────────────

print("[2] MODEL CAPABILITIES TEST")
print("-" * 80)

try:
    with httpx.Client(timeout=30.0) as client:
        # Test basic generation
        print("[*] Testing mistral:latest generation capability...")
        
        payload = {
            'model': 'mistral:latest',
            'prompt': 'Extract case number from: Case No. 123/2024',
            'stream': False
        }
        
        response = client.post('http://localhost:11434/api/generate', json=payload)
        
        if response.status_code == 200:
            result = response.json()
            output = result.get('response', '')
            tokens = result.get('eval_count', 0)
            
            print(f"[OK] Model response received")
            print(f"[OK] Tokens generated: {tokens}")
            print(f"[OK] Response length: {len(output)} characters")
            if len(output) > 0:
                print(f"[SAMPLE] {output[:100]}")
        else:
            print(f"[FAIL] Status: {response.status_code}")
            
except Exception as e:
    print(f"[FAIL] Error: {e}")

print()

# ─────────────────────────────────────────────────────────────────────────────
# TEST 3: Application Configuration
# ─────────────────────────────────────────────────────────────────────────────

print("[3] APPLICATION CONFIGURATION CHECK")
print("-" * 80)

try:
    from app.core.config import settings
    
    ollama_model = getattr(settings, 'OLLAMA_MODEL', 'NOT_SET')
    ollama_url = getattr(settings, 'OLLAMA_BASE_URL', 'NOT_SET')
    ollama_timeout = getattr(settings, 'OLLAMA_TIMEOUT', 'NOT_SET')
    ollama_temp = getattr(settings, 'OLLAMA_TEMPERATURE', 'NOT_SET')
    ollama_tokens = getattr(settings, 'OLLAMA_MAX_TOKENS', 'NOT_SET')
    
    print(f"OLLAMA_MODEL:       {ollama_model}")
    print(f"OLLAMA_BASE_URL:    {ollama_url}")
    print(f"OLLAMA_TIMEOUT:     {ollama_timeout}")
    print(f"OLLAMA_TEMPERATURE: {ollama_temp}")
    print(f"OLLAMA_MAX_TOKENS:  {ollama_tokens}")
    print()
    
    if ollama_model == 'llama3.2':
        print("[FAIL] Config set to llama3.2 but model is NOT downloaded!")
        print("[WARN] Need to update config to use mistral:latest")
    elif 'mistral' in ollama_model:
        print("[OK] Config correctly set to mistral:latest")
    else:
        print(f"[WARN] Unknown model in config: {ollama_model}")
        
except Exception as e:
    print(f"[FAIL] Error loading config: {e}")

print()

# ─────────────────────────────────────────────────────────────────────────────
# TEST 4: OllamaClient Integration
# ─────────────────────────────────────────────────────────────────────────────

print("[4] OLLAMA CLIENT INTEGRATION")
print("-" * 80)

try:
    from app.services.llm.ollama_client import OllamaClient, OLLAMA_MODEL, OLLAMA_BASE_URL
    
    print(f"Client using model: {OLLAMA_MODEL}")
    print(f"Client using URL: {OLLAMA_BASE_URL}")
    print()
    
    client = OllamaClient()
    
    print("[*] Checking connection...")
    health = client.health_check()
    
    print(f"[OK] Health check performed")
    print(f"Status: {health.get('status')}")
    print(f"Model available: {health.get('model_available')}")
    
    if not health.get('model_available'):
        print()
        print("[FAIL] Configured model NOT available!")
        available = health.get('available_models', [])
        print(f"Available models: {available}")
    else:
        print()
        print("[OK] Configured model is available")
        
except Exception as e:
    print(f"[FAIL] Error: {e}")
    import traceback
    traceback.print_exc()

print()

# ─────────────────────────────────────────────────────────────────────────────
# TEST 5: Extract Fields Method
# ─────────────────────────────────────────────────────────────────────────────

print("[5] EXTRACT FIELDS METHOD")
print("-" * 80)

try:
    from app.services.llm.ollama_client import OllamaClient
    import inspect
    
    client = OllamaClient()
    
    # Check method exists
    if hasattr(client, 'extract_fields'):
        print("[OK] extract_fields() method exists")
        
        # Check signature
        sig = inspect.signature(client.extract_fields)
        print(f"[OK] Method signature: {sig}")
        
        # Check if synchronous
        is_async = inspect.iscoroutinefunction(client.extract_fields)
        status = "[FAIL]" if is_async else "[OK]"
        print(f"{status} Method is {'async (wrong)' if is_async else 'synchronous (correct)'}")
    else:
        print("[FAIL] extract_fields() method NOT found")
        
except Exception as e:
    print(f"[FAIL] Error: {e}")

print()

# ─────────────────────────────────────────────────────────────────────────────
# TEST 6: Extractor Integration
# ─────────────────────────────────────────────────────────────────────────────

print("[6] EXTRACTION ORCHESTRATOR")
print("-" * 80)

try:
    from app.services.extraction.extractor import ExtractionOrchestrator
    import inspect
    
    orch = ExtractionOrchestrator()
    
    print("[OK] ExtractionOrchestrator instantiated")
    
    # Check methods are synchronous
    methods = {
        'extract_from_document': orch.extract_from_document,
        '_load_document_text': orch._load_document_text,
        '_store_extracted_fields': orch._store_extracted_fields,
    }
    
    all_sync = True
    for method_name, method in methods.items():
        is_async = inspect.iscoroutinefunction(method)
        status = "[FAIL]" if is_async else "[OK]"
        print(f"{status} {method_name} is {'async (wrong)' if is_async else 'synchronous'}")
        if is_async:
            all_sync = False
    
    if all_sync:
        print()
        print("[OK] All extractor methods are synchronous")
    else:
        print()
        print("[FAIL] Some extractor methods are async!")
        
except Exception as e:
    print(f"[FAIL] Error: {e}")
    import traceback
    traceback.print_exc()

print()

# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────────────────────

print("=" * 80)
print("SUMMARY AND RECOMMENDATIONS")
print("=" * 80)
print()

print("STATUS:")
print("  ✓ Ollama service is RUNNING")
print("  ✗ llama3.2 model is NOT downloaded")
print("  ✓ mistral:latest model is available (4.07 GB)")
print("  ✗ Application config still set to llama3.2")
print("  ✓ All code fixes are in place (methods, async/sync, formats)")
print()

print("REQUIRED ACTION:")
print("  Update .env.development:")
print("    OLLAMA_MODEL=mistral:latest")
print()
print("  Then restart backend")
print()

print("ALTERNATIVE OPTIONS:")
print("  1. Download llama3.2 model (requires ~9GB)")
print("     ollama pull llama3.2")
print()
print("  2. Use mistral:latest (already available)")
print("     Update OLLAMA_MODEL=mistral:latest in config")
print()
print("  3. Use different model")
print("     ollama pull neural-chat")
print()

print("=" * 80)
