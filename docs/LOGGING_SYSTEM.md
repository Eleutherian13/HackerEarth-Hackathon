# Logging System Documentation

## Overview

The LAOS logging system provides structured JSON logging with automatic sensitive data redaction, request tracking, audit trails, and health monitoring.

## Components

### 1. Structured JSON Logger (`app/core/logging.py`)

**Features:**
- JSON formatted output with timestamp, level, logger, message, request_id, user_id, correlation_id
- Automatic redaction of sensitive fields (passwords, tokens, credit cards, PII)
- Flexible output: stdout (container-friendly) or file-based
- Correlation ID propagation across async tasks
- Request ID tracking throughout request lifecycle
- Custom StructuredLogger with context methods

**Configuration via Environment:**
```bash
LOG_LEVEL=DEBUG        # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=json        # json or text
LOG_FILE_PATH=./logs/app.log  # Optional, omit for stdout only
```

**Usage:**
```python
from app.core.logging import get_logger, set_request_context

logger = get_logger(__name__)

# Simple logging
logger.info("Document uploaded successfully")

# Logging with context
logger.info_context(
    "Field verified",
    field_id=field.id,
    verification_status=field.verification_status,
    confidence_score=field.confidence_score
)

# Setting request context (automatic in middleware)
set_request_context(request_id="xyz123", user_id="user-id")
```

**Automatic Redaction:**
- Passwords, secrets, tokens, API keys
- Authorization headers
- Credit card numbers
- Social Security Numbers
- Email addresses (in data fields)
- Phone numbers

Any sensitive data matching these patterns is automatically replaced with `***REDACTED***` in logs.

### 2. Request/Response Logging Middleware (`app/api/middleware/logging.py`)

**Features:**
- Logs all HTTP requests and responses
- Automatic request ID generation or extraction from headers
- Correlation ID tracking
- Request duration measurement
- Skips logging for health checks (`/health`, `/health/ready`, `/health/live`)
- Injects request/correlation IDs in response headers

**Automatically Tracked:**
- Request method and path
- Status code
- Duration (milliseconds)
- Query parameters
- Request/Correlation IDs

**Request ID Behavior:**
1. Checks `X-Request-ID` header
2. Falls back to `X-Correlation-ID` header
3. Generates new UUID if neither provided
4. Returns in `X-Request-ID` response header

**Example Middleware Output:**
```json
{
  "timestamp": "2026-05-02T10:30:45.123456+00:00",
  "level": "INFO",
  "logger": "app.api.middleware.logging",
  "message": "POST /api/v1/documents/upload 201",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "extra": {
    "method": "POST",
    "path": "/api/v1/documents/upload",
    "status_code": 201,
    "duration_ms": 245.63
  }
}
```

### 3. Audit Logging (`app/core/audit.py`)

**Features:**
- Immutable append-only audit log table
- Captures: who, what, when, old_value, new_value, IP address, user agent
- Separate from application logs for compliance
- Integration with request context

**Audit Events Available:**
- `log_user_login()` - User login
- `log_user_logout()` - User logout
- `log_document_upload()` - Document uploaded
- `log_field_extracted()` - Field extracted
- `log_field_verified()` - Field verified by reviewer
- `log_field_edited()` - Field edited
- `log_field_rejected()` - Field rejected
- `log_action_plan_generated()` - Action plan created
- `log_action_plan_verified()` - Action plan verified
- `log_system_error()` - System error

**Usage:**
```python
from app.core.audit import log_field_verified
from app.models.domain.models import ExtractedField

# Log field verification
await log_field_verified(
    db=db,
    field_id=field.id,
    document_id=field.document_id,
    user_id=current_user.id,
    changes={
        "verification_status": {
            "old": "UNVERIFIED",
            "new": "APPROVED"
        }
    },
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent")
)

# Query audit trail
from app.core.audit import get_audit_trail

trail = get_audit_trail(
    db=db,
    document_id=document.id,
    limit=50
)
```

**Audit Log Fields:**
- `event_type` - Type of event (AuditEventType enum)
- `action` - Specific action (CREATE, UPDATE, DELETE, VERIFY, etc.)
- `entity_type` - Type of entity (User, Document, ExtractedField, etc.)
- `entity_id` - UUID of entity
- `document_id` - Related document UUID
- `user_id` - User who performed action
- `changes` - JSONB object with old/new values
- `ip_address` - Request IP address
- `user_agent` - Request user agent
- `created_at` - Timestamp (indexed)

