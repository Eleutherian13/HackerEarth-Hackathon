# Architecture Guide

Complete system design, data flow, and technical decisions for LAOS.

## System Overview

LAOS is a distributed, asynchronous system designed for processing court judgments at scale while maintaining accuracy through human verification.

### Key Architectural Principles

1. **Human-in-the-Loop**: Mandatory human review before any compliance action
2. **Immutable Audit Trail**: Every change is logged and traceable
3. **Asynchronous Processing**: Long-running tasks don't block user interactions
4. **Scalability**: Horizontal scaling of workers and services
5. **Resilience**: Graceful degradation, auto-recovery
6. **Security**: End-to-end encryption, least privilege access

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Load Balancer (Nginx)                     │
│            (SSL/TLS, Rate Limiting, Compression)            │
└──────────────────────┬──────────────────────────────────────┘
       ┌──────────────┬─────────────────┬──────────────┐
       │              │                 │              │
   ┌───▼────┐    ┌────▼──┐      ┌─────▼────┐    ┌───▼────┐
   │Frontend │    │Frontend│      │ Backend  │    │Backend │
   │React 1  │    │React 2 │      │API 1     │    │API 2   │
   └────┬────┘    └───┬────┘      └─────┬────┘    └────┬───┘
        │             │                  │              │
        └──────────────┴──────────────────┴──────────────┘
                       │
          ┌────────────┼────────────┐
          │            │            │
      ┌───▼───┐    ┌───▼──┐    ┌──▼───┐
      │PostgreSQL  │Redis │    │Celery│
      │Database    │Cache │    │Queue │
      └───┬───┘    └──────┘    └──┬───┘
          │                       │
          └─────────┬─────────────┘
                    │
           ┌────────▼────────┐
           │ Worker Nodes    │
           │ (PDF, Extraction,│
           │  Action Plans)  │
           └─────────────────┘
```

## Service Architecture

### Frontend (React + Vite)

**Responsibilities:**
- User authentication UI
- Document review interface
- Action plan tracking
- Dashboard and reports
- User administration (admin only)

**Key Components:**
- `pages/`: Page-level components (LoginPage, DashboardPage, ReviewPage)
- `components/`: Reusable UI components (DocumentViewer, ActionPlanForm)
- `services/`: API client code (apiClient.ts)
- `stores/`: State management (Zustand or Context API)
- `types/`: TypeScript interfaces

**Communication:**
- REST API to backend
- WebSocket for real-time notifications (future)
- Local storage for user preferences
- No direct database access

**Deployment:**
- Single Docker container
- Behind Nginx reverse proxy
- Gzip compression enabled
- Browser caching for static assets

### Backend API (FastAPI)

**Responsibilities:**
- RESTful API endpoints
- JWT authentication and authorization
- Database operations
- Business logic
- Audit logging
- Rate limiting and security

**Layers:**

```
HTTP Request
    ↓
[Rate Limiter] → Check request limits, return 429 if exceeded
    ↓
[Router] → Route to correct endpoint handler
    ↓
[Dependency Injection] → Provide DB session, current user, etc.
    ↓
[Request Validation] → Validate request body with Pydantic
    ↓
[Authentication] → Check JWT token, get current user
    ↓
[Authorization] → Verify user has permission for this action
    ↓
[Business Logic] → Execute service layer functions
    ↓
[Audit Logging] → Log action to audit_logs table
    ↓
[Response Validation] → Ensure response matches schema
    ↓
HTTP Response
```

**Main API Endpoints:**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/auth/login` | POST | User login |
| `/api/v1/auth/refresh` | POST | Refresh JWT token |
| `/api/v1/documents` | GET | List documents |
| `/api/v1/documents` | POST | Upload judgment |
| `/api/v1/documents/{id}` | GET | Get document details |
| `/api/v1/documents/{id}/approve` | POST | Approve extraction |
| `/api/v1/documents/{id}/reject` | POST | Reject and re-extract |
| `/api/v1/actions` | GET | List action items |
| `/api/v1/actions/{id}/complete` | POST | Submit completion |
| `/api/v1/users` | GET | List users (admin) |
| `/api/v1/users` | POST | Create user (admin) |

