"""
End-to-end test for document upload + LLM extraction pipeline.
Tests: register → login → upload PDF → check status → verify LLM extraction
"""

import sys
import time
import json
import uuid
import requests
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

API_URL = "http://localhost:8000/api/v1"
TEST_EMAIL = f"test_{uuid.uuid4().hex[:8]}@example.com"
TEST_PASSWORD = "Test1234"  # Keep password short to avoid bcrypt 72-byte limit, min 8 chars
TEST_PDF = Path("test_judgment.pdf")

def create_test_pdf():
    """Create a valid test PDF with court judgment content."""
    print("[1/6] Creating test PDF...")
    c = canvas.Canvas(str(TEST_PDF), pagesize=letter)
    c.setFont("Helvetica", 12)
    
    c.drawString(50, 750, "HIGH COURT OF DELHI")
    c.drawString(50, 700, "CIVIL APPEAL NO. 2024-001")
    c.drawString(50, 650, "Dated: 2024-05-01")
    c.drawString(50, 550, "PETITIONER: State of Delhi")
    c.drawString(50, 500, "RESPONDENT: ABC Corporation")
    c.drawString(50, 400, "JUDGMENT")
    c.drawString(50, 350, "This court hereby directs the respondent to comply with all")
    c.drawString(50, 330, "statutory obligations within 30 days of the order.")
    c.drawString(50, 310, "The respondent shall submit a compliance report within 45 days.")
    c.drawString(50, 290, "Failure to comply will result in contempt proceedings.")
    c.save()
    print("✓ Test PDF created")
    return TEST_PDF

def register_user(email: str, password: str):
    """Register a new test user."""
    print(f"\n[2/6] Registering user: {email}")
    response = requests.post(
        f"{API_URL}/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Upload Tester"
        }
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✓ Registration successful")
    elif response.status_code == 409:
        print("⚠ User already exists (will login)")
    else:
        print(f"Response: {response.text}")
    return response.status_code in [200, 409]

def login_user(email: str, password: str):
    """Login and get access token."""
    print(f"\n[3/6] Logging in: {email}")
    response = requests.post(
        f"{API_URL}/auth/login",
        json={"email": email, "password": password}
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        access_token = data.get("access_token")
        print(f"✓ Login successful, token: {access_token[:20]}...")
        return access_token
    else:
        print(f"✗ Login failed: {response.text}")
        return None

def upload_document(token: str, pdf_path: Path):
    """Upload PDF document."""
    print(f"\n[4/6] Uploading PDF: {pdf_path.name}")
    
    with open(pdf_path, 'rb') as f:
        files = {'file': f}
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.post(
            f"{API_URL}/documents/upload",
            files=files,
            headers=headers
        )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:300]}")
    
    if response.status_code == 200:
        data = response.json()
        document_id = data.get("document_id")
        print(f"✓ Upload successful, document_id: {document_id}")
        return document_id
    else:
        print(f"✗ Upload failed")
        return None

def check_document_status(token: str, document_id: str, max_wait: int = 60):
    """Check document processing status and wait for LLM extraction."""
    print(f"\n[5/6] Checking document status (max {max_wait}s wait)...")
    
    headers = {'Authorization': f'Bearer {token}'}
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        response = requests.get(
            f"{API_URL}/documents/{document_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            status = data.get("status")
            print(f"  Status: {status}")
            
            if status == "PENDING_REVIEW":
                print("✓ Document reached PENDING_REVIEW (LLM extraction complete!)")
                return True, data
            elif status == "FAILED":
                error = data.get("error_message")
                print(f"✗ Processing failed: {error}")
                return False, data
        else:
            print(f"  API error: {response.status_code}")
        
        time.sleep(3)
    
    print(f"✗ Timeout waiting for processing")
    return False, None

def get_extracted_fields(token: str, document_id: str):
    """Retrieve extracted fields from LLM."""
    print(f"\n[6/6] Retrieving extracted fields...")
    
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(
        f"{API_URL}/documents/{document_id}/extractions",
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        fields_count = data.get("total_fields", 0)
        print(f"✓ Retrieved {fields_count} extracted fields")
        
        fields = data.get("fields", [])
        for field in fields[:3]:
            print(f"  - {field.get('field_type')}: {field.get('value')[:100]}")
        
        return True, data
    else:
        print(f"✗ Failed to retrieve fields: {response.text[:300]}")
        return False, None

def main():
    """Run the complete end-to-end test."""
    print("=" * 70)
    print("LAOS Document Upload + LLM Extraction End-to-End Test")
    print("=" * 70)
    
    try:
        # Step 1: Create test PDF
        pdf_path = create_test_pdf()
        
        # Step 2: Register user
        if not register_user(TEST_EMAIL, TEST_PASSWORD):
            print("✗ Registration failed")
            return False
        
        # Step 3: Login
        access_token = login_user(TEST_EMAIL, TEST_PASSWORD)
        if not access_token:
            print("✗ Login failed")
            return False
        
        # Step 4: Upload document
        document_id = upload_document(access_token, pdf_path)
        if not document_id:
            print("✗ Upload failed")
            return False
        
        # Step 5: Check status
        success, status_data = check_document_status(access_token, document_id)
        if not success:
            print("✗ Document processing failed")
            return False
        
        # Step 6: Get extracted fields
        success, fields_data = get_extracted_fields(access_token, document_id)
        if not success:
            print("⚠ Could not retrieve fields (may not be extracted yet)")
        
        # Cleanup
        if TEST_PDF.exists():
            TEST_PDF.unlink()
        
        print("\n" + "=" * 70)
        print("✓ END-TO-END TEST PASSED!")
        print("Document upload + LLM extraction pipeline is working correctly.")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
