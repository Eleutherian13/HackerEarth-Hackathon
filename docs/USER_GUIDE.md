# User Guide

Complete instructions for using LAOS across all user roles (Reviewers, Officers, Administrators).

## Getting Started

### Login
1. Navigate to your instance: `https://yourdomain.com`
2. Enter email and password
3. Click "Login"
4. If "Remember me" is checked, you stay logged in for 7 days
5. System auto-logs you out after 30 minutes of inactivity

### Dashboard Overview
After login, you see the main dashboard with:
- **Quick Stats**: Total documents, pending actions, completion rate
- **Recent Activity**: Latest documents and actions
- **Your Assignments**: Documents/actions assigned to you
- **Department Performance**: Your department's metrics

### Navigation Menu
- **Judgments**: Browse all documents (Reviewer/Admin only)
- **Action Plans**: View assigned actions
- **Reports**: Analytics and compliance metrics
- **Users**: Manage team (Admin only)
- **Settings**: Personal settings and preferences
- **Help**: Documentation and support

---

## For Reviewers

Reviewers verify that extracted information is accurate before it's used for compliance planning.

### Main Task: Review Documents

#### 1. Access Documents Awaiting Review

**Step 1: Open Judgments Tab**
- Click "Judgments" in main menu
- Filter by Status: "Pending Review"
- System shows documents in order of upload

**Step 2: Select Document to Review**
- Click on document title to open review panel
- See:
  - Original PDF (left side)
  - Extracted fields (right side)
  - Confidence scores per field
  - Reviewer comments section

#### 2. Understand Confidence Scores

Each field shows a confidence indicator:

| Color | Score | Meaning | Action |
|-------|-------|---------|--------|
| 🟢 Green | 0.85+ | High confidence | Trust the extraction, minimal review needed |
| 🟡 Yellow | 0.60-0.85 | Medium confidence | Review carefully, may need correction |
| 🔴 Red | <0.60 | Low confidence | Manual verification required, likely needs correction |

#### 3. Review and Correct Fields

For each field:

**Green fields (High confidence):**
- Scan the original document to verify
- If correct, leave as-is
- If incorrect, edit and mark as "Corrected"

**Yellow/Red fields (Needs verification):**
- Carefully check against original document
- Click field to edit inline
- Common corrections:
  - Spelling/OCR errors
  - Date format standardization
  - Missing information
  - Extra information to remove

**Example corrections:**
```
BEFORE: "2024-12-31 (this date)"
AFTER: "2024-12-31"

BEFORE: "Misspelled: Shivraj"
AFTER: "Shivaraj" (correct spelling)

BEFORE: "Justice of the High Court of Madhya Pradesh"
AFTER: "High Court of Madhya Pradesh"
```

#### 4. Make Corrections

**To edit a field:**
1. Click on the field value
2. Edit inline in the text box
3. Click "Save" or press Enter
4. Field updates immediately

**For multiline fields (e.g., directions):**
1. Click "Edit" button
2. Use rich text editor
3. Format as needed
4. Click "Save"

#### 5. Add Comments

For fields requiring explanation:
1. Click "Add Comment" below field
2. Explain your correction:
   - Why you changed it
   - Which source document you referenced
   - Any ambiguities you resolved
3. Click "Post"

**Good comment example:**
```
"Changed 'High Court of Madhya Pradesh' to correct 'court_name' field.
The judgment header clearly states 'High Court of Madhya Pradesh, Indore
Bench'. Removed the bench name as it's stored separately in bench_name field."
```

#### 6. Approve or Reject

**Approving document:**
1. Review all corrections made
2. Verify against original PDF
3. Click "Approve Document"
4. Add summary (optional): "All fields verified and corrected"
5. Confirm approval

Document now moves to "Action Planning" stage.

**Rejecting document:**
1. Click "Reject Document"
2. Select reason:
   - Extraction quality too low
   - Document not readable
   - Document not a valid judgment
   - Other (specify)
3. Add detailed feedback
4. Click "Reject"

Document returned to "Uploaded" stage for re-extraction.

### Review Tips

**Speed up review:**
- Use keyboard shortcuts: Tab to next field, Shift+Tab to previous
- Use "Auto-review High Confidence": System pre-approves green fields
- Focus on red/yellow fields first
- Use filter to show only fields needing review

**Accuracy:**
- Always check original PDF
- Use Find (Ctrl+F) to search for values in PDF
- Be consistent (spelling, capitalization, date format)
- Check surrounding context for ambiguous terms