**Key Services:**

- **ExtractionService**: LLM-based field extraction
- **ActionPlanService**: Generate action items from extractions
- **AuditService**: Log all activities
- **EmailService**: Send notifications
- **ReportService**: Generate analytics reports

**Technology:**
- FastAPI framework (async Python)
- SQLAlchemy 2.0 ORM
- Pydantic v2 validation
- JWT authentication
- Middleware stack:
  - CORS
  - Rate limiting
  - Audit logging
  - Error handling

### Database (PostgreSQL)

**Primary storage** for all persistent data.

**Key Tables:**

```sql
-- Users and access control
users (id, email, password_hash, full_name, role, department_id, ...)
departments (id, name, code, budget, contact_email, ...)
audit_logs (id, user_id, action, resource_type, resource_id, changes, ...)

-- Document processing
judgments (id, file_path, file_name, status, uploaded_by, ...)
judgment_extractions (id, judgment_id, case_number, litigants, directions, ...)
extraction_fields (id, extraction_id, field_name, value, confidence_score, ...)

-- Action planning
action_plans (id, judgment_id, created_by, created_at, ...)
action_items (id, action_plan_id, type, description, status, deadline, ...)
action_completions (id, action_item_id, submitted_by, evidence_doc, verified_by, ...)

-- System state
background_jobs (id, task_type, status, result, error, ...)
cache_invalidation (id, key, expires_at, ...)
```

**Design Decisions:**
- Normalized schema for data integrity
- JSONB columns for extraction metadata
- Partitioned tables for large datasets (audit_logs)
- Indexes on frequently queried columns
- Foreign keys with CASCADE delete where appropriate

### Cache Layer (Redis)

**Temporary storage** for frequently accessed data and session management.

**Uses:**
- User sessions (30-minute TTL)
- JWT blacklist (token revocation)
- Rate limit counters
- Database query results
- Task queue (Celery)
- Pub/sub for notifications

**Data:**
```
Key Format: namespace:resource_id:subkey
Examples:
  session:abc123def456      → User session data
  rate_limit:192.168.1.1    → IP address request count
  judgment:123:extraction   → Cached extraction results
  task:job_123              → Background job status
```

**Expiration Strategy:**
- Sessions: 30 minutes
- Rate limits: 60 seconds
- Query results: 5 minutes
- Task results: 24 hours

### Worker Pool (Celery)

**Asynchronous task processing** for long-running operations.

**Tasks:**
- PDF processing (text extraction, OCR)
- LLM-based field extraction
- Action plan generation
- Email notifications
- Report generation
- Data export

**Task Flow:**
```
User uploads PDF
    ↓
Backend creates Task("process_document")
    ↓
Task pushed to Redis queue
    ↓
Worker picks up task
    ↓
Worker extracts text (Tesseract/PaddleOCR)
    ↓
Worker calls LLM (OpenAI GPT-4o-mini)
    ↓
Worker saves extracted fields
    ↓
Worker pushes notification
    ↓
Frontend receives notification
    ↓
User notified: "Document ready for review"
```

**Scaling:**
- Horizontal: Run multiple workers
- Each worker processes tasks independently
- Redis queue handles task distribution
- Celery Beat scheduler for periodic tasks

---

## Data Flow

### 1. Document Upload Flow

```
Frontend                    Backend                 Workers             Database
   │                          │                        │                    │
   ├─────Upload PDF────────────>                       │                    │
   │                          │                        │                    │
   │         <──────Response──┤                        │                    │
   │         (Document ID)    │                        │                    │
   │                          │                        │                    │
   │                    ┌─────────────────────────────>│                    │
   │                    │   Enqueue OCR task          │                    │
   │                    │                            │                    │
   │                    │                    ┌──────────────────────────>│
   │                    │                    │ Save document & status    │
   │                    │                    │ (UPLOADED)               │
   │                    │                    │                        │
   │                    │<───────────────────┤   Update status to        │
   │                    │     Extraction    │  (PROCESSING)           │
   │                    │      started      │                        │
   │                    │                    │                        │
   │<──────Notification─┤                    │                        │
   │   (Queued for      │                    │                        │
   │    processing)     │                    │                        │
   │                    │                    │ Extract text             │
   │                    │                    │ (Tesseract/PaddleOCR)   │
   │                    │                    │                        │
   │                    │                    │ Call LLM for extraction │
   │                    │                    │                        │
   │                    │                    │ Save extracted fields    │
   │                    │                    │ (with confidence scores) │
   │                    │                    │                        │
   │                    │<───────────────────┤   Extraction complete    │
   │                    │    Update status to        │
   │                    │  (PENDING_REVIEW)          │
   │                    │                            │
   │<──────Notification─┤                    │                        │
   │   (Ready for review)  │                        │                    │
   │                    │                        │                    │
```

