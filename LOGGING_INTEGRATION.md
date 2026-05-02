# Logging System Integration Checklist

## Files Created/Modified

### Core Logging
- ✅ `/backend/app/core/logging.py` - Structured JSON logger with redaction
- ✅ `/backend/app/core/audit.py` - Audit trail functions
- ✅ `/backend/app/core/config.py` - Added LOG_FILE_PATH setting

### Middleware & Endpoints
- ✅ `/backend/app/api/middleware/logging.py` - Request/response logging
- ✅ `/backend/app/api/v1/endpoints/health.py` - Health check endpoints
- ✅ `/backend/main.py` - FastAPI app initialization with middleware

### Configuration
- ✅ `/backend/.env.example` - Example configuration with logging options
- ✅ `/docs/LOGGING_SYSTEM.md` - Comprehensive logging documentation

## Integration Steps

### 1. Update Requirements
Ensure `requirements.txt` includes all dependencies:
```
fastapi>=0.100.0
uvicorn[standard]>=0.23.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-multipart>=0.0.6
sqlalchemy>=2.0.0
redis[asyncio]>=5.0.0
```

### 2. Configure Environment
Copy `.env.example` to `.env` and configure:
```bash
cp backend/.env.example backend/.env
```

### 3. Start Application
The logging system initializes automatically when the app starts:
```bash
cd backend
python main.py
# Or with uvicorn:
uvicorn main:app --reload --log-config=None
```

## Feature Checklist

### ✅ Structured JSON Logger
- [x] JSON formatted output with timestamp, level, logger, message
- [x] request_id, user_id, correlation_id fields
- [x] Automatic redaction of sensitive fields
- [x] Support for extra context fields
- [x] File or stdout output
- [x] Environment-aware configuration

### ✅ Request/Response Logging Middleware
- [x] Log HTTP method, path, status_code, duration
- [x] Extract or generate request_id
- [x] Propagate correlation_id
- [x] Skip health check endpoints
- [x] Inject request_id in response headers
- [x] Track request context

### ✅ Audit-Specific Logger
- [x] Immutable append-only database table
- [x] Capture: who (user_id), what (action), when (timestamp)
- [x] Old/new values in changes JSONB
- [x] IP address and user agent tracking
- [x] Event type classification
- [x] Query functions for audit trail

### ✅ Health Check Endpoints
- [x] /health - General health with component breakdown
- [x] /health/ready - Readiness probe (Kubernetes)
- [x] /health/live - Liveness probe (Kubernetes)
- [x] Database connectivity check
- [x] Redis connectivity check
- [x] Storage backend check
- [x] Response timing measurements

### ✅ Configuration
- [x] Environment-specific settings
- [x] Development/staging/production profiles
- [x] Optional Sentry integration
- [x] File and stdout output options
- [x] JSON and text format options
- [x] LOG_FILE_PATH configuration

## Usage Examples

### Simple Logging
```python
from app.core.logging import get_logger

logger = get_logger(__name__)
logger.info("Application started")
```

### Logging with Context
```python
logger.info_context(
    "Document verification completed",
    document_id=doc.id,
    verified_fields=100,
    verification_status="VERIFIED"
)
```

### Audit Logging
```python
from app.core.audit import log_field_verified

await log_field_verified(
    db=db,
    field_id=field.id,
    document_id=field.document_id,
    user_id=current_user.id,
    changes={"status": {"old": "UNVERIFIED", "new": "APPROVED"}},
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent")
)
```

### Health Checks
```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/ready
curl http://localhost:8000/health/live
```

## Testing Logging

```python
# Test structured logging
from app.core.logging import get_logger, set_request_context

logger = get_logger(__name__)
set_request_context(
    request_id="test-123",
    user_id="user-456"
)
logger.info_context("Test message", test_field="test_value")

# Test audit logging
from app.core.audit import log_document_upload

await log_document_upload(
    db=db,
    document_id=document.id,
    user_id=user.id,
    ip_address="127.0.0.1"
)

# Test health endpoints
import requests
response = requests.get("http://localhost:8000/health")
print(response.json())
```

## Monitoring & Alerts

### Log Aggregation
For production, aggregate logs using:
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Splunk
- DataDog
- CloudWatch (AWS)
- Stackdriver (GCP)

### Useful Queries

**Find all errors:**
```sql
SELECT * FROM audit_logs WHERE event_type = 'SYSTEM_ERROR' ORDER BY created_at DESC;
```

**User action audit trail:**
```sql
SELECT * FROM audit_logs WHERE user_id = 'user-uuid' ORDER BY created_at DESC;
```

**Document verification history:**
```sql
SELECT * FROM audit_logs WHERE document_id = 'doc-uuid' AND action = 'VERIFY' ORDER BY created_at DESC;
```

## Performance Considerations

- Request logging adds ~1-5ms per request
- Audit logging is asynchronous and non-blocking
- Health checks are lightweight (~10-50ms)
- JSON formatting has minimal performance impact
- Consider log retention policies for production

## Security Notes

- Sensitive data is automatically redacted
- Logs may contain PII - restrict log access
- Audit trails are immutable - cannot be deleted
- Use RBAC to restrict audit log access
- Enable log encryption in production
- Monitor log access patterns

## Troubleshooting

**High disk usage:**
- Implement log rotation
- Increase LOG_LEVEL from DEBUG to INFO
- Implement audit log retention policy

**Missing request_id:**
- Ensure RequestLoggingMiddleware is configured first
- Check if endpoint is in SKIP_LOGGING_PATHS

**Sensitive data in logs:**
- Add field name to REDACT_KEYS set
- Check custom exception handlers
- Review error messages for accidental data exposure

## Next Steps

1. Deploy to development environment
2. Monitor log output and performance
3. Configure log aggregation tool
4. Set up alerts for errors and warnings
5. Implement log retention policies
6. Test Kubernetes health probes
7. Configure Sentry (optional)
