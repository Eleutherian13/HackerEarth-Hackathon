# Authentication Bypass Setup Guide

## Overview

The LAOS backend now supports **authentication bypass mode** for development and testing. When enabled, all API requests bypass JWT token validation and use a system user with full permissions.

This allows you to:
- ✅ Test all LLM features without authentication
- ✅ Upload and process documents without tokens
- ✅ Run integration tests without login
- ✅ Develop features independently of auth system

## Quick Start

### 1. Enable Auth Bypass

```bash
cd backend
python enable_auth_bypass.py --enable
```

This will:
- Create/update `.env` file with `AUTH_BYPASS=true`
- Set up the bypass user in the system
- Allow all requests to use the system user

### 2. Start the Backend

```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Test LLM Features

No authentication required! Just send requests directly:

```bash
# Upload a document
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@sample.pdf"

# List documents
curl http://localhost:8000/api/v1/documents

# Check document status
curl http://localhost:8000/api/v1/documents/{document_id}/status
```

## How It Works

### When AUTH_BYPASS is Enabled

1. **Auth Middleware**: Automatically creates a bypass user context
2. **Dependencies**: `get_current_user()` returns the bypass user
3. **User Object**: 
   - ID: `00000000-0000-0000-0000-000000000001`
   - Email: `bypass@system.local`
   - Role: `SUPERADMIN` (full access)
   - Name: `System Bypass User`

### When AUTH_BYPASS is Disabled (Normal Mode)

1. All requests require valid JWT tokens
2. Tokens obtained via `/api/v1/auth/login`
3. Normal authentication flow applies

## Configuration

### Environment Variable

Add to `.env`:

```env
AUTH_BYPASS=true    # Enable bypass mode
AUTH_BYPASS=false   # Disable bypass mode (default)
```

### Bypass User Details

The system creates a special user when `AUTH_BYPASS=true`:

```python
User(
    id="00000000-0000-0000-0000-000000000001",
    email="bypass@system.local",
    full_name="System Bypass User",
    role=UserRole.SUPERADMIN,  # Full permissions
    is_active=True,
    is_email_verified=True
)
```

## Available Endpoints (No Auth Required)

### Document Management
```
POST   /api/v1/documents/upload          Upload PDF
GET    /api/v1/documents                 List documents
GET    /api/v1/documents/{id}            Get document details
GET    /api/v1/documents/{id}/status     Check processing status
DELETE /api/v1/documents/{id}            Delete document
```

### Content Extraction
```
GET    /api/v1/documents/{id}/extraction     Get extracted content
GET    /api/v1/documents/{id}/extracted-fields   Get specific fields
POST   /api/v1/documents/{id}/extraction/verify Verify extraction
```

### LLM Features
```
POST   /api/v1/documents/{id}/llm-analysis              Start analysis
GET    /api/v1/documents/{id}/llm-analysis/{task_id}    Get result
```

### Review & Feedback
```
GET    /api/v1/documents/{id}/review                 Get review results
POST   /api/v1/documents/{id}/review                 Submit review
```

### Dashboard & Analytics
```
GET    /api/v1/dashboard/stats            System statistics
GET    /api/v1/dashboard/activity         Activity feed
```

### Admin Functions
```
GET    /api/v1/admin/users                List users
POST   /api/v1/admin/users                Create user
GET    /api/v1/admin/system-health        System health
```

## Code Modifications

### 1. Configuration (`app/core/config.py`)

Added auth bypass settings:
```python
AUTH_BYPASS: bool = False
AUTH_BYPASS_USER_ID: str = "00000000-0000-0000-0000-000000000001"
AUTH_BYPASS_USER_EMAIL: str = "bypass@system.local"
```

### 2. Security Module (`app/core/security.py`)

Added bypass user creation:
```python
def get_or_create_bypass_user(db: Session) -> User:
    """Get or create a bypass user for when AUTH_BYPASS is enabled."""
    # Creates/returns the bypass system user