### 2. Document Review Flow

```
Reviewer               Frontend                Backend            Database
   │                      │                        │                  │
   ├─Open Dashboard────────>                       │                  │
   │                      │                        │                  │
   │<────Document List─────┤                       │                  │
   │  (status=PENDING)     │ ┌─Request pending docs>                  │
   │                      │ │                      │                  │
   │                      │ │      <─SELECT * FROM judgments...──────>│
   │                      │ │                      │                  │
   │                      │ │<────────Results────────────────────────┤
   │                      │ │                      │                  │
   │<────Display list──────┤                       │                  │
   │                      │                        │                  │
   ├─Select document──────────>                    │                  │
   │                      │                        │                  │
   │<───View extraction────┤ ┌─Get extraction with>                  │
   │ (PDF + fields)        │ │   confidence scores │                  │
   │                      │ │                      │                  │
   │                      │ │<─────Data + scores──────────────────────┤
   │                      │<─────Display─────────────┤                │
   │                      │                        │                  │
   ├─Edit field-----------────> Save correction   │                  │
   │                      │                        │                  │
   │<─Confirmation────────┤ ┌──Update extraction──>│                  │
   │                      │                        │                  │
   │                      │                      ┌─────UPDATE judgment_extractions
   │                      │                      │  SET case_number = '...'
   │                      │                      │  WHERE id = X
   │                      │                      │
   │                      │                      ├─────INSERT INTO audit_logs
   │                      │                      │  (action=EDITED, ...)
   │                      │                      │
   │                      │<─────Saved─────────────────────────────────┤
   │                      │                        │                  │
   ├─Approve document─────────> Validate all fields│                  │
   │                      │                        │                  │
   │                      │ ┌─Check all fields are populated>         │
   │                      │ │                      │                  │
   │                      │ │<─Validation Result──────────────────────┤
   │                      │                        │                  │
   │<─Approve confirmed───┤ ┌─UPDATE status to    │                  │
   │                      │ │  APPROVED            │                  │
   │                      │ │ ─INSERT INTO audit_logs
   │                      │ │  (action=APPROVED)   │
   │                      │ │ ─ENQUEUE generate_action_plan task
   │                      │<────Approved────────────────────────────────┤
   │                      │                        │                  │
   │<─Notification────────┤                        │                  │
   │ (Status: APPROVED)   │                        │                  │
   │                      │                        │                  │
```

### 3. Action Plan Generation & Completion

```
System               Extraction        Action Plan        Database
   │                  Service            Service            │
   │                    │                   │                │
   ├─Extraction────────>│                   │                │
   │ (approved)        │                   │                │
   │                   │──Parse directions │                │
   │                   │──Extract deadlines│                │
   │                   │<─────────────────>│                │
   │                   │                   │─Create items   │
   │                   │                   │───────────────>│
   │                   │                   │                │
   │<──────Notify Officer: "Action assigned to you"──────────┤
   │                   │                   │                │
   │                   │                   │<─Get action────┤
   │                   │                   │     item       │
   │ Officer submits                       │                │
   │ completion────────────────────────────────────────────>│
   │                                       │ ┌─Verify       │
   │                                       │ │ evidence    │
   │                                       │ │ document    │
   │ Reviewer approves                     │ │             │
   │ completion────────────────────────────────────────────>│
   │                                       │ ┌─Mark as      │
   │                                       │ │ COMPLETED    │
   │                                       │ │             │
   │<──────Notify: "Action completed"──────────────────────┤
   │                                       │                │
```

