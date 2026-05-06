# Email Configuration Guide

## Overview

The LAOS system supports email notifications for user access requests and approvals. Emails are sent to:
- **Admin**: When a new access request is submitted
- **User**: When their access request is approved or rejected with temporary login credentials

## Configuration

### 1. Enable SMTP in Environment Variables

Update your `.env` file with Gmail SMTP settings:

```env
SMTP_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=wmangesh91@gmail.com
SMTP_PASSWORD=your-app-specific-password
SMTP_FROM_EMAIL=wmangesh91@gmail.com
SMTP_FROM_NAME=LAOS Admin
ADMIN_EMAIL=wmangesh91@gmail.com
FRONTEND_URL=http://localhost:5173
```

### 2. Generate Gmail App Password

Gmail requires an **App-Specific Password** for SMTP access (if 2-factor authentication is enabled):

1. **Enable 2-Step Verification** (if not already enabled):
   - Go to [Google Account Security](https://myaccount.google.com/security)
   - Click "2-Step Verification" and follow setup

2. **Generate App Password**:
   - Go to [Google Account Settings](https://myaccount.google.com/apppasswords)
   - Select "Mail" as the app
   - Select "Windows Computer" (or your OS)
   - Google will generate a **16-character password**
   - Copy this password to `.env` as `SMTP_PASSWORD`

### 3. Test Email Configuration

Once configured, the system will automatically send emails when:

#### When User Submits Access Request
1. User fills signup form with email & name
2. **Admin receives notification email** with request details
3. User sees success message

#### When Admin Approves Request
1. Admin approves request via `/admin/access-requests/{id}/approve`
2. System creates user account with temporary password
3. **User receives approval email** with login credentials:
   - Email
   - Temporary Password
   - Link to login page

#### When Admin Rejects Request
1. Admin rejects request via `/admin/access-requests/{id}/reject`
2. **User receives rejection email** with reason

## Email Endpoints

### Admin: List Access Requests
```bash
GET /admin/access-requests?status=PENDING
```

### Admin: Approve Access Request
```bash
POST /admin/access-requests/{request_id}/approve
Content-Type: application/json

{
  "department_id": "uuid-of-department"
}
```

**Response**:
```json
{
  "message": "User account created for John Doe",
  "user_id": "uuid",
  "temporary_password": "GeneratedTemp@Pass123"
}
```

### Admin: Reject Access Request
```bash
POST /admin/access-requests/{request_id}/reject
Content-Type: application/json

{
  "reason": "Department not verified"
}
```

## Testing Email (Mock Mode)

For **local development** without real email, keep `SMTP_ENABLED=false`:
- All emails are printed to console
- No actual emails sent
- Useful for testing

**Console output example**:
```
[EMAIL MOCK] To: officer@gov.in, Subject: Your LAOS Account Has Been Created
Body:
Dear Officer Name,
Your access request has been approved...
```

## Troubleshooting

### Gmail Login Failed
- ✅ Verify app password is generated correctly
- ✅ Verify email and password in `.env` are correct
- ✅ Check that 2-Step Verification is enabled
- ❌ Regular Gmail password won't work with SMTP

### Email Not Sending
- ✅ Check `SMTP_ENABLED=true` in `.env`
- ✅ Verify network connection and firewall allows SMTP (port 587)
- ✅ Check backend logs for error messages
- ✅ Verify Gmail app-specific password is correct

### Port Issues
- If port 587 blocked by firewall, try:
  - `SMTP_PORT=465` (SSL)
  - Or configure firewall to allow 587

## Email Templates

### User Access Notification (Admin)
Subject: "New Access Request: {Officer Name}"

### Approval Email (User)
Subject: "Your LAOS Account Has Been Created"
- Contains: Email, temporary password, login link
- Warns user to change password on first login

### Rejection Email (User)
Subject: "Your LAOS Access Request - Unable to Approve"
- Contains: Rejection reason
- Link to contact admin

## Production Considerations

For production deployments:

1. **Use environment-specific config**:
   ```env
   ENVIRONMENT=production
   SMTP_ENABLED=true
   FRONTEND_URL=https://laos.yourdomain.com
   ADMIN_EMAIL=admin@yourdomain.com
   ```

2. **Monitor email delivery**:
   - Check Gmail's "Security" logs
   - Monitor application logs for email failures
   - Implement retry logic for failed emails (future enhancement)

3. **Security best practices**:
   - Never commit `.env` file to git
   - Use secure password storage
   - Rotate app-specific passwords regularly
   - Monitor admin email account for suspicious activity

## Next Steps

1. Set up Gmail app-specific password
2. Update `.env` with email configuration
3. Restart backend service
4. Test with access request workflow
5. Verify emails arrive correctly