**When you're unsure:**
- Add detailed comment explaining your uncertainty
- Mark as "Needs clarification" (not approval/rejection)
- Document escalates to senior reviewer
- Senior reviewer resolves and finalizes

---

## For Officers

Officers track and complete compliance action items assigned to their department.

### Main Task: Complete Action Items

#### 1. View Your Assignments

**Step 1: Open Action Plans**
- Click "Action Plans" in main menu
- Filter by Status: "Assigned to me"
- System shows deadline urgency:
  - 🔴 Red: Due within 7 days
  - 🟡 Yellow: Due within 30 days
  - 🟢 Green: Due after 30 days

**Step 2: Select Action Item**
- Click on action title
- See:
  - Related judgment (link to original)
  - Detailed directions from court
  - Deadline (date)
  - Required evidence/verification
  - Progress status
  - Comments from reviewers

#### 2. Understand Action Item Status

| Status | Meaning | Your Action |
|--------|---------|------------|
| Assigned | New action, not yet started | Read details, start work |
| In Progress | Work started, deadline approaching | Update progress, gather evidence |
| Pending Verification | Work complete, needs evidence | Upload supporting documents |
| Completed | Court requirement fulfilled | System marks as done |
| Overdue | Missed deadline | Contact supervisor immediately |

#### 3. Update Progress

**To mark as "In Progress":**
1. Click "Start Working" button
2. System records start date/time
3. Status changes to "In Progress"
4. Deadline appears in red if approaching

**To add progress updates:**
1. Click "Add Update"
2. Describe work done:
   - Steps completed
   - Challenges faced
   - Next steps planned
   - Estimated completion date
3. Click "Post"

**Example update:**
```
"Met with Revenue Department on April 25.
Collected property documents showing corrected assessment.
Prepared response letter for court.
Plan to submit to District Court by May 5.
Waiting for Finance approval on refund amount."
```

#### 4. Mark as Complete (with Evidence)

**Before marking complete, gather:**
- Official documents showing compliance
- Timestamps/photographs
- Approval from higher authority
- Payment receipts (if monetary)
- Correspondence with other departments

**To submit completion:**
1. Click "Submit Completion"
2. Select evidence type:
   - Official Letter
   - Compliance Certificate
   - Payment Receipt
   - Implementation Report
   - Photograph
   - Other
3. Upload document(s):
   - Click "Upload" or drag-and-drop
   - Add description: "What does this document show?"
   - Attach multiple files if needed
4. Add completion summary:
   - How requirement was fulfilled
   - Any deviations or challenges
   - Other stakeholders involved
5. Click "Submit for Review"

Action moves to "Pending Verification" stage.

**Verification process:**
- Reviewer examines your evidence
- Within 3-5 days, either approves or asks for more info
- If rejected, you can resubmit with additional evidence
- Once approved, system marks action as "Completed"

#### 5. Handle Overdue Actions

If deadline is approaching or past:

1. Click action item
2. Look for "Overdue Alert"
3. Click "Request Extension" if needed:
   - Explain why more time needed
   - Propose new deadline
   - Add supporting documentation
   - Requires supervisor approval
4. Or accelerate completion:
   - Click "Expedite"
   - Gather remaining evidence quickly
   - Submit within 24-48 hours

### Action Plan Examples

#### Example 1: Fine Payment Action
```
Court Direction: "Government shall pay ₹5,00,000 fine within 30 days"

Your Steps:
1. Get approval from Finance Department (Week 1)
2. Prepare payment voucher (Week 1-2)
3. Transfer money from budget (Week 2-3)
4. Get bank receipt/confirmation (Week 3)
5. Submit receipt as evidence (Week 3)

Evidence to Upload:
- Budget sanction letter
- Payment voucher
- Bank transfer confirmation
- Acknowledgment receipt from treasury
```

#### Example 2: Implementation Action
```
Court Direction: "Implement pollution control measures by March 31"

Your Steps:
1. Survey site, assess requirements (Week 1)
2. Procure equipment (Week 2-4)
3. Install and test (Week 4-6)
4. Get environmental certification (Week 6-8)
5. Submit certification as evidence (Week 8)

Evidence to Upload:
- Project proposal
- Purchase orders
- Installation photos
- Test certificates
- Environmental audit report
```