---

## Data Models

### Key Entities

#### User
```python
class User(Base):
    id: UUID
    email: str                    # Unique login email
    password_hash: str            # Bcrypt hash
    full_name: str
    role: UserRole               # SUPERADMIN, ADMIN, REVIEWER, OFFICER
    department_id: UUID          # Assigned department
    is_active: bool              # Deactivation flag
    created_at: datetime
    last_login: datetime
```

#### Judgment
```python
class Judgment(Base):
    id: UUID
    file_name: str               # Original PDF name
    file_path: str               # S3/local storage path
    file_size_bytes: int
    status: JudgmentStatus       # UPLOADED, PROCESSING, PENDING_REVIEW, APPROVED, REJECTED
    uploaded_by: UUID            # User ID
    uploaded_at: datetime
    reviewed_by: UUID | None     # Reviewer ID
    reviewed_at: datetime | None
```

#### JudgmentExtraction
```python
class JudgmentExtraction(Base):
    id: UUID
    judgment_id: UUID
    
    # Extracted fields
    case_number: str | None
    court_name: str | None
    judgment_date: date | None
    litigants: str | None        # JSON array
    directions: str | None       # Full text
    
    # Metadata
    extraction_confidence: float  # Overall confidence 0.0-1.0
    extracted_at: datetime
    is_manually_verified: bool
    verified_by: UUID | None
```

#### ActionItem
```python
class ActionItem(Base):
    id: UUID
    action_plan_id: UUID
    type: ActionItemType         # MONETARY_FINE, IMPLEMENTATION, etc.
    description: str             # What needs to be done
    status: ActionItemStatus     # ASSIGNED, IN_PROGRESS, PENDING_VERIFICATION, COMPLETED
    deadline: date
    assigned_to: UUID            # Officer ID
    assigned_at: datetime
    completed_at: datetime | None
    evidence_document_id: UUID | None
```

#### AuditLog
```python
class AuditLog(Base):
    id: UUID
    user_id: UUID
    action: str                  # VIEW, EDIT, APPROVE, REJECT, CREATE, DELETE
    resource_type: str           # judgment, extraction, user, action_item
    resource_id: UUID
    changes: dict                # {field: {old: value, new: value}}
    ip_address: str
    user_agent: str
    created_at: datetime
```

---

## API Contract

### Request/Response Format

**All API responses follow standard format:**

```json
{
  "status": "success" | "error",
  "data": {...},
  "error": "Optional error message",
  "timestamp": "2024-05-01T10:30:00Z"
}
```

**Example: List Documents**
```json
GET /api/v1/documents?status=PENDING_REVIEW&page=1&per_page=50

Response:
{
  "status": "success",
  "data": {
    "items": [
      {
        "id": "uuid-123",
        "file_name": "judgment_2024.pdf",
        "case_number": null,
        "status": "PENDING_REVIEW",
        "uploaded_at": "2024-05-01T09:30:00Z",
        "uploaded_by_name": "User Name"
      }
    ],
    "pagination": {
      "total": 125,
      "page": 1,
      "per_page": 50,
      "pages": 3
    }
  },
  "timestamp": "2024-05-01T10:30:00Z"
}
```

**Example: Approve Document**
```json
POST /api/v1/documents/{id}/approve

Request:
{
  "comment": "All fields verified against original"
}

Response:
{
  "status": "success",
  "data": {
    "id": "uuid-123",
    "status": "APPROVED",
    "approved_at": "2024-05-01T10:30:00Z",
    "action_plan_generated": true,
    "action_items_count": 3
  },
  "timestamp": "2024-05-01T10:30:00Z"
}
```

### Authentication

All endpoints (except `/health` and `/login`) require:

```
Authorization: Bearer <JWT_TOKEN>
```

**Token Structure:**
```json
{
  "sub": "user@example.com",
  "user_id": "uuid-123",
  "role": "REVIEWER",
  "department_id": "uuid-456",
  "exp": 1640000000,
  "iat": 1640000000
}
```

---

