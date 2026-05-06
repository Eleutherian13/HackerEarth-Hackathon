# Complete Access Request Workflow Testing Guide

## Overview

This guide walks through testing the complete user access request and approval workflow, from sign-up through email notifications.

## Prerequisites

1. **Backend running** on `http://localhost:8000`
2. **Frontend running** on `http://localhost:5173`
3. **Database migrations applied** (see instructions below)
4. **Email configured** (see [EMAIL_CONFIGURATION.md](EMAIL_CONFIGURATION.md))

## Step 1: Apply Database Migration

Before testing, run the Alembic migration to create the `access_requests` table:

```bash
cd backend
alembic upgrade head
```

**Or if using container**:
```bash
docker-compose exec backend alembic upgrade head
```

## Step 2: Test Access Request Submission

### Via Frontend UI

1. Open browser to `http://localhost:5173`
2. Look for "Request Officer Access" or "Sign Up" link
3. Fill form:
   - Full Name: `John Officer`
   - Email: `john@example.com`
4. Submit form
5. Should see success message: "Request Submitted Successfully"

### Via API (Manual Testing)

```bash
curl -X POST http://localhost:8000/api/v1/auth/request-access \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "full_name": "John Officer"
  }'
```

**Success Response**:
```json
{
  "message": "Access request submitted successfully. An administrator will review and create your account."
}
```

### What Happens

1. ✅ Access request stored in `access_requests` table with `PENDING` status
2. ✅ Notification email sent to admin (if `SMTP_ENABLED=true`)
3. ✅ Frontend shows success message
4. ✅ User sees "An administrator will review..."

## Step 3: Admin Reviews Pending Requests

### List All Pending Requests

```bash
curl -X GET http://localhost:8000/admin/access-requests?status=PENDING \
  -H "Authorization: Bearer {ADMIN_JWT_TOKEN}"
```

**Response**:
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "john@example.com",
      "full_name": "John Officer",
      "status": "PENDING",
      "created_at": "2024-01-15T10:30:00Z",
      "reviewed_at": null
    }
  ],
  "total": 1
}
```

## Step 4: Admin Approves Request

### Approve Access Request

```bash
curl -X POST http://localhost:8000/admin/access-requests/550e8400-e29b-41d4-a716-446655440000/approve \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {ADMIN_JWT_TOKEN}" \
  -d '{
    "department_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
  }'
```

**Response**:
```json
{
  "message": "User account created for John Officer",
  "user_id": "660e8400-e29b-41d4-a716-446655440111",
  "temporary_password": "Tr0pical#Mango42!"
}
```

### What Happens

1. ✅ New user created in `users` table
   - Email: `john@example.com`
   - Full Name: `John Officer`
   - Role: `OFFICER`
   - Status: `is_active=true`
   - `must_change_password=true` (forces password change)

2. ✅ Access request updated
   - Status changed to `APPROVED`
   - `reviewed_by_admin_id` set to admin's user ID
   - `reviewed_at` set to current timestamp

3. ✅ Approval email sent to user with:
   - Email: john@example.com
   - Temporary password: Tr0pical#Mango42!
   - Login link: http://localhost:5173/login

4. ✅ Admin notification shows temporary password (for their records)

## Step 5: User Logs In with Temporary Password

### Login with Temporary Credentials

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d 'username=john@example.com&password=Tr0pical%23Mango42%21'
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "660e8400-e29b-41d4-a716-446655440111",
    "email": "john@example.com",
    "full_name": "John Officer",
    "role": "OFFICER",
    "must_change_password": true
  }
}
```

### What Happens

- ✅ User authenticated successfully
- ✅ `must_change_password: true` indicates password change required
- ✅ Frontend should prompt for password change on first login

## Step 6: User Changes Password (First Login)

```bash
curl -X POST http://localhost:8000/api/v1/auth/change-password \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {USER_JWT_TOKEN}" \
  -d '{
    "current_password": "Tr0pical#Mango42!",
    "new_password": "MyNewSecurePassword@123",
    "new_password_confirm": "MyNewSecurePassword@123"
  }'
```

