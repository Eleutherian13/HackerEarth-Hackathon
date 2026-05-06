# Access Request Workflow - Implementation Summary

## What Was Implemented

A complete user access request and approval workflow for LAOS has been implemented with the following components:

### 1. Database Model (`AccessRequest`)

**Location**: `backend/app/models/domain/models.py`

New model created to store access requests with the following fields:
- `id`: UUID primary key
- `email`: Requester's email (unique)
- `full_name`: Requester's full name
- `status`: Request status (PENDING, APPROVED, REJECTED, EXPIRED)
- `decision_reason`: Optional rejection/approval reason
- `reviewed_by_admin_id`: Foreign key to admin user who reviewed
- `reviewed_at`: Timestamp of admin's decision
- `created_at`: Request submission time
- `updated_at`: Last update time

**Indexes**: 
- status + created_at (for efficient filtering)
- email (for uniqueness checking)

### 2. User Access Request Endpoint (Updated)

**Location**: `backend/app/api/v1/endpoints/auth.py`

- **Endpoint**: `POST /api/v1/auth/request-access`
- **Changes**:
  - Now stores access request to database
  - Prevents duplicate pending requests
  - Sends notification email to admin
  - Updated to import `AccessRequest` model and `AccessRequestStatus` enum

### 3. Admin Approval Endpoints

**Location**: `backend/app/api/v1/endpoints/admin.py`

#### List Pending Access Requests
- **Endpoint**: `GET /admin/access-requests?status=PENDING`
- **Authentication**: Admin role required
- **Returns**: List of pending access requests with pagination

#### Approve Access Request
- **Endpoint**: `POST /admin/access-requests/{request_id}/approve`
- **Authentication**: Admin role required
- **Payload**: 
  ```json
  {
    "department_id": "uuid"
  }
  ```
- **Response**:
  ```json
  {
    "message": "User account created...",
    "user_id": "uuid",
    "temporary_password": "Generated@Pass123"
  }
  ```
- **Actions**:
  - Creates new user account
  - Sets `must_change_password=true`
  - Updates access request status to APPROVED
  - Sends approval email to requester
  - Records review timestamp and admin ID

#### Reject Access Request
- **Endpoint**: `POST /admin/access-requests/{request_id}/reject`
- **Authentication**: Admin role required
- **Payload**:
  ```json
  {
    "reason": "Department not verified"
  }
  ```
- **Response**:
  ```json
  {
    "message": "Access request from ... has been rejected"
  }
  ```
- **Actions**:
  - Updates status to REJECTED
  - Stores rejection reason
  - Sends rejection email to requester
  - Records review timestamp and admin ID

### 4. Email Notification Functions

**Location**: `backend/app/core/email.py`

#### 1. `send_access_request_notification()`
- **Recipient**: Admin email
- **Trigger**: When user submits access request
- **Content**: Requester's name and email with action link

#### 2. `send_approval_email()`
- **Recipient**: Requester's email
- **Trigger**: When admin approves request
- **Content**:
  - Email address for login
  - Temporary password
  - Login URL
  - Warning to change password on first login
  - Professional HTML + plain text

#### 3. `send_rejection_email()`
- **Recipient**: Requester's email
- **Trigger**: When admin rejects request
- **Content**:
  - Rejection reason
  - Contact info for questions
  - Professional HTML + plain text

### 5. Configuration Updates

**Location**: `backend/app/core/config.py`

Added new email configuration settings:
```python
ADMIN_EMAIL: str = "admin@example.com"
FRONTEND_URL: str = "http://localhost:5173"
SMTP_ENABLED: bool = False
SMTP_HOST: str = "smtp.gmail.com"
SMTP_PORT: int = 587
SMTP_USER: str = ""
SMTP_PASSWORD: str = ""
SMTP_FROM_EMAIL: str = ""
SMTP_FROM_NAME: str = "LAOS Admin"
```

### 6. Database Migration

**Location**: `backend/alembic/versions/004_add_access_requests_table.py`

Creates:
- `access_requests` table with all required columns
- `access_request_status` enum type
- Indexes for performance
- Foreign key constraint to users table

### 7. Documentation Files

#### EMAIL_CONFIGURATION.md
- Gmail app-specific password setup
- SMTP configuration guide
- Testing email (mock mode)
- Troubleshooting

#### WORKFLOW_TESTING.md
- Step-by-step workflow testing
- API examples with curl
- Database verification queries
- Success criteria

#### .env.example
- Email configuration section added
- Sample values provided

## Workflow Flow