## Storage Architecture

### File Storage

**Options (configurable):**

1. **Local Filesystem** (Development)
   - Path: `/app/storage/documents/`
   - Good for: Testing, small deployments
   - Backup: Manual copy

2. **S3 Compatible** (Production)
   - Bucket: `laos-documents`
   - Path format: `s3://laos-documents/{year}/{month}/{document_id}.pdf`
   - Encryption: Server-side with KMS keys
   - Versioning: Enabled
   - Lifecycle: Archive after 1 year

3. **Azure Blob Storage** (Alternative)
   - Container: `laos-documents`
   - Path format: `blob://laos-documents/{year}/{month}/{document_id}/`
   - Encryption: At rest and in transit
   - Lifecycle: Auto-delete after 7 years

**Configuration:**
```python
# In core/config.py
STORAGE_TYPE = "s3"  # or "local", "azure"

if STORAGE_TYPE == "s3":
    S3_BUCKET = "laos-documents"
    S3_REGION = "ap-south-1"
    S3_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
    S3_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
```

### Database Storage

**PostgreSQL:**
- ACID compliance (atomicity, consistency, isolation, durability)
- Referential integrity via foreign keys
- Row-level security (future)
- Automated backups every 4 hours
- Point-in-time recovery enabled

---

## Security Architecture

### Authentication & Authorization

**Flow:**
```
User Login
    ↓
POST /api/v1/auth/login {email, password}
    ↓
Backend validates email + password
    ↓
Backend generates JWT access token (30 min)
                           + refresh token (7 days)
    ↓
Frontend stores tokens in secure httpOnly cookies
    ↓
Subsequent requests include JWT in Authorization header
    ↓
Middleware validates JWT signature
    ↓
Endpoint checks user role/permissions
    ↓
Log action to audit_logs
```

**Token Blacklist:**
- On logout, token added to Redis
- Middleware checks token against blacklist
- Prevents token reuse after logout

### Role-Based Access Control (RBAC)

**Roles and Permissions:**

| Role | Permissions |
|------|-------------|
| SUPERADMIN | Everything - users, departments, system config |
| ADMIN | Manage users in department, view all documents/actions |
| REVIEWER | Review documents, approve/reject extractions |
| OFFICER | View assigned actions, submit completions |

**Example Authorization Check:**
```python
@app.post("/api/v1/documents/{id}/approve")
async def approve_document(
    id: UUID,
    current_user: User = Depends(get_current_user)
):
    # Check: Is user a REVIEWER or ADMIN?
    if current_user.role not in [UserRole.REVIEWER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    # Check: Does user have access to this document?
    doc = get_document(id)
    if current_user.role == UserRole.ADMIN:
        # Admin can see all documents in their department
        if doc.department_id != current_user.department_id:
            raise HTTPException(status_code=403, detail="Forbidden")
    
    # Proceed with approval
    approve(doc, current_user)
```

### Data Encryption

**In Transit:**
- HTTPS/TLS 1.2+ (enforced)
- Certificate: Let's Encrypt
- HSTS enabled (Strict-Transport-Security header)

**At Rest:**
- Database passwords: Encrypted in .env (not committed)
- JWT secrets: 256-bit keys
- File storage: S3 server-side encryption (KMS)
- Sensitive fields: Encrypted at database level (future)

### Audit Trail

**Every action logged:**
```sql
INSERT INTO audit_logs (
  user_id,
  action,              -- VIEW, EDIT, APPROVE, REJECT, CREATE, DELETE
  resource_type,       -- judgment, extraction, user, action_item
  resource_id,
  changes,             -- JSON: {field: {old: val, new: val}}
  ip_address,
  user_agent,
  created_at
)
```

**Audit logs immutable:**
- Never updated or deleted
- Queryable by date range, user, action type
- Compliance reports generated from audit logs
- Retention: Indefinite

---

## Performance Optimization

### Database Optimization

**Indexing Strategy:**
```sql
-- Frequently searched fields
CREATE INDEX idx_judgments_status ON judgments(status);
CREATE INDEX idx_judgments_created_at ON judgments(created_at DESC);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);

-- Composite indexes for common queries
CREATE INDEX idx_action_items_status_deadline 
  ON action_items(status, deadline);
```

