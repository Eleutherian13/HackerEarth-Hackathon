# ⚡ Quick Reference: Auth Bypass for LLM Features

## TL;DR - Get Started in 2 Minutes

```bash
# 1. Enable auth bypass
cd backend
python enable_auth_bypass.py --enable

# 2. Start backend (existing method)
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 3. Test (no auth token needed!)
curl http://localhost:8000/api/v1/documents

# 4. Upload document
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@judgment.pdf"
```

## What Was Changed?

### 4 Backend Files Modified
1. ✅ `app/core/config.py` - Added AUTH_BYPASS flag
2. ✅ `app/core/security.py` - Added bypass user creation
3. ✅ `app/api/middleware/auth.py` - Check for bypass in auth flow
4. ✅ `app/api/deps.py` - Return bypass user in dependencies

### 3 New Helper Files Created
1. ✅ `enable_auth_bypass.py` - Enable/disable bypass mode
2. ✅ `bypass_example_usage.py` - Example usage script
3. ✅ Documentation files for setup & reference

## The Bypass User

When `AUTH_BYPASS=true`, system creates:
- **ID**: `00000000-0000-0000-0000-000000000001`
- **Email**: `bypass@system.local`
- **Role**: `SUPERADMIN` (full permissions!)
- **Name**: System Bypass User

This user handles all requests - no token validation needed.

## Features Now Accessible

| Feature | Before | After |
|---------|--------|-------|
| Document Upload | 🔐 Need token | ✅ Free access |
| LLM Analysis | 🔐 Need token | ✅ Free access |
| Extraction | 🔐 Need token | ✅ Free access |
| Review System | 🔐 Need token | ✅ Free access |
| Admin Functions | 🔐 Need token | ✅ Free access |
| Swagger Docs | ✅ Works | ✅ Works |

## Usage Examples

### Upload Document
```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@judgment.pdf"
```

### List Documents
```bash
curl http://localhost:8000/api/v1/documents
```

### LLM Analysis
```bash
curl -X POST http://localhost:8000/api/v1/documents/{id}/llm-analysis \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Summarize this judgment"}'
```

### Python
```python
import requests

# No token needed!
response = requests.post(
    "http://localhost:8000/api/v1/documents/upload",
    files={"file": open("judgment.pdf", "rb")}
)
doc_id = response.json()["document_id"]

# Extract content
response = requests.get(
    f"http://localhost:8000/api/v1/documents/{doc_id}/extraction"
)
print(response.json())
```

## Enable/Disable

### Enable Bypass
```bash
python enable_auth_bypass.py --enable
```
Sets `AUTH_BYPASS=true` in `.env`

### Disable Bypass
```bash
python enable_auth_bypass.py --disable
```
Sets `AUTH_BYPASS=false` in `.env`

### Check Status
```bash
python enable_auth_bypass.py --status
```

## Configuration

Add to `.env`:
```env
# Enable auth bypass
AUTH_BYPASS=true

# Disable auth bypass (default)
AUTH_BYPASS=false
```

**Important**: Restart backend after changing `.env`

## Key Points

✅ **All LLM features work without authentication**
✅ **Document upload/processing works without tokens**
✅ **Easy to enable/disable via helper script**
✅ **Fully backward compatible (normal mode still works)**
✅ **Only for development/testing (never production)**

⚠️ **Security Warning**: Never enable in production!

## Testing

### Run Example Script
```bash
python bypass_example_usage.py
```

Shows:
- Health check
- Document listing
- Upload demonstration
- LLM analysis
- Available endpoints

### Access API Docs
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

All endpoints documented and testable directly.

## How It Works

```
Request → Auth Middleware
           ↓
        Check AUTH_BYPASS
           ↓
    ┌─────┴─────┐
    │           │
  true       false
    │           │
    ↓           ↓
  Use Skip    Token
 Bypass  Validation
  User       ↓
    │      Get User
    └─────┬──────┘
         │
      Continue to Endpoint
           ↓
     Handle Request
```

## Troubleshooting

**Still getting 401?**
- Check: `grep AUTH_BYPASS backend/.env`
- Restart backend after changing `.env`
- Verify database is running

**Can't upload?**
- Check: `backend/storage/documents/` directory exists
- Verify file permissions
- Check logs for errors

**LLM not working?**
- Verify Ollama running: `curl http://localhost:11434`
- Check OLLAMA_BASE_URL in `.env`
- Verify model available

## Files Reference

### Documentation
- `AUTH_BYPASS_SETUP.md` - Complete setup guide
- `AUTH_BYPASS_IMPLEMENTATION.md` - Technical details
- `QUICK_REFERENCE.md` - This file

### Scripts
- `enable_auth_bypass.py` - Manage bypass mode
- `bypass_example_usage.py` - Example client

### Modified Code
- `app/core/config.py` - Configuration
- `app/core/security.py` - User creation
- `app/api/middleware/auth.py` - Middleware
- `app/api/deps.py` - Dependencies

## Summary

| Action | Command |
|--------|---------|
| Enable bypass | `python enable_auth_bypass.py --enable` |
| Disable bypass | `python enable_auth_bypass.py --disable` |
| Check status | `python enable_auth_bypass.py --status` |
| Start backend | `python -m uvicorn main:app --reload` |
| Test API | `python bypass_example_usage.py` |
| Docs | http://localhost:8000/docs |

That's it! You can now use all LAOS LLM features without authentication. 🚀
