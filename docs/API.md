# API Documentation

Complete reference for LAOS REST API endpoints, request/response formats, authentication, and error handling.

## API Overview

**Base URL**: `https://yourdomain.com/api/v1`

**Authentication**: JWT Bearer token (except `/auth/login` and `/health`)

**Response Format**: JSON with standard envelope:
```json
{
  "status": "success" | "error",
  "data": {...} | null,
  "error": "Error message if status=error",
  "timestamp": "2024-05-01T10:30:00Z"
}
```

---

## Authentication Endpoints

### Login

Creates JWT access and refresh tokens.

**Endpoint**: `POST /auth/login`

**Request**:
```json
{
  "email": "user@example.com",
  "password": "UserPassword123!"
}
```

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "user": {
      "id": "uuid-123",
      "email": "user@example.com",
      "full_name": "John Reviewer",
      "role": "REVIEWER",
      "department": {
        "id": "uuid-456",
        "name": "Revenue Department"
      }
    }
  },
  "timestamp": "2024-05-01T10:30:00Z"
}
```

**Errors**:
- 401: Invalid email/password
- 429: Too many login attempts

**Usage in Requests**:
```bash
# Store token
ACCESS_TOKEN="eyJhbGciOiJIUzI1NiIs..."

# Use in headers
curl -H "Authorization: Bearer $ACCESS_TOKEN" \
  https://yourdomain.com/api/v1/documents
```

### Refresh Token

Get new access token using refresh token.

**Endpoint**: `POST /auth/refresh`

**Headers**:
```
Authorization: Bearer <refresh_token>
```

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
  }
}
```

**Errors**:
- 401: Invalid or expired refresh token
- 401: Refresh token revoked (user logged out)

### Logout

Revoke tokens (adds to blacklist).

**Endpoint**: `POST /auth/logout`

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {"message": "Logged out successfully"}
}
```

---

## Document Endpoints

### List Documents

Get paginated list of documents with filters.

**Endpoint**: `GET /documents`

**Query Parameters**:
```
status: UPLOADED | PROCESSING | PENDING_REVIEW | APPROVED | REJECTED
department_id: UUID (admin only, filter by department)
page: integer (default: 1)
per_page: integer (default: 50, max: 500)
sort_by: uploaded_at | case_number | status (default: uploaded_at)
sort_order: asc | desc (default: desc)
```

**Example Request**:
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "https://yourdomain.com/api/v1/documents?status=PENDING_REVIEW&page=1&per_page=25"
```

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "items": [
      {
        "id": "uuid-123",
        "file_name": "judgment_2024-RC-456.pdf",
        "file_size_bytes": 250000,
        "status": "PENDING_REVIEW",
        "uploaded_at": "2024-05-01T09:30:00Z",
        "uploaded_by_name": "Officer Name",
        "case_number": null,
        "extraction_confidence": null,
        "reviewed_by_name": null
      }
    ],
    "pagination": {
      "total": 125,
      "page": 1,
      "per_page": 25,
      "pages": 5
    }
  },
  "timestamp": "2024-05-01T10:30:00Z"
}
```

### Upload Document

Upload a judgment PDF for processing.

**Endpoint**: `POST /documents`

**Headers**:
```
Content-Type: multipart/form-data
Authorization: Bearer <access_token>
```

**Request Body**:
```
file: PDF file (max 50MB)
case_number: string (optional)
description: string (optional)
```

**Response** (201 Created):
```json
{
  "status": "success",
  "data": {
    "id": "uuid-789",
    "file_name": "judgment_2024.pdf",
    "status": "PROCESSING",
    "uploaded_at": "2024-05-01T10:30:00Z",
    "message": "Document queued for processing. Status updates via notifications."
  },
  "timestamp": "2024-05-01T10:30:00Z"
}
```

**Errors**:
- 400: File too large
- 400: Invalid file format (not PDF)
- 413: Payload too large
- 429: Upload rate limit exceeded

**Example with curl**:
```bash
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@judgment.pdf" \
  -F "case_number=2024-RC-123" \
  https://yourdomain.com/api/v1/documents
