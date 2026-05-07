"""
Simplified end-to-end test using direct API calls and existing test account.
"""

import sys
import time
import json
import requests
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

API_URL = "http://localhost:8000/api/v1"
TEST_PDF = Path("test_judgment.pdf")

# Use existing test account (pre-seeded in database)
TEST_EMAIL = "reviewer@laos.gov.in"
TEST_PASSWORD = "Reviewer@123456"

def create_test_pdf():
    """Create a valid test PDF with court judgment content."""
    print("[1/5] Creating test PDF...")
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

def login_user(email: str, password: str):
    """Login and get access token."""
    print(f"\n[2/5] Logging in as: {email}")
    response = requests.post(
        f"{API_URL}/auth/login",
        data={"username": email, "password": password}  # Use form data, not JSON
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        access_token = data.get("access_token")
        print(f"✓ Login successful")
        return access_token
    else:
        print(f"✗ Login failed: {response.text[:300]}")
        return None

def upload_document(token: str, pdf_path: Path):
    """Upload PDF document."""
    print(f"\n[3/5] Uploading PDF: {pdf_path.name}")
    
    with open(pdf_path, 'rb') as f:
        files = {'file': f}
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.post(
            f"{API_URL}/documents/upload",
            files=files,
            headers=headers,
            timeout=30
        )
    
    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Response: {response.text[:500]}")
        return None
    
    data = response.json()
    document_id = data.get("document_id")
    print(f"✓ Upload successful, document_id: {document_id}")
    print(f"  Filename: {data.get('filename')}")
    print(f"  Status: {data.get('status')}")
    return document_id

def check_document_status(token: str, document_id: str, max_wait: int = 90):
    """Check document processing status and wait for LLM extraction."""
    print(f"\n[4/5] Checking document status (max {max_wait}s wait)...")
    
    headers = {'Authorization': f'Bearer {token}'}
    start_time = time.time()
    wait_count = 0
    
    while time.time() - start_time < max_wait:
        response = requests.get(
            f"{API_URL}/documents/{document_id}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            status = data.get("status")
            print(f"  [{wait_count}] Status: {status}")
            
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
        wait_count += 1
    
    print(f"✗ Timeout waiting for processing (checked {wait_count} times)")
    return False, None

def get_extracted_fields(token: str, document_id: str):
    """Retrieve extracted fields from LLM."""
    print(f"\n[5/5] Retrieving extracted fields...")
    
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(
        f"{API_URL}/documents/{document_id}/extractions",
        headers=headers,
        timeout=10
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        fields_count = data.get("total_fields", 0)
        print(f"✓ Retrieved {fields_count} extracted fields")
        
        fields = data.get("fields", [])
        for i, field in enumerate(fields[:5]):
            value_preview = str(field.get('value', ''))[:80]
            print(f"  [{i+1}] {field.get('field_type')}: {value_preview}")
        
        return True, data
    else:
        print(f"⚠ Status {response.status_code}: {response.text[:300]}")
        return False, None

def main():
    """Run the simplified end-to-end test."""
    print("=" * 70)
    print("LAOS Document Upload + LLM Extraction E2E Test")
    print("=" * 70)
    
    try:
        # Step 1: Create test PDF
        pdf_path = create_test_pdf()
        
        # Step 2: Login
        access_token = login_user(TEST_EMAIL, TEST_PASSWORD)
        if not access_token:
            print("✗ Login failed")
            return False
        
        # Step 3: Upload document
        document_id = upload_document(access_token, pdf_path)
        if not document_id:
            print("✗ Upload failed")
            return False
        
        # Step 4: Check status and wait for processing
        success, status_data = check_document_status(access_token, document_id, max_wait=90)
        if not success:
            print("⚠ Document processing did not reach PENDING_REVIEW")
            if status_data:
                print(f"  Final status: {status_data.get('status')}")
                if status_data.get('error_message'):
                    print(f"  Error: {status_data.get('error_message')}")
        
        # Step 5: Try to get extracted fields (may not exist if processing failed)
        if success:
            get_extracted_fields(access_token, document_id)
        
        # Cleanup
        if TEST_PDF.exists():
            TEST_PDF.unlink()
        
        print("\n" + "=" * 70)
        if success:
            print("✓ END-TO-END TEST PASSED!")
            print("Document upload + LLM extraction pipeline is working!")
        else:
            print("⚠ TEST COMPLETED WITH WARNINGS")
            print("Document was uploaded but processing did not complete successfully.")
        print("=" * 70)
        return success
        
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