#### Example 3: Administrative Action
```
Court Direction: "Issue revised guidelines by February 28"

Your Steps:
1. Form committee, set meeting schedule (Week 1)
2. Draft new guidelines (Week 2-3)
3. Internal consultations (Week 3-4)
4. Publish guidelines (Week 4)
5. Submit published document as evidence (Week 4)

Evidence to Upload:
- Committee meeting minutes
- Draft guidelines with approval marks
- Published notification
- Dissemination memo to departments
```

---

## For Administrators

Administrators manage system configuration, users, and department settings.

### User Management

#### Create New User

**Step 1: Navigate to Users**
- Click "Users" in main menu
- Click "Add New User"

**Step 2: Enter User Details**
- Email: user@department.gov.in
- Full Name: As per official records
- Department: Select from dropdown
- Role: Choose from list

**Available Roles:**
- **ADMIN**: Full system access, manage users
- **REVIEWER**: Review documents, approve extractions
- **OFFICER**: Complete action items, track progress

**Step 3: Set Permissions**
- Department-specific permissions
- Document access scope
- Report access level

**Step 4: Send Invitation**
- System sends invitation email
- User clicks link, sets password
- User activates account
- Can login immediately

#### Manage User Passwords

**First-time password reset:**
1. Click user in User list
2. Click "Reset Password"
3. System generates temporary password
4. User receives email with link
5. User sets permanent password on first login

**For forgotten passwords:**
- Users click "Forgot Password" on login page
- Receive email reset link
- Set new password
- Can login with new password

#### Deactivate User

**When user leaves:**
1. Click user in User list
2. Click "Deactivate"
3. Confirm deactivation
4. User can no longer login
5. Their records remain for audit trail

### Department Management

#### Add Department

**Step 1: Navigate to Departments**
- Click "Settings" → "Departments"
- Click "Add Department"

**Step 2: Configure Department**
- Name: Official department name
- Code: Short code (e.g., "RV" for Revenue)
- Budget: Allocate annual budget
- Contact Person: Primary contact for department
- Email: Department email

**Step 3: Assign Users**
- Select officers who belong to this department
- System tracks their action items by department
- Reports grouped by department

#### Configure Department Permissions

**Document access:**
- Can upload documents for this department
- Can review their own department's actions
- Can access reports for department

**Budget allocation:**
- Set department budget
- Track spending against budget
- Generate budget utilization reports

### System Configuration

#### Configure Extraction Settings

**In Settings → Extraction:**

- **MIN_CONFIDENCE_THRESHOLD**: Minimum score (0.60)
  - Fields below this flagged for manual review
  - Recommended: 0.60 for strict review, 0.50 for lenient
  
- **HIGH_CONFIDENCE_THRESHOLD**: Above this (0.85)
  - Green flag - can be auto-approved
  - Recommended: 0.85 for high accuracy
  
- **MAX_PDF_SIZE_MB**: Limit document size (50 MB)
  - Larger PDFs take longer to process
  - Recommended: 50-100 MB
  
- **EXTRACT_OCR_ENABLED**: Use OCR for scanned PDFs
  - Slower but higher accuracy on scanned documents
  - Recommended: Enabled

#### Configure Deadline Settings

**In Settings → Deadlines:**

- **ACTION_REVIEW_TIMEOUT**: Days for initial review (3)
  - How long reviewer has to review extraction
  
- **ACTION_SUBMISSION_TIMEOUT**: Days for completion (90)
  - How long officer has to complete action
  
- **COMPLETION_REVIEW_TIMEOUT**: Days for verification (5)
  - How long reviewer has to verify completion

#### Configure Email Notifications

**In Settings → Notifications:**

Enable/disable email alerts for:
- ✓ Document ready for review
- ✓ Document rejected, needs re-extraction
- ✓ Action assigned to me
- ✓ Action deadline approaching
- ✓ Action overdue
- ✓ Completion submitted for verification
- ✓ Completion verified, action complete

### Reports & Analytics

#### Dashboard Metrics

**Overview section shows:**
- Total judgments processed
- Documents pending review
- Action items pending completion
- Overall compliance rate

**Department Performance:**
- Documents reviewed per department
- Average review time
- Action completion rate
- Budget utilization

#### Generate Reports

**Compliance Report:**
- Date range: Select custom dates
- Departments: Filter by specific departments
- Metrics:
  - Total judgments received
  - Documents approved/rejected
  - Actions completed vs. pending
  - Average completion time
  - Compliance rate percentage

**Example:** "For Q1 2024, Revenue Department:
- Received 45 judgments
- Approved 42 (93%)
- Generated 87 action items
- Completed 78 (90%)
- Average completion: 45 days
- Compliance rate: 90%"

