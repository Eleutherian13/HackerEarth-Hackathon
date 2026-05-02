# Quick Integration Guide - PDF Ingestion System

## 1. Backend Setup

### Step 1: Install Dependencies
```bash
cd backend
pip install pymupdf boto3  # Optional: PyMuPDF for enhanced validation, boto3 for S3
```

### Step 2: Configure Environment (`.env`)
```bash
# Storage backend selection
STORAGE_BACKEND=local  # or 's3'

# Local storage
LOCAL_STORAGE_PATH=./storage

# S3 storage (if using S3)
S3_BUCKET_NAME=my-court-documents-bucket
S3_ENDPOINT_URL=  # Leave empty for AWS S3, set for S3-compatible services
```

### Step 3: Register Endpoint in `main.py`
```python
from app.api.v1.endpoints import documents

# In your router setup:
app.include_router(documents.router, prefix="/api/v1")
```

### Step 4: Run Database Migration (if needed)
```bash
# Document model should already exist, but ensure:
alembic upgrade head
```

### Step 5: Start Backend
```bash
uvicorn app.main:app --reload
```

## 2. Frontend Setup

### Step 1: Install Frontend Dependencies
```bash
cd frontend
npm install  # Should already have @mui/material, @mui/icons-material, react-router-dom
```

### Step 2: Register Routes in `App.tsx` or routing config
```typescript
import Upload from './pages/Upload';
import DocumentStatus from './pages/DocumentStatus';

export const Routes = [
  {
    path: '/upload',
    element: <Upload />,
    label: 'Upload Document'
  },
  {
    path: '/documents/:id/status',
    element: <DocumentStatus />
  }
];
```

### Step 3: Update Navigation (e.g., header or sidebar)
```typescript
import { Link } from 'react-router-dom';

<Link to="/upload">Upload Court Judgment</Link>
```

### Step 4: Create Status Page (for after upload)
```typescript
// frontend/src/pages/DocumentStatus.tsx
import { useParams } from 'react-router-dom';

export default function DocumentStatus() {
  const { id } = useParams<{ id: string }>();
  // Fetch /api/v1/documents/{id}/status
  // Show processing progress
}
```

### Step 5: Run Frontend
```bash
npm start
```

## 3. Test the Integration

### Test 1: Upload Valid PDF
```bash
# Create a test PDF or use an existing one
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@sample.pdf" \
  -F 'metadata_json={"case_ref":"TEST-2024-001"}' \
  http://localhost:3000/api/v1/documents/upload
```