```
┌─────────────────────────────────────────────┐
│ 1. User submits access request via frontend │
└────────────────────┬────────────────────────┘
                     ▼
        POST /api/v1/auth/request-access
                     ▼
    ┌─────────────────────────────────────┐
    │ • Check if email already exists     │
    │ • Check if pending request exists   │
    │ • Create AccessRequest (PENDING)    │
    │ • Send admin notification email     │
    └─────────────────────────────────────┘
                     ▼
    ✓ Request submitted successfully
                     ▼
┌─────────────────────────────────────────────┐
│ 2. Admin logs in and views pending requests │
└────────────────────┬────────────────────────┘
                     ▼
       GET /admin/access-requests?status=PENDING
                     ▼
    Returns list of pending requests
                     ▼
┌────────────────────────────────────────────────────────┐
│         Option A: Admin Approves                       │
├────────────────────────────────────────────────────────┤
│ POST /admin/access-requests/{id}/approve              │
│                                                        │
│ • Create User account with temp password              │
│ • Set must_change_password=true                       │
│ • Update AccessRequest status=APPROVED               │
│ • Send approval email with credentials                │
└─────────────────────┬────────────────────────────────┘
                      ▼
      ✓ User can login with temp password
                      ▼
      User forced to change password
                      ▼
┌─────────────────────────────────────────────┐
│ 3. User logs in as new OFFICER account      │
└─────────────────────────────────────────────┘

Or: Option B: Admin Rejects
    POST /admin/access-requests/{id}/reject
    • Update AccessRequest status=REJECTED
    • Send rejection email with reason
    • User notified via email
```

## Files Modified

1. **backend/app/models/domain/models.py**
   - Added `AccessRequest` model class

2. **backend/app/api/v1/endpoints/auth.py**
   - Updated `request_access()` to store requests in DB
   - Added imports for `AccessRequest` and `AccessRequestStatus`

3. **backend/app/api/v1/endpoints/admin.py**
   - Added list access requests endpoint
   - Added approve access request endpoint
   - Added reject access request endpoint
   - Added schema classes for responses
   - Updated imports

4. **backend/app/core/email.py**
   - Added `send_approval_email()` function
   - Added `send_rejection_email()` function

5. **backend/app/core/config.py**
   - Added email configuration settings

6. **backend/.env.example**
   - Added email configuration section

## Files Created

1. **backend/alembic/versions/004_add_access_requests_table.py**
   - Database migration for access_requests table

2. **backend/docs/EMAIL_CONFIGURATION.md**
   - Email setup guide

3. **backend/docs/WORKFLOW_TESTING.md**
   - Complete testing guide with examples

## Next Steps to Get Running

### 1. Update Environment Variables
```bash
# backend/.env
ADMIN_EMAIL=wmangesh91@gmail.com
SMTP_ENABLED=true
SMTP_USER=wmangesh91@gmail.com
SMTP_PASSWORD=your-16-char-app-password
SMTP_FROM_EMAIL=wmangesh91@gmail.com
FRONTEND_URL=http://localhost:5173
```

### 2. Apply Database Migration
```bash
cd backend
alembic upgrade head
```

### 3. Restart Backend
```bash
# If running manually
python main.py

# If using docker
docker-compose restart backend
```

### 4. Test the Workflow
1. Submit access request from frontend
2. Check admin email (or console if mock mode)
3. Admin approves via API
4. Check user email for credentials
5. User logs in with temporary password
6. User changes password on first login

## Key Features

✅ **Database Persistence**: All access requests stored in DB  
✅ **Workflow Tracking**: Status tracking (PENDING → APPROVED/REJECTED)  
✅ **Admin Review**: Dedicated endpoint to list and manage requests  
✅ **Automatic User Creation**: User account created on approval  
✅ **Secure Temporary Passwords**: 12-character passwords with special chars  
✅ **Email Notifications**: Admin + user notifications  
✅ **Audit Trail**: All decisions recorded with timestamps  
✅ **Error Handling**: Duplicate prevention, validation  
✅ **Mock Email Mode**: Test without real SMTP  
✅ **Professional Templates**: HTML + plain text emails  

## Security Considerations

1. **Password Security**:
   - Temporary passwords are 12 characters with mixed case + symbols
   - Users forced to change on first login
   - Passwords hashed with bcrypt (12 rounds)

2. **Access Control**:
   - Approval endpoints require ADMIN role
   - User data validation on input

3. **Email**:
   - Supports Gmail app-specific passwords
   - SMTP connection uses TLS (port 587)
   - Mock mode for development (no real emails)

4. **Database**:
   - Email field has unique constraint
   - Foreign keys prevent orphaned data
   - Audit fields track who approved/rejected

## Troubleshooting

See [WORKFLOW_TESTING.md](WORKFLOW_TESTING.md#troubleshooting) for detailed troubleshooting guide.

Common issues:
- **"AccessRequest not imported"**: Run migration first
- **"Email not sending"**: Check SMTP settings and network
- **"Cannot create user"**: Verify department_id exists
- **"Access denied"**: Ensure user has ADMIN role
