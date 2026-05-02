"""
API Input Validation Implementation - Summary

This implementation provides defense-in-depth input validation across all API endpoints.

COMPONENTS IMPLEMENTED:

1. Core Validators Module (/backend/app/core/validators.py)
   - InputValidator class with 15+ validation methods
   - Case number format validation (Indian court formats)
   - Date range validation
   - Email domain validation (government email only)
   - File size validation (0 < size <= max_mb)
   - Filename validation (path traversal prevention)
   - Pagination validation (page >= 1, per_page in range)
   - Sort column/order validation (whitelist-based)
   - XSS/HTML injection prevention
   - Password strength validation
   - Text sanitization
   - UUID format validation
   - Field-specific validators (case details, parties, etc.)

2. Validation Dependencies (/backend/app/api/deps.py)
   - validate_document_exists(document_id) -> returns Document or 404
   - validate_field_exists(field_id) -> returns ExtractedField or 404
   - validate_reviewer_permission(current_user) -> checks role permissions
   - validate_pagination_params() -> validates page, per_page with limits
   - validate_sort_params() -> validates sort_by and sort_order

3. Request Size Limiting Middleware (/backend/app/api/middleware/size_limit.py)
   - RequestSizeLimitMiddleware: Enforces max body size
     * Default: 10MB for all requests
     * Upload endpoint: 55MB
     * Returns 413 Payload Too Large if exceeded
     * Logs oversized attempts
   
   - ContentTypeValidationMiddleware: Validates Content-Type headers
     * JSON endpoints must have Content-Type: application/json
     * Upload endpoint must have Content-Type: multipart/form-data
     * Returns 415 Unsupported Media Type for violations
     * Prevents content-type confusion attacks

4. Endpoint Validations

   A. Document Upload (/api/v1/documents/upload)
      - File size validation (reject > 50MB)
      - Filename validation (no path traversal, < 500 chars)
      - PDF format validation (existing)
      - Duplicate detection (existing)
      - Metadata JSON validation
   
   B. Field Review (/api/v1/documents/{id}/fields/{id}/review)
      - expected_version must be positive integer
      - Comments XSS prevention (no <script>, javascript:, etc)
      - Comments length validation (max 2000 chars)
      - Review action enum validation (existing in schema)
      - UUID format validation for document/field IDs
   
   C. Dashboard/Listing (endpoints not modified yet, but validators ready)
      - Pagination validation via validate_pagination_params
      - Sort validation via validate_sort_params
      - Search query sanitization via InputValidator.sanitize_search_query
   
   D. Admin endpoints (validators ready via deps)
      - validate_reviewer_permission for role checks
      - Password strength validation available

MIDDLEWARE SETUP:
   The middlewares are added to the FastAPI app in /backend/main.py:
   - ContentTypeValidationMiddleware (applied first)
   - RequestSizeLimitMiddleware (applied second)

VALIDATION RESPONSE CODES:
   - 200: Valid request, processed successfully
   - 400: Bad Request (malformed input, validation failed)
   - 413: Payload Too Large (request size exceeds limit)
   - 415: Unsupported Media Type (wrong Content-Type header)
   - 422: Unprocessable Entity (semantic validation failed)
   - 404: Not Found (resource doesn't exist)
   - 403: Forbidden (insufficient permissions)

SECURITY FEATURES:
   1. XSS Prevention: Detects and rejects HTML/script content
   2. Path Traversal Prevention: Rejects filenames with .., /, \\, \x00
   3. SQL Injection Prevention: Sanitizes search queries, validates sort columns (whitelist)
   4. File Size Limits: Prevents disk exhaustion attacks
   5. Rate Limiting Ready: Infrastructure for slowapi integration
   6. Strong Password Requirements: 12+ chars, mixed case, numbers, special chars
   7. Content-Type Validation: Prevents header-based attacks

HOW TO USE:

1. In endpoint handlers, import validators:
   ```python
   from app.core.validators import InputValidator
   from app.api.deps import validate_pagination_params, validate_sort_params
   ```

2. For file operations:
   ```python
   if not InputValidator.validate_filename(filename):
       raise HTTPException(400, "Invalid filename")
   if not InputValidator.validate_file_size(file_size):
       raise HTTPException(413, "File too large")
   ```

3. For user input:
   ```python
   if not InputValidator.validate_no_html_script(user_comment):
       raise HTTPException(422, "XSS detected")
   if not InputValidator.validate_text_length(comment, max_length=2000):
       raise HTTPException(422, "Text too long")
   ```

4. For pagination/sorting:
   ```python
   page, per_page = await validate_pagination_params(page=1, per_page=20)
   sort_by, sort_order = await validate_sort_params(sort_by="created_at", sort_order="DESC")
   ```

5. For email domains:
   ```python
   if not InputValidator.validate_email_domain(email):
       raise HTTPException(400, "Only government emails allowed")
   ```

TESTING:
   Unit tests for validators: Test InputValidator methods directly
   Integration tests: /backend/tests/integration/test_input_validation.py
   
   Test cases cover:
   - File upload validations
   - Review submission validations
   - Pagination validations
   - Sort parameter validations
   - XSS prevention
   - Content-Type validation
   - Authentication/authorization
   - Request size limits

NEXT STEPS FOR FULL IMPLEMENTATION:

1. Apply validators to dashboard endpoints:
   - GET /api/v1/dashboard
   - GET /api/v1/action-items
   - Any list/filter endpoints

2. Apply validators to admin endpoints:
   - POST /api/v1/admin/users (password strength, email domain)
   - PUT /api/v1/admin/users/{id}
   - Role validation for role assignments

3. Implement rate limiting:
   - Install slowapi: pip install slowapi
   - Create /backend/app/core/rate_limiter.py
   - Apply @limiter decorators to endpoints

4. Add OWASP ZAP scanning:
   - Run automated security scans
   - Fix any findings
   - Integrate into CI/CD

5. Add API rate limiting headers:
   - X-RateLimit-Limit
   - X-RateLimit-Remaining
   - X-RateLimit-Reset

VALIDATION PATTERNS USED:

Pattern 1: Whitelist-based (most secure)
   - Allowed columns: ["created_at", "updated_at", "status"]
   - Allowed roles: {REVIEWER, ADMIN, SUPERADMIN}

Pattern 2: Regex-based (for formats)
   - Case numbers: r'^[A-Z]+[\s/-]*\(?[A-Z]?\)?\s*\d+[\s/-]\d{4}$'
   - UUIDs: r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'

Pattern 3: Length-based
   - Comments: 0-2000 characters
   - Filenames: 1-500 characters
   - Search queries: 1-200 characters

Pattern 4: Content-based (removal)
   - HTML tags: <script>, <iframe>, <object>, <embed>
   - Event handlers: onerror, onload, onclick
   - Protocols: javascript:, data:

CONFIGURATION:

Email domains (in InputValidator.ALLOWED_EMAIL_DOMAINS):
   - nic.in
   - gov.in
   - mailbox.nic.in
   - meity.gov.in
   - dopt.gov.in
   - agmis.nic.in
   - judiciary.nic.in
   (Add more as needed)

File size limits (in validators):
   - Default: 10MB
   - PDF uploads: 50MB
   - Middleware absolute: 55MB

Pagination defaults (in validators):
   - Min page: 1
   - Min per_page: 1
   - Max per_page: 100 (default, configurable)

PASSWORD REQUIREMENTS:
   - Minimum 12 characters
   - Must contain lowercase letters
   - Must contain uppercase letters
   - Must contain numbers
   - Must contain special characters (!@#$%^&*, etc)

"""