**Budget Report:**
- Track department spending
- Compare vs. allocated budget
- Identify over/under-budget departments
- Export for finance reconciliation

#### Export Data

**Available exports:**
- Document list (Excel, CSV)
- Action items (Excel, CSV)
- User activity (Excel, CSV)
- Audit logs (for compliance)

**To export:**
1. Navigate to any list view
2. Click "Export"
3. Select format (Excel, CSV)
4. Click "Download"
5. File downloads to your computer

### Audit & Compliance

#### View Audit Log

**In Reports → Audit Log:**

See every action in system:
- User who performed action
- Action type (view, edit, approve)
- Document/user affected
- Timestamp
- Changes made (before/after)

**Example audit trail:**
```
04-May-2024 14:30:22 | reviewer1 | APPROVED | Judgment #245 | "All fields verified"
04-May-2024 14:25:15 | reviewer1 | EDITED | Case_Number field | "2024-RC-456" → "2024-RC-457"
04-May-2024 14:20:00 | reviewer1 | VIEWED | Judgment #245 | 8 minutes viewing time
```

**Filter audit log by:**
- Date range
- User
- Action type
- Document
- Department

### User Activity Monitoring

**Track user engagement:**
- Last login time
- Documents reviewed by user
- Actions completed by user
- Time spent per document
- Comments/corrections made

**To view:**
1. Click "Users"
2. Click user name
3. See "Activity Summary" tab
4. Shows all their actions with timestamps

### System Health Monitoring

**In Settings → System Health:**

View:
- 🟢 Database: Connected, response time
- 🟢 Redis: Connected, memory used
- 🟢 Workers: Running count, queue depth
- 🟢 Storage: Free disk space, upload folder size
- 🟢 API: Response time, error rate

**Alerts if any are red:**
- Check immediately
- Restart service if needed
- Contact DevOps if persists

---

## Keyboard Shortcuts

For faster navigation:

| Shortcut | Action |
|----------|--------|
| `?` | Show help panel |
| `j` | Jump to next document |
| `k` | Jump to previous document |
| `e` | Edit current field |
| `a` | Approve document |
| `r` | Reject document |
| `Ctrl+S` | Save changes |
| `/` | Focus search |
| `Esc` | Close dialog |
| `Tab` | Next field |
| `Shift+Tab` | Previous field |

---

## Troubleshooting

### "Cannot view document PDF"
- Check PDF file is not corrupted
- Try downloading PDF to your computer
- If still blank, contact support

### "Extraction looks wrong"
- Verify with original document
- Scanned PDFs may have OCR errors
- Correct the fields and approve
- System learns from corrections

### "Forgot my password"
- Click "Forgot Password" on login screen
- Check email for reset link
- Click link and create new password
- If email not received, contact admin

### "Deadline has passed"
- Click "Request Extension"
- Explain why more time needed
- Supervisor receives approval request
- If approved, new deadline is set
- If not approved, escalate to department head

### "Cannot upload document"
- Check file size < 50 MB
- Ensure file is PDF format (.pdf)
- Try different browser
- Contact support if still fails

### "System is slow"
- Check internet connection
- Try refreshing page (Ctrl+R)
- Close other browser tabs
- Try again in 5 minutes
- If still slow, contact support

---

## Frequently Asked Questions

**Q: How long does extraction take?**
A: 2-30 seconds depending on PDF size and quality. Scanned PDFs take longer.

**Q: Can I edit a document after approving it?**
A: No, approved documents are locked. Submit rejection if changes needed.

**Q: How long is my login session?**
A: 30 minutes of inactivity, then auto-logout. Check "Remember me" for 7-day persistence.

**Q: What if my correction is wrong?**
A: Admins can see all changes in audit log. Acknowledge in next document.

**Q: Can I print documents?**
A: Click PDF → Print button. Works in all browsers.

**Q: How do I export action items?**
A: In Action Plans list, click "Export to Excel". Downloads immediately.

**Q: What's the difference between actions and directions?**
A: Directions are what the court ordered. Actions are compliance steps your department must take.

---

## Getting Help

- **In-app Help**: Click `?` on any page
- **Documentation**: See [docs/](docs/) folder
- **API Reference**: Available at `/docs` endpoint
- **Contact Support**: Email support@yourdomain.com
- **Report Bug**: Click "Report Issue" in settings menu

---

**Last Updated**: May 1, 2024
**Version**: 1.0.0
