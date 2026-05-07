# LAOS System Architecture

## High-Level System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    LAOS COURT JUDGMENT SYSTEM                   │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│  FRONTEND (React + TypeScript)                                   │
├──────────────────────────────────────────────────────────────────┤
│  • Home (Document Upload)          • Dashboard (Metrics)         │
│  • Documents List                  • Document Status             │
│  • Extraction Review (3-panel)     • Action Plan Review          │
│  • Login / User Management                                       │
└──────────────────────────────────────────────────────────────────┘
              ↑↓ HTTP/REST API (http://localhost:8000)
┌──────────────────────────────────────────────────────────────────┐
│  BACKEND (FastAPI + Python)                                      │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  API Layer (app/api/v1/endpoints/)                              │
│  • documents.py (CRUD operations)                               │
│  • documents_extraction.py (Extraction endpoints)               │
│  • review.py (Field verification)                              │
│  • dashboard_enhanced.py (Dashboard metrics)                    │
│  • action_plan.py (Action item endpoints)                       │
│                                                                   │
│  Service Layer (app/services/)                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ LLM Service (llm/ollama_client.py)                    │    │
│  │ • Extract fields with confidence scores                │    │
│  │ • Generate action plans                               │    │
│  │ • Health check & model management                     │    │
│  └────────────────────────────────────────────────────────┘    │
│           ↓↓ HTTP (localhost:11434)                              │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Ollama Server (llama3.2 model)                        │    │
│  │ • LLM inference                                       │    │
│  │ • JSON response generation                           │    │
│  │ • Auto model pulling                                 │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Extraction Service (extraction/)                      │    │
│  │ • ExtractionOrchestrator                             │    │
│  │   - Load document pages                              │    │
│  │   - Call Ollama                                      │    │
│  │   - Validate fields                                 │    │
│  │   - Sanitize values                                 │    │
│  │   - Store to database                               │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Validation & Sanitization (extraction/)               │    │
│  │ • ExtractionValidator                                │    │
│  │   - Case number format validation                    │    │
│  │   - Date range validation (1950-current)             │    │
│  │   - Confidence score range (0.0-1.0)                 │    │
│  │ • ExtractionSanitizer                                │    │
│  │   - Unicode normalization (NFKD)                     │    │
│  │   - HTML/XML tag removal                             │    │
│  │   - Whitespace collapse                              │    │
│  │   - Length enforcement (max 5000)                    │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Action Plan Service (action_plan/)                   │    │
│  │ • ActionPlanGenerator                                │    │
│  │   - Classify action types                            │    │
│  │   - Calculate priority (CRITICAL/HIGH/MEDIUM/LOW)    │    │
│  │   - Parse relative dates (within X days)             │    │
│  │   - Assess compliance risk                           │    │
│  │ • DepartmentMatcher                                  │    │
│  │   - Map to 14 Indian government departments          │    │
│  │   - Confidence scoring via keyword matching          │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                   │
│  Data Layer (app/db/ + SQLAlchemy ORM)                          │
│  • Session management                                           │
│  • Query building                                              │
│  • Transaction handling                                        │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
              ↑↓ SQLAlchemy ORM
┌──────────────────────────────────────────────────────────────────┐
│  DATABASE (PostgreSQL)                                            │
├──────────────────────────────────────────────────────────────────┤
│  Tables:                                                         │
│  • users (auth & roles)                                         │
│  • documents (PDF metadata)                                     │
│  • document_pages (page content)                                │
│  • extracted_fields (AI-extracted values)                       │
│  • action_plan_items (generated compliance items)               │
│  • departments (14 government agencies)                         │
│  • review_sessions (verification tracking)                      │
│  • audit_logs (complete audit trail)                            │
└──────────────────────────────────────────────────────────────────┘

              ↑↓ Redis Protocol
┌──────────────────────────────────────────────────────────────────┐
│  CACHE (Redis)                                                   │
├──────────────────────────────────────────────────────────────────┤
│  • Session tokens                                               │
│  • Temporary extraction results                                 │
│  • Dashboard cache                                              │
└──────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagrams

### 1. Document Processing Pipeline

```
PDF Upload
    ↓
[1. Storage]
    Document.filename = "judgment.pdf"
    Document.processing_status = "UPLOADED"
    DocumentPage records created (one per page)
    ↓
[2. Text Loading]
    For each page:
    - Try cleaned_text
    - Fallback to raw_text
    - Fallback to ocr_text
    - Concatenate with "---PAGE BREAK---"
    ↓
[3. Ollama Extraction]
    POST /api/generate
    System prompt: Legal document analyzer
    User message: Full judgment text
    Response: JSON with extracted fields
    ↓
[4. Validation]
    ExtractionValidator:
    - validate_case_number() ✓
    - validate_date() ✓
    - validate_confidence() ✓
    - validate_field_count() ✓
    ↓
[5. Sanitization]
    ExtractionSanitizer:
    - sanitize_string() [Unicode + HTML + length]
    - sanitize_date() [YYYY-MM-DD format]
    - sanitize_confidence() [0.0-1.0 range]
    ↓
[6. Database Storage]
    Create ExtractedField records:
    - field_type (CASE_NUMBER, DATE, etc.)
    - value (sanitized)
    - confidence_score (0.0-1.0)
    - source_quotes (evidence)
    - verification_status = "UNVERIFIED"
    ↓
[7. Status Update]
    Document.processing_status = "PENDING_REVIEW"
    ↓
[Complete]
    Ready for human review
```

### 2. Field Verification Workflow

```
Display Extracted Fields in 3-Panel Interface

LEFT PANEL (Field List):
- Group fields by type
- Show confidence score (color-coded)
- Show verification status icon

CENTER PANEL (PDF Viewer):
- Display page image
- Overlay SVG highlights at bbox coordinates
- Show field type and confidence in tooltip

RIGHT PANEL (Details):
- Current value (truncated to 500 chars)
- Confidence score bar (0-100%)
- Status badge
- Source evidence (quoted text)
- Action buttons (Approve/Edit/Reject/Flag)

User Actions:
[APPROVE] → verification_status = "APPROVED"
           → verified_by_user_id = current_user
           → verified_at = now
           → increment version
           → create AuditLog entry

[EDIT]     → show text input with current value
           → on save:
           → update value
           → verification_status = "EDITED"
           → store edit history (old/new/reason)
           → increment version
           → create AuditLog entry

[REJECT]   → verification_status = "REJECTED"
           → verified_at = now
           → create AuditLog entry

[FLAG]     → verification_status = "FLAGGED_FOR_REVIEW"
           → requires_human_review = true
           → create AuditLog entry
```

### 3. Action Plan Generation

```
Query for Verified Extractions:
    SELECT * FROM extracted_fields
    WHERE verification_status IN ('APPROVED', 'EDITED')
    AND document_id = ?
    ↓
[Structured Organization]
    Group by field_type:
    - case_details
    - directions_and_orders
    - deadlines_and_periods
    - appeal_information
    - compliance_requirements
    - financial_matters
    ↓
[Action Type Determination]
    Rule-based classification:
    "comply" / "implement" → COMPLIANCE
    "appeal" / "SLP" → APPEAL_CONSIDERATION
    "examine" / "verify" → INTERNAL_REVIEW
    "report" / "escalate" → ESCALATION
    "monitor" / "track" → MONITORING
    ↓
[Priority Calculation]
    IF deadline <= 7 days → CRITICAL
    ELSE IF contains "urgent"/"immediately" → CRITICAL
    ELSE IF deadline <= 30 days → HIGH
    ELSE IF deadline <= 90 days → MEDIUM
    ELSE → LOW
    ↓
[Due Date Calculation]
    Parse relative dates:
    "within 7 days" → judgment_date + 7
    "within 2 weeks" → judgment_date + 14
    "within 1 month" → judgment_date + 30
    "forthwith" / "immediately" → judgment_date + 7
    DEFAULT → judgment_date + 30
    ↓
[Department Assignment]
    DepartmentMatcher:
    - Extract entity name from order
    - Search keyword map for 14 departments
    - Calculate confidence score
    - Select best match
    ↓
[Risk Assessment]
    IF contains "contempt" → high risk
    DEFAULT → "Non-compliance may result in legal action"
    ↓
[Create ActionPlanItem Records]
    INSERT INTO action_plan_items:
    - title (from operative direction)
    - description (full text)
    - action_type (classified)
    - priority (calculated)
    - due_date (parsed)
    - responsible_department (matched)
    - risk_if_ignored (assessed)
    - completion_status = "NOT_STARTED"
    ↓
[Update Document Status]
    Document.processing_status = "VERIFIED"
    ↓
[Return to User]
    Display generated action items
    Ready for execution and monitoring
```

## Database Schema (Simplified)

```sql
-- Users & Authorization
users
├── id (UUID)
├── email (VARCHAR)
├── full_name (VARCHAR)
├── role (ENUM: SUPERADMIN, REVIEWER, OFFICER, VIEWER)
└── department_id (FK)

-- Documents
documents
├── id (UUID)
├── filename (VARCHAR)
├── processing_status (ENUM)
├── uploaded_by (FK users)
├── created_at (TIMESTAMP)
└── error_message (TEXT)

document_pages
├── id (UUID)
├── document_id (FK)
├── page_number (INT)
├── cleaned_text (TEXT) ← preferred
├── raw_text (TEXT)     ← fallback
├── ocr_text (TEXT)     ← last resort
└── bounding_boxes (JSONB)

-- Extracted Fields
extracted_fields
├── id (UUID)
├── document_id (FK)
├── field_type (ENUM)
├── value (VARCHAR 5000)
├── confidence_score (FLOAT)
├── source_quotes (JSONB array)
├── verification_status (ENUM: UNVERIFIED, APPROVED, EDITED, REJECTED, FLAGGED)
├── verified_by_user_id (FK users)
├── version (INT) ← optimistic locking
└── verified_at (TIMESTAMP)

-- Action Plan
action_plan_items
├── id (UUID)
├── document_id (FK)
├── title (VARCHAR)
├── description (TEXT)
├── action_type (ENUM)
├── priority (ENUM: CRITICAL, HIGH, MEDIUM, LOW)
├── due_date (DATE)
├── completion_status (ENUM)
├── responsible_department_id (FK)
├── risk_if_ignored (TEXT)
└── actual_completion_date (DATE)

-- Audit Trail
audit_logs
├── id (UUID)
├── entity_type (VARCHAR)
├── entity_id (UUID)
├── action (VARCHAR)
├── changes (JSONB)
├── created_by (FK users)
└── created_at (TIMESTAMP)

-- Departments
departments
├── id (UUID)
├── name (VARCHAR)
├── code (VARCHAR)
└── is_active (BOOLEAN)
```

## API Architecture

```
Base Path: /api/v1

Routers:
├── auth.py
│   ├── POST /auth/login
│   ├── POST /auth/register
│   ├── POST /auth/refresh
│   └── POST /auth/logout
│
├── documents.py
│   ├── GET /documents
│   ├── POST /documents (upload)
│   ├── GET /documents/{id}
│   ├── DELETE /documents/{id}
│   └── GET /documents/{id}/status
│
├── documents_extraction.py ← NEW
│   ├── POST /documents/{id}/extract
│   ├── GET /documents/{id}/extractions?status=UNVERIFIED
│   └── GET /documents/{id}/pages/{page}/text
│
├── review.py ← MODIFIED
│   ├── POST /review/fields/{id}/verify
│   └── POST /review/documents/{id}/generate-action-plan
│
├── dashboard_enhanced.py ← NEW
│   ├── GET /dashboard/summary
│   ├── GET /dashboard/actions?page=1&department=LAW
│   ├── GET /dashboard/critical-items
│   ├── GET /dashboard/overdue-items
│   ├── GET /dashboard/completion-trends
│   └── POST /dashboard/actions/{id}/mark-complete
│
├── action_plan.py
│   ├── GET /action-plan-items
│   └── GET /action-plan-items/{id}
│
├── cases.py
│   ├── GET /cases
│   └── GET /cases/{id}
│
└── admin.py
    ├── GET /admin/users
    ├── POST /admin/users
    ├── PUT /admin/users/{id}
    └── DELETE /admin/users/{id}
```

## Frontend Component Hierarchy

```
App.tsx (Routes)
├── Login.tsx
├── Home.tsx (Index.tsx - Upload)
├── Dashboard.tsx ← NEW
│   └── Metrics cards
│
├── Documents.tsx ← NEW
│   └── Documents list table
│
├── DocumentStatus.tsx ← NEW
│   └── Processing workflow
│
├── ExtractionReview.tsx ← NEW
│   ├── LEFT: Field list (FieldGroup → FieldItem)
│   ├── CENTER: PDFHighlightViewer.tsx ← NEW
│   │   ├── Toolbar (page nav, zoom controls)
│   │   ├── Canvas (image + SVG overlay)
│   │   └── Legend (highlights list)
│   └── RIGHT: FieldDetails (buttons + evidence)
│
├── ActionPlanReview.tsx ← NEW
│   └── ActionItemList
│       └── ActionItemCard (expandable)
│
├── VerificationPage.tsx
├── Cases.tsx
├── Departments.tsx
├── AuditTrail.tsx
└── NotFound.tsx
```

## Deployment Architecture

```
┌────────────────────────────────────────────┐
│         Docker Container Orchestration      │
├────────────────────────────────────────────┤
│                                            │
│  ┌─────────────────────────────────────┐  │
│  │  nginx (Reverse Proxy)              │  │
│  │  Ports: 80, 443                    │  │
│  └─────────────────────────────────────┘  │
│           ↓↓                               │
│  ┌──────────────────┐ ┌─────────────────┐ │
│  │ FastAPI Backend  │ │  Node Frontend  │ │
│  │ Port: 8000       │ │  Port: 5173     │ │
│  └──────────────────┘ └─────────────────┘ │
│           ↓                                │
│  ┌────────────────────────────────────┐   │
│  │      PostgreSQL Database           │   │
│  │      Port: 5432                   │   │
│  └────────────────────────────────────┘   │
│                                            │
│  ┌────────────────────────────────────┐   │
│  │      Redis Cache                  │   │
│  │      Port: 6379                   │   │
│  └────────────────────────────────────┘   │
│                                            │
└────────────────────────────────────────────┘

External Services:
┌────────────────────────────────────────────┐
│      Ollama LLM Server                     │
│      http://localhost:11434               │
└────────────────────────────────────────────┘
```

## Security Architecture

```
┌────────────────────────────────────────┐
│         Request Flow Security          │
├────────────────────────────────────────┤
│                                        │
│  1. HTTPS/TLS Layer (nginx)           │
│     └─ Encrypt in transit             │
│                                        │
│  2. Authentication Layer               │
│     ├─ JWT token in Authorization     │
│     └─ Token verification on each req │
│                                        │
│  3. Authorization Layer                │
│     ├─ Check user role                │
│     ├─ Check department membership     │
│     └─ Row-level access control       │
│                                        │
│  4. Input Validation Layer             │
│     ├─ Pydantic model validation      │
│     ├─ ContentType validation         │
│     └─ Size limit middleware          │
│                                        │
│  5. Database Layer                     │
│     ├─ Parameterized queries (ORM)    │
│     ├─ Row-level security             │
│     └─ Encrypted sensitive fields     │
│                                        │
│  6. Audit Trail                        │
│     ├─ Log all modifications          │
│     ├─ Track user & timestamp         │
│     └─ Store changes (old/new)        │
│                                        │
└────────────────────────────────────────┘
```

## Performance Optimization

```
┌─────────────────────────────────────────┐
│   Response Time Optimization            │
├─────────────────────────────────────────┤
│                                         │
│  Frontend Optimization:                 │
│  • Code splitting (lazy routes)        │
│  • Image optimization                  │
│  • CSS/JS minification                 │
│                                         │
│  Backend Optimization:                  │
│  • Query caching (Redis)               │
│  • N+1 query prevention (joins)        │
│  • Index optimization (DB)             │
│  • Async processing (FastAPI)          │
│                                         │
│  Ollama Optimization:                   │
│  • Document chunking (4000 word max)   │
│  • Temperature tuning (0.1)            │
│  • Timeout management (120s)           │
│  • Model caching (in memory)           │
│                                         │
└─────────────────────────────────────────┘

Expected Performance:
├─ API Response: <200ms (avg)
├─ Field Extraction: 30-60s (per document)
├─ Action Plan Gen: 5-10s
├─ Dashboard Load: <500ms
└─ PDF Rendering: <100ms
```

## Scalability Considerations

```
Current Architecture: Single-Instance

Horizontal Scaling Path:
├─ Load Balancer (nginx)
│  └─ Multiple FastAPI instances
│
├─ Database
│  └─ PostgreSQL replication (read replicas)
│
├─ Cache
│  └─ Redis cluster
│
└─ Ollama
   └─ Multiple instances (queue + round-robin)

To Scale:
1. Add load balancer (HAProxy/nginx)
2. Docker Swarm or Kubernetes
3. Database read replicas
4. Redis cluster
5. Ollama instance pool with job queue
```

---

This architecture ensures:

- ✓ Scalability (horizontal + vertical)
- ✓ Security (multiple layers)
- ✓ Reliability (proper error handling)
- ✓ Maintainability (clear separation of concerns)
- ✓ Performance (caching + optimization)
- ✓ Auditability (complete audit trail)