```

Also made `oauth2_scheme` optional:
```python
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login", 
    auto_error=False  # Don't error when token missing in bypass mode
)
```

### 3. Auth Middleware (`app/api/middleware/auth.py`)

Modified dispatch to check for bypass:
```python
if settings.AUTH_BYPASS:
    # Use bypass user, skip token validation
else:
    # Normal auth flow
```

### 4. Dependencies (`app/api/deps.py`)

Updated `get_current_user()`:
```python
async def get_current_user(request, db, token):
    if settings.AUTH_BYPASS:
        return get_or_create_bypass_user(db)  # Skip token validation
    # ... normal auth flow
```

## Usage Examples

### Python Client

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Upload document (no auth needed!)
with open("judgment.pdf", "rb") as f:
    response = requests.post(
        f"{BASE_URL}/documents/upload",
        files={"file": f}
    )
    doc_id = response.json()["document_id"]

# Extract content
response = requests.get(
    f"{BASE_URL}/documents/{doc_id}/extraction"
)
print(response.json())

# LLM Analysis
response = requests.post(
    f"{BASE_URL}/documents/{doc_id}/llm-analysis",
    json={"prompt": "Summarize this judgment"}
)
task_id = response.json()["task_id"]

# Check result
response = requests.get(
    f"{BASE_URL}/documents/{doc_id}/llm-analysis/{task_id}"
)
print(response.json()["result"])
```

### cURL Examples

```bash
# Upload
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@judgment.pdf"

# List
curl http://localhost:8000/api/v1/documents

# Extract
curl http://localhost:8000/api/v1/documents/{doc_id}/extraction

# LLM Analysis
curl -X POST http://localhost:8000/api/v1/documents/{doc_id}/llm-analysis \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Summarize this"}'
```

## Disabling Auth Bypass

When you're ready to use normal authentication:

```bash
python enable_auth_bypass.py --disable
```

Or manually set in `.env`:
```env
AUTH_BYPASS=false
```

Then restart the backend. All endpoints will now require JWT tokens.

## Security Notes

⚠️ **Important**: 
- Auth bypass should **ONLY** be used in development/testing
- Never enable `AUTH_BYPASS=true` in production
- The bypass user has `SUPERADMIN` role with full access
- All requests are still logged and audited
- Use normal authentication for production deployments

## Troubleshooting

### Still getting 401 errors?

1. Check `.env` file:
   ```bash
   grep AUTH_BYPASS backend/.env
   ```

2. Restart the backend (changes to .env require restart)

3. Check that the database is accessible and bypass user can be created

### Can't upload files?

1. Verify the upload endpoint: `POST /api/v1/documents/upload`
2. Check `LOCAL_STORAGE_PATH` exists: `backend/storage/documents/`
3. Check file permissions

### LLM features not working?

1. Verify Ollama is running: `http://localhost:11434`
2. Check Ollama model: `curl http://localhost:11434/api/tags`
3. Verify OLLAMA_BASE_URL in `.env`

## Scripts Reference

### enable_auth_bypass.py

Manage auth bypass state:

```bash
# Enable bypass mode
python enable_auth_bypass.py --enable

# Disable bypass mode  
python enable_auth_bypass.py --disable

# Check current status
python enable_auth_bypass.py --status
```

### bypass_example_usage.py

Example usage demonstrating all features:

```bash
python bypass_example_usage.py
```

This will:
- Check server health
- List documents
- Show API endpoints available
- Demonstrate workflow

## API Documentation

Once backend is running with auth bypass:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

All endpoints are documented and can be tested directly from the docs interface.

## Summary

| Mode | Requires Token | Bypass User | Use Case |
|------|---|---|---|
| **AUTH_BYPASS=true** | ❌ No | ✅ Yes | Development, Testing |
| **AUTH_BYPASS=false** | ✅ Yes | ❌ No | Production, Normal Use |

Need help? Check the other documentation files:
- `IMPLEMENTATION_GUIDE.md` - Detailed implementation
- `QUICK_START_AFTER_AUDIT.md` - Full deployment guide
- `API.md` - API reference