### 4. Health Check Endpoints (`app/api/v1/endpoints/health.py`)

**Three Health Check Endpoints:**

#### 1. General Health Check
```
GET /health
```
Returns detailed status of all components.

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2026-05-02T10:30:45.123456+00:00",
  "version": "1.0.0",
  "components": {
    "database": {
      "status": "ok",
      "response_time_ms": 2.34,
      "message": null
    },
    "redis": {
      "status": "ok",
      "response_time_ms": 0.56,
      "message": null
    },
    "storage": {
      "status": "ok",
      "response_time_ms": 0.0,
      "message": null
    }
  }
}
```

#### 2. Readiness Probe
```
GET /health/ready
```
Returns 200 only if all critical dependencies are available.

**Use Case:** Kubernetes readiness probe - traffic only routed to ready pods.

#### 3. Liveness Probe
```
GET /health/live
```
Simple check that service is running (no dependency checks).

**Use Case:** Kubernetes liveness probe - restart if this fails.

**Status Values:**
- `ok` - All systems operational
- `degraded` - Some non-critical systems down
- `error` - Critical system failure

## Configuration

### Development Environment
```bash
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
LOG_FORMAT=text
```

### Production Environment
```bash
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE_PATH=/var/log/laos/app.log
```

### Kubernetes Deployment

Example health check configuration:
```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

## Example Log Output

### Text Format (Development)
```
2026-05-02 10:30:45 - app.api.v1.endpoints.auth - INFO - [550e8400-e29b-41d4-a716-446655440000] - User logged in successfully
2026-05-02 10:30:46 - app.core.audit - INFO - [550e8400-e29b-41d4-a716-446655440000] - Audit event logged: USER_LOGIN/LOGIN
```

### JSON Format (Production)
```json
{
  "timestamp": "2026-05-02T10:30:45.123456+00:00",
  "level": "INFO",
  "logger": "app.api.v1.endpoints.auth",
  "message": "User logged in successfully",
  "module": "auth",
  "function": "login",
  "line": 52,
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user-uuid",
  "extra": {
    "email": "user@example.com"
  }
}
```

## Best Practices

1. **Always use structured logging with context:**
   ```python
   # Good
   logger.info_context("Document processed", document_id=doc.id, status=status)
   
   # Avoid
   logger.info(f"Document {doc.id} processed with status {status}")
   ```

2. **Use request context for tracing:**
   - Set request context early in request lifecycle
   - Use same correlation ID across all related operations
   - Propagate correlation ID to async tasks

3. **Sensitive data handling:**
   - Never log passwords, tokens, or API keys
   - System automatically redacts known sensitive patterns
   - Review logs for custom sensitive fields

4. **Performance:**
   - Avoid logging large objects
   - Truncate response bodies if necessary
   - Use appropriate log levels (DEBUG for verbose, INFO for production)

5. **Audit trails:**
   - Log all user actions with `log_*` functions
   - Include change details in `changes` parameter
   - Query audit trail for compliance reports

## Sentry Integration (Optional)

Configure Sentry for error tracking:

```bash
SENTRY_DSN=https://your-sentry-key@sentry.io/project-id
```

The system will automatically send errors to Sentry when configured.

## Log Rotation

For production file-based logging, use a log rotation tool:

```bash
# Using logrotate (Linux)
/var/log/laos/app.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 app app
    sharedscripts
    postrotate
        systemctl reload laos
    endscript
}
```

## Troubleshooting

**Logs not appearing:**
1. Check `LOG_LEVEL` is not ERROR when expecting lower levels
2. Verify `LOG_FILE_PATH` directory is writable
3. Check stdout if `LOG_FILE_PATH` not set
4. Ensure logging configuration imported before app start

**Performance degradation:**
1. Check `LOG_LEVEL` - DEBUG can be verbose
2. Verify `LOG_FORMAT=json` in production
3. Check disk I/O if using file logging
4. Monitor audit table size and implement retention policy

**Missing sensitive data redaction:**
1. Redaction is automatic for known patterns
2. Add custom fields to `REDACT_KEYS` for application-specific fields
3. Review logs regularly for accidental sensitive data exposure