```

### Get Document

Retrieve document details and extraction.

**Endpoint**: `GET /documents/{id}`

**Path Parameters**:
```
id: UUID - Document ID
```

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "id": "uuid-123",
    "file_name": "judgment_2024.pdf",
    "file_url": "https://yourdomain.com/api/v1/documents/uuid-123/file",
    "status": "PENDING_REVIEW",
    "uploaded_at": "2024-05-01T09:30:00Z",
    "uploaded_by": {
      "id": "uuid-456",
      "email": "officer@example.com",
      "full_name": "Officer Name"
    },
    "extraction": {
      "id": "uuid-789",
      "case_number": "2024-RC-123",
      "court_name": "High Court of Madhya Pradesh",
      "judgment_date": "2024-04-15",
      "litigants": ["Government", "Private Party"],
      "directions": "Full text of court directions...",
      "extraction_confidence": 0.92,
      "is_manually_verified": false,
      "extracted_at": "2024-05-01T09:35:00Z",
      "fields": [
        {
          "name": "case_number",
          "value": "2024-RC-123",
          "confidence": 0.99,
          "is_corrected": false
        },
        {
          "name": "court_name",
          "value": "High Court of Madhya Pradesh",
          "confidence": 0.95,
          "is_corrected": false
        }
      ]
    },
    "action_plan": {
      "id": "uuid-101",
      "status": "ACTIVE",
      "action_items_count": 3,
      "completed_count": 0
    }
  },
  "timestamp": "2024-05-01T10:30:00Z"
}
```

**Errors**:
- 404: Document not found
- 403: Access denied

### Download Document

Download original PDF file.

**Endpoint**: `GET /documents/{id}/file`

**Response** (200 OK):
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="judgment_2024.pdf"
Content-Length: 250000

[Binary PDF data]
```

**Errors**:
- 404: Document not found
- 403: Access denied

### Approve Document

Approve extraction and generate action plan.

**Endpoint**: `POST /documents/{id}/approve`

**Headers**:
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body**:
```json
{
  "comment": "All fields verified against original document"
}
```

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "id": "uuid-123",
    "status": "APPROVED",
    "approved_at": "2024-05-01T10:30:00Z",
    "approved_by": "reviewer@example.com",
    "action_plan": {
      "id": "uuid-101",
      "action_items_count": 3,
      "created_at": "2024-05-01T10:30:00Z"
    }
  },
  "timestamp": "2024-05-01T10:30:00Z"
}
```

**Errors**:
- 400: Document status not PENDING_REVIEW
- 400: Extraction incomplete (missing required fields)
- 403: User role cannot approve
- 404: Document not found

### Reject Document

Reject extraction and request re-processing.

**Endpoint**: `POST /documents/{id}/reject`

**Headers**:
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body**:
```json
{
  "reason": "Extraction quality too low",
  "feedback": "More than 50% of fields are incorrect or unconfident"
}
```

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "id": "uuid-123",
    "status": "REJECTED",
    "rejected_at": "2024-05-01T10:30:00Z",
    "rejected_by": "reviewer@example.com",
    "message": "Document returned to UPLOADED status for re-extraction"
  },
  "timestamp": "2024-05-01T10:30:00Z"
}
```

---

## Extraction Endpoints

### Update Extraction Field

Correct an extracted field during review.

**Endpoint**: `PATCH /documents/{id}/extraction/fields/{field_name}`

**Headers**:
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body**:
```json
{
  "value": "Corrected value",
  "comment": "Changed from 'Indore' to 'Indore Bench' for clarity"
}
```

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "field_name": "court_name",
    "value": "Indore Bench",
    "is_corrected": true,
    "corrected_at": "2024-05-01T10:30:00Z",
    "comment": "Changed from 'Indore' to 'Indore Bench' for clarity"
  },
  "timestamp": "2024-05-01T10:30:00Z"
}
```