**Query Optimization:**
- Use `EXPLAIN ANALYZE` to identify slow queries
- Limit result sets with pagination
- Use database views for complex reports
- Avoid N+1 queries with eager loading

### Caching Strategy

**Redis Cache Layers:**

```
L1: Database query cache (5 minutes)
    SELECT COUNT(*) FROM judgments WHERE status='APPROVED'

L2: Session cache (30 minutes)
    User login session, JWT token info

L3: Rate limit counters (60 seconds)
    Track requests per user/IP

L4: Static data cache (1 hour)
    Departments, user roles, system config
```

**Cache Invalidation:**
```python
# When document status changes
cache.delete(f"judgment:{judgment_id}:extraction")
cache.delete(f"user:{user_id}:documents")

# Bulk invalidation
cache.delete_pattern("action_items:*")
```

### API Response Optimization

- Pagination: Always limit results (default: 50 per page)
- Lazy loading: Don't fetch related data unless needed
- Field selection: Allow clients to request specific fields (future)
- Response compression: Gzip enabled
- Browser caching: Set Cache-Control headers

---

## Scalability

### Horizontal Scaling

**Backend replicas:**
```bash
# Run 3 backend instances with load balancing
docker compose scale backend=3

# Nginx distributes traffic round-robin
upstream backend {
    server backend-1:8000;
    server backend-2:8000;
    server backend-3:8000;
}
```

**Worker scaling:**
```bash
# Run 5 workers for CPU-bound tasks
celery -A app.worker --concurrency=5

# Task distribution via Redis queue
# Workers pick tasks based on availability
```

**Database scaling:**
- Read replicas for analytics queries
- Write operations to primary
- Connection pooling (PgBouncer)

### Load Testing Results

**Single backend instance:**
- 150 requests/second
- p95 latency: 500ms
- Memory: 200MB
- CPU: 20%

**3 backend instances (load balanced):**
- 450 requests/second (+3x)
- p95 latency: 300ms (faster)
- Memory: 600MB (3x)
- CPU: 25% per instance

---

## Deployment Architecture

### Development
```
docker-compose up
├── Backend (1 instance, hot-reload)
├── Frontend (Vite dev server)
├── PostgreSQL (single)
├── Redis (single)
└── Celery worker (1 instance)
```

### Production
```
docker-compose -f docker-compose.prod.yml up -d
├── Nginx (reverse proxy)
├── Backend (3+ replicas)
├── Frontend (1+ replicas)
├── PostgreSQL (replicated)
├── Redis (cluster or sentinel)
└── Celery workers (5+ workers)
```

---

## Technology Stack Justification

See [docs/ADR/](docs/ADR/) for detailed architecture decisions:

- [ADR-002: FastAPI async vs Flask sync](docs/ADR/ADR-002-fastapi-async-vs-flask-sync.md)
- [ADR-003: PostgreSQL JSONB vs Document Store](docs/ADR/ADR-003-postgresql-jsonb-vs-document-store.md)
- [ADR-004: Redis/Celery vs In-Memory Queues](docs/ADR/ADR-004-redis-celery-vs-in-memory-queues.md)
- [ADR-010: Custom Pipeline vs LangChain](docs/ADR/ADR-010-custom-pipeline-vs-langchain.md)

---

## Future Enhancements

**Planned Improvements:**

1. **GraphQL API**: Complement REST for flexible queries
2. **Real-time Notifications**: WebSocket for live updates
3. **ML-based Field Confidence**: Train confidence model on user corrections
4. **Full-Text Search**: Elasticsearch for judgment text search
5. **Row-Level Security**: Database-level permissions
6. **API Rate Limiting per Endpoint**: Different limits for different endpoints
7. **Kubernetes Deployment**: K8s manifests for cloud deployment
8. **Observability**: Prometheus metrics, Grafana dashboards, Jaeger tracing
9. **Document Diff Viewer**: Side-by-side comparison of extracted vs. manual data

---

**Last Updated**: May 1, 2024
**Reviewed by**: Architecture Team