**Expected Response (202 Accepted):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "original_filename": "sample.pdf",
  "page_count": 15,
  "processing_status": "UPLOADED",
  "storage_path": "documents/550e8400.../sample.pdf"
}
```

### Test 2: Duplicate Upload
Upload the same file twice without `?force=true`

**Expected Response (409 Conflict):**
```json
{
  "detail": "Document with this file hash already exists",
  "document_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Test 3: Invalid PDF
Upload a non-PDF file with .pdf extension

**Expected Response (400 Bad Request):**
```json
{
  "detail": "File does not have valid PDF magic bytes"
}
```

### Test 4: UI Upload Flow
1. Navigate to `http://localhost:3000/upload`
2. Drag PDF onto drop zone (or click to browse)
3. Fill optional metadata fields
4. Click "Upload Document"
5. See progress bar
6. See success message with document ID
7. Click "View Processing Status" to check status

## 4. Storage Backend Differences

### Local Storage
- **Use for:** Development, testing, single-server setup
- **Files stored:** `./storage/documents/{uuid}/{filename}`
- **Pros:** Simple, no external dependencies, good for testing
- **Cons:** Single server only, no redundancy
- **Setup:** Create writeable `./storage` directory

```bash
mkdir -p storage
chmod 755 storage
```

### S3 Storage
- **Use for:** Production, multi-server, cloud deployment
- **Files stored:** `s3://bucket-name/documents/{uuid}/{filename}`
- **Pros:** Scalable, distributed, built-in redundancy, cost-effective
- **Cons:** Requires AWS account, boto3 dependency
- **Setup:** Configure AWS credentials and S3 bucket

```bash
# Configure AWS credentials
aws configure
# Or set environment variables:
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
```

## 5. Common Customizations

### Change Max Upload Size
In `upload_handler.py`:
```python
MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100MB instead of 50MB
```

And in `DropZone.tsx`:
```typescript
const MAX_FILE_SIZE_MB = 100;
```

### Add Custom Metadata Fields
In `Upload.tsx`:
```typescript
// Add fields for your metadata
<input
  placeholder="Judge Name"
  value={metadata.judge_name || ''}
  onChange={(e) => handleMetadataChange('judge_name', e.target.value)}
/>
```

### Change Drop Zone Appearance
In `DropZone.tsx`:
```typescript
// Customize colors, icons, text, etc.
<Avatar
  sx={{
    backgroundColor: 'success.light',  // Change color
    color: 'success.main',
  }}
>
  <DescriptionIcon />  {/* Use different icon */}
</Avatar>
```

### Handle Upload Success Differently
In `Upload.tsx`:
```typescript
const handleViewStatus = () => {
  if (uploadedDocument) {
    // Instead of navigating:
    // - Call webhook
    // - Trigger email notification
    // - Update parent component state
    navigate(`/documents/${uploadedDocument.id}`);
  }
};
```

## 6. Debugging Common Issues

### Issue: 401 Unauthorized on Upload
**Cause:** Authentication token missing or expired
**Fix:** 
- Check Authorization header is being sent
- Verify token is valid
- Re-authenticate user

### Issue: 403 Forbidden
**Cause:** User doesn't have permission to upload
**Fix:**
- Check user role/permissions
- Verify authentication middleware
- Check request headers

### Issue: 409 Conflict (duplicate)
**Cause:** Same file uploaded twice
**Fix:**
- This is expected behavior (prevents duplicates)
- To reprocess: Use `?force=true` parameter
- Or delete existing document first

### Issue: Storage Path Not Found
**Cause:** Storage backend misconfiguration
**Fix:**
- **Local:** Create `./storage` directory with write permissions
- **S3:** Check S3_BUCKET_NAME and AWS credentials
- Check logs for specific storage errors

### Issue: PDF Validation Fails on Valid PDF
**Cause:** PDF has special structure or is scanned image
**Fix:**
- Ensure PDF is valid and not corrupted
- Try opening in Adobe Reader
- For scanned PDFs, OCR may help (separate pipeline)
- Check PyMuPDF/fitz is installed for enhanced validation

## 7. Performance Optimization

### For Large Files
1. Increase server timeouts (nginx, FastAPI)
2. Consider chunked upload (future feature)
3. Use S3 multipart upload (boto3 handles automatically)

### For High Volume
1. Use connection pooling (database)
2. Queue uploads (Celery)
3. Use S3 for storage (scales automatically)
4. Add CDN for presigned URLs

### For Better UX
1. Show real-time progress (already implemented)
2. Allow parallel uploads (extend Upload component)
3. Queue upload jobs (add upload queue)
4. Provide upload history (add DocumentHistory component)

## 8. Monitoring & Logging

### Check Upload Logs
```bash
# Backend logs show:
# - Every upload attempt
# - File size, hash, page count
# - Validation errors
# - Storage operations
# - User info (IP, user-agent, user ID)

tail -f logs/app.log | grep upload
```

### Monitor Database
```sql
-- Check document uploads
SELECT id, original_filename, page_count, created_at
FROM documents
ORDER BY created_at DESC
LIMIT 10;

-- Check for duplicates
SELECT file_hash, COUNT(*) as count
FROM documents
WHERE deleted_at IS NULL
GROUP BY file_hash
HAVING COUNT(*) > 1;
```

### Check Storage
```bash
# Local storage
ls -la storage/documents/

# S3 storage
aws s3 ls s3://bucket-name/documents/ --recursive
```

## 9. Next Steps

After integration:

1. ✅ Test upload flow (as shown in Test the Integration)
2. ✅ Set up monitoring and logging
3. Implement Document Status page
4. Set up classification background job
5. Implement OCR pipeline
6. Create document search/listing
7. Add document viewer
8. Set up audit trail UI
9. Implement document sharing

## 10. Support & Troubleshooting

For detailed troubleshooting, see `PDF_INGESTION_SUMMARY.md`

Key files:
- Backend: `app/services/ingestion/` and `app/api/v1/endpoints/documents.py`
- Frontend: `src/pages/Upload.tsx` and `src/components/Upload/`
- Config: `.env` and database models

Questions or issues? Check:
1. Error messages in logs
2. Network tab in browser DevTools
3. API response headers and body
4. Database for document record
5. Storage for file existence