**Errors**:
- 400: Field is immutable
- 400: Invalid value for field
- 404: Field not found
- 404: Document not found

---

## Action Plan Endpoints

### List Action Items

Get action items assigned to current user or department.

**Endpoint**: `GET /actions`

**Query Parameters**:
```
status: ASSIGNED | IN_PROGRESS | PENDING_VERIFICATION | COMPLETED | OVERDUE
assigned_to_me: boolean (filter for current user)
department_id: UUID (admin only)
page: integer (default: 1)
per_page: integer (default: 50)
sort_by: deadline | created_at (default: deadline)
```

**Example Request**:
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "https://yourdomain.com/api/v1/actions?status=ASSIGNED&assigned_to_me=true"
```

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "items": [
      {
        "id": "uuid-201",
        "type": "IMPLEMENTATION",
        "description": "Install pollution control equipment at facility",
        "status": "ASSIGNED",
        "deadline": "2024-06-30",
        "days_remaining": 60,
        "priority": "HIGH",
        "assigned_at": "2024-05-01T09:30:00Z",
        "assigned_to": {
          "id": "uuid-456",
          "email": "officer@example.com",
          "full_name": "Officer Name"
        },
        "judgment": {
          "id": "uuid-123",
          "case_number": "2024-RC-123",
          "court_name": "High Court"
        }
      }
    ],
    "pagination": {
      "total": 25,
      "page": 1,
      "per_page": 50
    }
  },
  "timestamp": "2024-05-01T10:30:00Z"
}
```

### Get Action Item

Retrieve detailed action item information.

**Endpoint**: `GET /actions/{id}`

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "id": "uuid-201",
    "type": "IMPLEMENTATION",
    "description": "Install pollution control equipment at facility",
    "status": "ASSIGNED",
    "deadline": "2024-06-30",
    "days_remaining": 60,
    "priority": "HIGH",
    "assigned_at": "2024-05-01T09:30:00Z",
    "assigned_to": {
      "id": "uuid-456",
      "email": "officer@example.com",
      "full_name": "Officer Name"
    },
    "judgment": {
      "id": "uuid-123",
      "file_name": "judgment_2024.pdf",
      "case_number": "2024-RC-123",
      "court_name": "High Court of Madhya Pradesh",
      "directions": "Full text of court directions..."
    },
    "action_plan": {
      "id": "uuid-101",
      "total_items": 3,
      "completed_items": 0
    },
    "timeline": [
      {
        "date": "2024-05-01",
        "event": "Action assigned",
        "by": "reviewer@example.com"
      }
    ]
  },
  "timestamp": "2024-05-01T10:30:00Z"
}
```

### Start Action Item

Mark action as "In Progress".

**Endpoint**: `POST /actions/{id}/start`

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "id": "uuid-201",
    "status": "IN_PROGRESS",
    "started_at": "2024-05-01T10:30:00Z",
    "deadline_alert": "30 days remaining"
  }
}
```

### Submit Action Completion

Submit completion evidence.

**Endpoint**: `POST /actions/{id}/complete`

**Headers**:
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Request Body**:
```
evidence_document: File (PDF, image, or document)
evidence_type: OFFICIAL_LETTER | COMPLIANCE_CERT | PAYMENT_RECEIPT | REPORT | PHOTO | OTHER
description: string (What does this document show?)
comment: string (Additional context)
```

**Response** (201 Created):
```json
{
  "status": "success",
  "data": {
    "id": "uuid-201",
    "completion": {
      "id": "uuid-302",
      "status": "PENDING_VERIFICATION",
      "submitted_at": "2024-05-01T10:30:00Z",
      "submitted_by": "officer@example.com",
      "evidence": {
        "file_name": "compliance_cert.pdf",
        "evidence_type": "COMPLIANCE_CERT",
        "description": "Environmental audit certificate from authorized agency"
      }
    },
    "message": "Submission received. Reviewer will verify within 3-5 days."
  }
}
```