**Response**:
```json
{
  "message": "Password changed successfully. Please log in again with your new password."
}
```

### What Happens

- ✅ Old password verified
- ✅ New password validated for strength
- ✅ `must_change_password` set to `false`
- ✅ User can now use new password for logins

## Step 7: Reject Access Request (Alternative)

### Reject a Pending Request

```bash
curl -X POST http://localhost:8000/admin/access-requests/550e8400-e29b-41d4-a716-446655440000/reject \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {ADMIN_JWT_TOKEN}" \
  -d '{
    "reason": "Department verification pending"
  }'
```

**Response**:
```json
{
  "message": "Access request from John Officer has been rejected"
}
```

### What Happens

1. ✅ Access request status changed to `REJECTED`
2. ✅ Rejection reason stored in `decision_reason`
3. ✅ Rejection email sent to user:
   - Subject: "Your LAOS Access Request - Unable to Approve"
   - Body: Includes rejection reason
   - Contact information for resubmission

## Testing with Mock Email (No Real Email)

For development without actual email sending:

1. Keep `SMTP_ENABLED=false` in `.env`
2. Emails will print to backend console instead
3. Example console output:

```
[EMAIL MOCK] To: admin@example.com, Subject: New Access Request: John Officer
Body:
A new officer has requested access to LAOS.

Name: John Officer
Email: john@example.com
---

[EMAIL MOCK] To: john@example.com, Subject: Your LAOS Account Has Been Created
Body:
Dear John Officer,

Your access request has been approved, and your account has been created.

Login Credentials:
Email: john@example.com
Temporary Password: Tr0pical#Mango42!
...
```

## Getting Admin JWT Token

To make authenticated requests to admin endpoints, you need an admin JWT token:

1. **Create admin user** (if not exists):
```bash
cd backend
python create_test_user_simple.py  # Or use admin creation script
```

2. **Login as admin**:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d 'username=admin@example.com&password={admin_password}'
```

3. **Extract** `access_token` from response
4. **Use** in requests:
```bash
curl -X GET http://localhost:8000/admin/access-requests \
  -H "Authorization: Bearer {access_token}"
```

## Database Verification

After completing workflow, verify data in database:

### Check Access Requests

```sql
SELECT id, email, full_name, status, reviewed_at 
FROM access_requests 
ORDER BY created_at DESC;
```

### Check Users Created

```sql
SELECT id, email, full_name, role, is_active, must_change_password
FROM users 
WHERE email = 'john@example.com';
```

### Check Audit Logs

```sql
SELECT event_type, action, changes, created_at
FROM audit_logs
WHERE entity_type = 'User'
ORDER BY created_at DESC;
```

## Troubleshooting

### "Access request not found"
- ✅ Verify request_id is correct UUID
- ✅ Check request exists in database: `SELECT * FROM access_requests WHERE id = 'xxx'`

### "Cannot approve a request with status PENDING"
- ❌ This should not happen - indicates DB corruption
- ✅ Check access_request status in DB

### "Department not found"
- ✅ Verify department_id exists: `SELECT id FROM departments LIMIT 5`
- ✅ Use valid department UUID from database

### Email not sending
- ✅ Verify `SMTP_ENABLED=true` in `.env`
- ✅ Check backend logs for error messages
- ✅ Verify Gmail app-specific password is correct
- ✅ Check internet connection

### "Must provide JWT token"
- ✅ Ensure token is in Authorization header
- ✅ Format: `Authorization: Bearer {token}`
- ✅ Token must be from admin or user with role ADMIN

## Success Criteria

✅ Access request workflow is complete when:

1. User submits access request via frontend
2. Admin receives notification email
3. Admin sees request in `/admin/access-requests` list
4. Admin approves request with valid department
5. User receives approval email with temporary password
6. User can login with temporary password
7. User can change password
8. User can access system as OFFICER role

## Next Steps

Once workflow is working:
1. Set up email notifications in production environment
2. Implement admin dashboard UI for access requests
3. Add request expiration (auto-reject after N days)
4. Add bulk approval/rejection features
5. Implement audit logging for approvals/rejections
