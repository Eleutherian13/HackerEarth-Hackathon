# Document Status Tracking - Quick Start

## Backend Integration

### 1. Verify Endpoints Are Registered
In `/backend/main.py`, ensure the documents router is registered:
```python
from app.api.v1.endpoints import documents

# In your router setup:
app.include_router(documents.router, prefix="/api/v1")
```

### 2. Test the Endpoints

**Test Status Endpoint:**
```bash
curl -X GET \
  -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/documents/{document_id}/status
```

**Test Listing Endpoint:**
```bash
curl -X GET \
  -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/documents?page=1&page_size=10"
```

## Frontend Integration

### 1. Add Routes
In your main routing file (e.g., `App.tsx`):
```typescript
import DocumentStatus from './pages/DocumentStatus';
import Documents from './pages/Documents';

<Routes>
  {/* ... other routes */}
  <Route path="/documents" element={<Documents />} />
  <Route path="/documents/:id/status" element={<DocumentStatus />} />
</Routes>
```

### 2. Update Upload Redirect
In `Upload.tsx`, after successful upload:
```typescript
const handleViewStatus = () => {
  if (uploadedDocument) {
    navigate(`/documents/${uploadedDocument.id}/status`);
  }
};
```

### 3. Add Navigation
In your header/sidebar navigation:
```typescript
<Link to="/documents">Documents</Link>
<Link to="/upload">Upload Document</Link>
```

### 4. Install Dependencies (if needed)
```bash
cd frontend
npm install date-fns  # For date formatting
```

## Component Tree

```
App
├── Header/Navigation
│   ├── Link to /upload
│   └── Link to /documents
├── /upload → Upload.tsx
│   ├── DropZone
│   ├── UploadProgress
│   └── onClick → /documents/{id}/status
├── /documents → Documents.tsx
│   ├── SearchBar
│   ├── StatusFilter
│   ├── DocumentsTable
│   └── Pagination
└── /documents/:id/status → DocumentStatus.tsx
    ├── Summary Cards
    ├── StatusChip
    ├── Tabs
    │   ├── Processing Jobs
    │   ├── Extracted Fields
    │   ├── Action Plan
    │   └── Timeline
    └── RefreshButton
```

## API Response Handling

### Status Endpoint Response
```typescript
interface DocumentStatusResponse {
  document: {
    id: string;
    filename: string;
    status: 'UPLOADED' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED';
    page_count?: number;
    // ... other fields
  };
  processing_jobs: Array<{
    id: string;
    type: string;
    status: string;
    // ... timestamps, error, etc.
  }>;
  extracted_fields: Array<{
    field_type: string;
    value: string;
    confidence_score: number;
    // ...
  }>;
  action_plan_items: Array<{
    title: string;
    priority: string;
    completion_status: string;
    // ...
  }>;
  summary: {
    total_fields_extracted: number;
    fields_verified: number;
    // ...
  };
}
```

### Listing Endpoint Response
```typescript
interface DocumentsListResponse {
  items: Array<{
    id: string;
    original_filename: string;
    processing_status: string;
    page_count?: number;
    file_size_bytes: number;
    created_at: string;
    updated_at: string;
  }>;
  total: number;
  page: number;
  page_size: number;
}
```

## Common Use Cases

### 1. Upload Document & Track Status
```typescript
// 1. Upload (Upload.tsx)
const response = await fetch('/api/v1/documents/upload', ...);
const doc = await response.json();

// 2. Redirect to status page
navigate(`/documents/${doc.id}/status`);

// 3. DocumentStatus page auto-fetches and refreshes
```

### 2. View All Documents
```typescript
// Navigate to /documents
// Page shows all documents with summary stats
// Click "View" on any document to see status details
```

### 3. Search Documents
```typescript
// In Documents.tsx:
// Type in search box → filters by filename
// Select status filter → filters by processing status
// Pagination updates automatically
```

### 4. Monitor Processing Progress
```typescript
// In DocumentStatus.tsx:
// Auto-refreshes every 2 seconds
// Shows progress via:
// - Overall status
// - Processing jobs timeline
// - Extracted fields count
// - Action items progress
```

## Customization

### Change Auto-Refresh Interval
In `DocumentStatus.tsx`:
```typescript
const { data, loading, error, refetch } = useDocumentStatus(id, {
  autoRefresh: true,
  refreshInterval: 5000  // Change to 5 seconds
});
```

### Change Page Size Default
In `Documents.tsx`:
```typescript
const [pageSize, setPageSize] = useState(25);  // Default 25 instead of 10
```

### Customize Status Colors
Add to any component:
```typescript
const statusColors: Record<string, 'success' | 'error' | 'info' | 'warning'> = {
  'COMPLETED': 'success',
  'FAILED': 'error',
  'IN_PROGRESS': 'info',
  'UPLOADED': 'warning',
};
```

## Debugging

### Check Network Requests
1. Open DevTools (F12)
2. Go to Network tab
3. Filter by XHR/Fetch
4. Look for `/api/v1/documents*` requests
5. Check response status and body

### Verify Auto-Refresh
1. Open DevTools Console
2. In DocumentStatus page, look for repeated requests
3. Every 2 seconds should see new request
4. Requests should stop after completion

### Check Component State
```typescript
// Add to component for debugging:
useEffect(() => {
  console.log('Data:', data);
  console.log('Loading:', loading);
  console.log('Error:', error);
}, [data, loading, error]);
```

## Performance Tips

1. **Limit Search Results:** Ensure pagination is working
2. **Stop Auto-Refresh:** Manually call `stopAutoRefresh()` if not needed
3. **Cache Data:** Consider implementing React Query for caching
4. **Lazy Load Tabs:** Load tab content only when visible
5. **Virtualize Lists:** For 1000+ documents, use react-window

## Security Best Practices

1. Always include Authorization header (handled by fetch interceptor)
2. Don't expose document IDs in URLs unnecessarily
3. Validate page parameters on frontend
4. Handle 401/403 errors gracefully
5. Clear auth tokens on logout

## Troubleshooting Quick Reference

| Issue | Solution |
|-------|----------|
| 404 Document Not Found | Verify document ID, check if document exists |
| 401 Unauthorized | Check auth token, re-login if needed |
| Empty document list | Check database, try without filters |
| Slow loading | Reduce page size, check network/database |
| Auto-refresh not working | Check browser console, verify server responding |
| Formatting errors in dates | Ensure date-fns is installed |
| Missing columns in table | Check API response includes all fields |

## Next Features to Implement

1. Document download (GET `/api/v1/documents/{id}/file`)
2. Field verification UI
3. Action plan management
4. Document comments
5. Audit trail view
6. WebSocket real-time updates
7. Batch operations
8. Export to CSV/PDF

---

**Questions or issues?** Check the main documentation:
- [PDF_INGESTION_SUMMARY.md](./PDF_INGESTION_SUMMARY.md) - Upload system
- [DOCUMENT_STATUS_TRACKING.md](./DOCUMENT_STATUS_TRACKING.md) - Status system