**Errors**:
- 400: Action already completed
- 400: Deadline passed (can request extension)
- 400: Required evidence missing
- 413: File too large

### Request Extension

Request deadline extension.

**Endpoint**: `POST /actions/{id}/request-extension`

**Headers**:
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body**:
```json
{
  "new_deadline": "2024-07-15",
  "reason": "Procurement delayed due to supplier issues",
  "supporting_docs": "Can provide email correspondence"
}
```

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "id": "uuid-201",
    "extension_request": {
      "status": "PENDING_APPROVAL",
      "requested_at": "2024-05-01T10:30:00Z",
      "current_deadline": "2024-06-30",
      "proposed_deadline": "2024-07-15",
      "requested_by": "officer@example.com",
      "message": "Extension request submitted for supervisor approval"
    }
  }
}
```

---

## User Management Endpoints (Admin Only)

### List Users

Get all users in system (admin only).

**Endpoint**: `GET /users`

**Query Parameters**:
```
role: ADMIN | REVIEWER | OFFICER
department_id: UUID
status: active | inactive
page: integer
per_page: integer
```

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "items": [
      {
        "id": "uuid-456",
        "email": "user@example.com",
        "full_name": "User Name",
        "role": "REVIEWER",
        "department": {
          "id": "uuid-789",
          "name": "Revenue Department"
        },
        "is_active": true,
        "last_login": "2024-05-01T10:00:00Z",
        "created_at": "2024-04-01T00:00:00Z"
      }
    ],
    "pagination": {
      "total": 45,
      "page": 1,
      "per_page": 50
    }
  }
}
```

### Create User

Create new user (admin only).

**Endpoint**: `POST /users`

**Request Body**:
```json
{
  "email": "newuser@example.com",
  "full_name": "New User",
  "role": "REVIEWER",
  "department_id": "uuid-789"
}
```

**Response** (201 Created):
```json
{
  "status": "success",
  "data": {
    "id": "uuid-999",
    "email": "newuser@example.com",
    "full_name": "New User",
    "role": "REVIEWER",
    "created_at": "2024-05-01T10:30:00Z",
    "message": "User created. Invitation email sent to newuser@example.com"
  }
}
```

### Update User

Update user details (admin only).

**Endpoint**: `PATCH /users/{id}`

**Request Body**:
```json
{
  "full_name": "Updated Name",
  "role": "ADMIN",
  "is_active": true
}
```

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "id": "uuid-456",
    "email": "user@example.com",
    "full_name": "Updated Name",
    "role": "ADMIN",
    "updated_at": "2024-05-01T10:30:00Z"
  }
}
```

### Deactivate User

Deactivate user account (admin only).

**Endpoint**: `POST /users/{id}/deactivate`

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "id": "uuid-456",
    "is_active": false,
    "message": "User deactivated. They can no longer login."
  }
}
```

---

## Report Endpoints

### Dashboard Metrics

Get dashboard summary metrics.

**Endpoint**: `GET /reports/dashboard`

