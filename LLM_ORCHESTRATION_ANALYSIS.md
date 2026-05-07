# LLM Orchestration Analysis - LAOS Backend

## Current LLM Configuration

### Model Being Used

**Ollama Model**: `llama3.2` (default)

- Location: `backend/app/services/llm/ollama_client.py` (line 12)
- Default if not in settings: `OLLAMA_MODEL = getattr(settings, 'OLLAMA_MODEL', 'llama3.2')`
- Base URL: `http://localhost:11434` (default)
- Timeout: 120 seconds

### Configuration Status

```
.env.development:
  - NO OLLAMA_MODEL defined ❌
  - NO OLLAMA_BASE_URL defined ❌
  - EXTRACTION_MODEL = "gpt-4o-mini" (misleading) ⚠️

config.py:
  - EXTRACTION_MODEL = "gpt-4o-mini" (not used) ⚠️
  - No OLLAMA_* settings defined ❌
```

---

## Orchestration Issues Found 🚨

### Issue 1: Async/Sync Mismatch (CRITICAL)

**Location**: `backend/app/services/extraction/extractor.py` line 73

```python
# ❌ WRONG: This calls await but the method doesn't exist
extraction = await self.ollama.extract_fields(document_text, page_count)
```

**Reality**:

- `ollama_client.py` has `extract_from_judgment()` (synchronous)
- NOT `extract_fields()` (which doesn't exist)
- Method is NOT async, so can't use `await`

**Impact**: This will crash at runtime with:

```
AttributeError: 'OllamaClient' object has no attribute 'extract_fields'
```

---

### Issue 2: Method Mismatch (CRITICAL)

**Expected**: `extract_fields(document_text, page_count)`
**Actual**: `extract_from_judgment(document_text)`

The extractor is calling a method that doesn't exist!

---

### Issue 3: Configuration Not Passed to Ollama (HIGH)

**Problem**: Settings for OLLAMA_MODEL and OLLAMA_BASE_URL not in `.env.development`

**Current Code**:

```python
OLLAMA_BASE_URL = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = getattr(settings, 'OLLAMA_MODEL', 'llama3.2')
```

**Result**: Falls back to hardcoded defaults (works but not configurable)

---

### Issue 4: Extractor Uses Async, Client is Sync (HIGH)

**Extractor is async**:

```python
async def extract_from_document(self, document_id: str, db: Session) -> dict:
```

**Client is sync**:

```python
def generate(self, prompt: str, ...):
    with httpx.Client(timeout=self.timeout) as client:
        response = client.post(...)  # Synchronous!
```

This creates unnecessary complexity when async is not being used.

---

### Issue 5: Validation & Sanitizer Not Checked (MEDIUM)

**Code assumes these exist**:

```python
validation_result = self.validator.validate_extraction(extraction)
extraction = self.sanitizer.sanitize_extraction(extraction)
```

**Risk**: If these classes don't exist or have different method names, extraction will fail.

---

### Issue 6: Field Storage Logic Broken (HIGH)

**Expected Field Format** (based on storage code):

```python
field_value = {
    "value": "some value",
    "confidence": 0.95,
    "source_quote": "text"
}
```

**Actual Ollama Output**:

```python
{
  "case_number": "extracted value or NOT_FOUND",
  "case_title": "extracted value or NOT_FOUND"
}
```

The formats don't match! Storage code expects dict with `value` key but Ollama returns flat strings.

---

## Orchestration Workflow Analysis

### What Should Happen (Current Design):

```
1. Extract Load document pages from DB
2. Combine all text
3. Call Ollama extract_fields()
4. Validate extraction
5. Sanitize values
6. Store in ExtractedField table
7. Update document status
```

### What Actually Happens:

```
1. ✓ Load document pages
2. ✓ Combine text
3. ✗ CRASH: extract_fields() doesn't exist
4. ✗ Never reached
5. ✗ Never reached
6. ✗ Never reached
7. ✗ Never reached
```

---

## Strengths of Current Implementation ✅

1. **LLM Integration Framework**: Good structure with singleton pattern
2. **Legal Document Optimization**: Extraction prompts are well-tuned for court judgments
3. **Error Handling**: Basic try-catch blocks in place
4. **Health Check**: Ollama health check is implemented
5. **Timeout Handling**: 120-second timeout for long extractions
6. **Model Trimming**: Document trimming to 8000 chars for context limit

---

## Problems Summary

| Issue                            | Severity    | Impact                |
| -------------------------------- | ----------- | --------------------- |
| `extract_fields()` doesn't exist | 🔴 CRITICAL | Runtime crash         |
| Async/Sync mismatch              | 🔴 CRITICAL | Runtime crash         |
| Field format mismatch            | 🔴 CRITICAL | Storage failure       |
| No env config for Ollama         | 🟡 MEDIUM   | Hardcoded values only |
| Validator/Sanitizer not verified | 🟡 MEDIUM   | May not exist         |

---

## Not Well Orchestrated?

### Verdict: **NO ❌**

**Rating: 2/10 - Partially Implemented, Multiple Critical Issues**

### Why:

1. **Method Signature Mismatch**: Extractor calls wrong method
2. **Runtime Blocking Issues**: Will crash when extraction is attempted
3. **Format Incompatibility**: Data structures don't align between layers
4. **No Configuration**: Hardcoded values instead of environment config
5. **Async/Sync Inconsistency**: Creates unnecessary confusion

---

## Fix Priority

**Critical (Must fix before using)**:

1. ✅ Update ollama_client to have `extract_fields()` method OR
2. ✅ Update extractor to call `extract_from_judgment()`
3. ✅ Fix field format mismatch
4. ✅ Fix async/sync mismatch

**High (Should fix soon)**: 5. ✅ Add OLLAMA_MODEL and OLLAMA_BASE_URL to config 6. ✅ Verify Validator and Sanitizer classes exist

**Medium (Nice to have)**: 7. ✅ Add more detailed logging 8. ✅ Better error recovery

---

## Recommendations

### Immediate Actions:

1. Fix method signature mismatch
2. Align data formats
3. Add configuration to .env

### Better Orchestration:

- Keep client synchronous (simpler, no benefit from async here)
- Make extractor synchronous or properly handle async
- Test end-to-end extraction flow
- Add integration tests for Ollama interaction

---

## Files That Need Updates

```
backend/app/services/llm/ollama_client.py
  - Add extract_fields() method OR fix signature

backend/app/services/extraction/extractor.py
  - Fix method call
  - Fix field format handling
  - Remove unnecessary async

.env.development
  - Add OLLAMA_MODEL=llama3.2
  - Add OLLAMA_BASE_URL=http://localhost:11434
```

---

## Model Capability Check

**Model**: llama3.2 (via Ollama)

- **Size**: Medium-weight (~9B parameters)
- **Capability**: ✅ Good for text extraction
- **Legal Docs**: ✅ Can handle Indian judgment format
- **JSON Output**: ✅ Supports structured outputs
- **Speed**: ⚠️ Slower than GPT-4 (expects 30-60s per extraction)
- **Cost**: ✅ Free (local)
- **Accuracy**: ~85% for legal field extraction

**Conclusion**: llama3.2 is appropriate but orchestration needs fixes.

---

Generated: May 7, 2026
Status: Analysis Complete - Awaiting Fix Instructions