**Query Parameters**:
```
department_id: UUID (filter by department)
date_range: 7d | 30d | 90d | custom (default: 7d)
from_date: YYYY-MM-DD (for custom range)
to_date: YYYY-MM-DD (for custom range)
```

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "overview": {
      "total_judgments": 245,
      "pending_review": 12,
      "approved": 180,
      "rejected": 8,
      "approval_rate": 95.7
    },
    "actions": {
      "total_items": 387,
      "assigned": 45,
      "in_progress": 78,
      "completed": 264,
      "completion_rate": 68.2
    },
    "performance": {
      "avg_review_time_days": 2.5,
      "avg_completion_time_days": 35.8,
      "completion_rate_by_department": {
        "Revenue": 75,
        "Home": 62,
        "Health": 58
      }
    }
  }
}
```

### Generate Report

Generate custom compliance report.

**Endpoint**: `POST /reports/generate`

**Request Body**:
```json
{
  "report_type": "compliance",
  "date_range": "custom",
  "from_date": "2024-04-01",
  "to_date": "2024-04-30",
  "department_ids": ["uuid-789"],
  "format": "pdf"
}
```

**Response** (200 OK):
```json
{
  "status": "success",
  "data": {
    "report_id": "uuid-report-123",
    "status": "GENERATING",
    "message": "Report generation started. Download link will be sent to your email.",
    "download_url": "https://yourdomain.com/api/v1/reports/uuid-report-123/download"
  }
}
```

---

## Health Check Endpoint

### Health Status

Get system health without authentication.

**Endpoint**: `GET /health`

**Response** (200 OK):
```json
{
  "status": "healthy",
  "timestamp": "2024-05-01T10:30:00Z",
  "components": {
    "database": "connected",
    "redis": "connected",
    "workers": "operational",
    "storage": "operational"
  },
  "uptime_seconds": 86400,
  "version": "1.0.0"
}
```

**Response** (503 Service Unavailable):
```json
{
  "status": "degraded",
  "timestamp": "2024-05-01T10:30:00Z",
  "components": {
    "database": "connected",
    "redis": "disconnected",
    "workers": "operational",
    "storage": "operational"
  },
  "issues": ["Redis cache unavailable"]
}
```

---

## Error Handling

### Standard Error Response

All errors follow consistent format:

```json
{
  "status": "error",
  "error": "Error message",
  "details": {
    "field": "Field with error",
    "reason": "Specific validation error"
  },
  "timestamp": "2024-05-01T10:30:00Z"
}
```

### HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | OK | Successful GET/POST |
| 201 | Created | Resource created (POST) |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Invalid input, validation failed |
| 401 | Unauthorized | Missing/invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Action conflicts with current state |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Dependency unavailable |

### Common Error Responses

**401 Unauthorized**:
```json
{
  "status": "error",
  "error": "Unauthorized",
  "details": {
    "reason": "Missing or invalid JWT token"
  }
}
```

**403 Forbidden**:
```json
{
  "status": "error",
  "error": "Forbidden",
  "details": {
    "reason": "User role cannot perform this action"
  }
}
```

**429 Rate Limited**:
```json
{
  "status": "error",
  "error": "Rate limit exceeded",
  "details": {
    "retry_after": 60
  }
}
```

---

## Rate Limiting

**Default Limits**:
- General: 60 requests per minute per IP
- Auth endpoints: 10 requests per minute per IP
- Authenticated users: 100 requests per minute per user

**Rate Limit Headers**:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1640000060
```

**When Rate Limited** (429):
```json
{
  "status": "error",
  "error": "Rate limit exceeded",
  "details": {
    "limit": 60,
    "retry_after_seconds": 35
  }
}
```

---

## Pagination

All list endpoints support pagination:

**Query Parameters**:
```
page: integer >= 1 (default: 1)
per_page: integer 1-500 (default: 50)
```

**Response Structure**:
```json
{
  "data": {
    "items": [...],
    "pagination": {
      "total": 245,
      "page": 1,
      "per_page": 50,
      "pages": 5,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

---

## Filtering & Sorting

**Standard Filter Parameters**:
- `status`: Exact match
- `created_from`: Date range start (ISO 8601)
- `created_to`: Date range end (ISO 8601)
- `department_id`: Exact match (UUID)
- `assigned_to`: Exact match (UUID)

**Standard Sort Parameters**:
- `sort_by`: Field to sort by
- `sort_order`: `asc` or `desc` (default: `desc`)

**Example**:
```bash
GET /documents?status=APPROVED&created_from=2024-04-01&sort_by=created_at&sort_order=desc
```

---

## Interactive Documentation

**Swagger UI**: Available at `/docs`
- Try out endpoints interactively
- See example requests/responses
- View parameter details

**ReDoc**: Available at `/redoc`
- Read-only documentation
- Better for reference

---

**Last Updated**: May 1, 2024
**API Version**: v1
**Status**: Production Ready
