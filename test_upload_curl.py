"""
Direct test of document upload and ingestion using curl commands.
Handles authentication and multipart uploads properly.
"""

import subprocess
import json
import time
import sys
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

API_URL = "http://localhost:8000/api/v1"
TEST_PDF = Path("test_judgment.pdf")
TEST_EMAIL = "testupload123@example.com"
TEST_PASSWORD = "Pass123456"  # Valid per schema: min 8, max 100

def create_test_pdf():
    """Create a valid test PDF."""
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
    c.save()
    print("✓ Test PDF created")

def curl_post_json(url, data, headers=None):
    """Execute curl POST with JSON data."""
    cmd = [
        "curl", "-s", "-X", "POST", url,
        "-H", "Content-Type: application/json",
    ]
    if headers:
        for k, v in headers.items():
            cmd.extend(["-H", f"{k}: {v}"])
    cmd.extend(["-d", json.dumps(data)])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"error": result.stdout}

def curl_post_form(url, files=None, data=None, headers=None):
    """Execute curl POST with multipart form data."""
    cmd = ["curl", "-s", "-X", "POST", url]
    if headers:
        for k, v in headers.items():
            cmd.extend(["-H", f"{k}: {v}"])
    if data:
        for k, v in data.items():
            cmd.extend(["-F", f"{k}={v}"])
    if files:
        for k, v in files.items():
            cmd.extend(["-F", f"{k}=@{v}"])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"error": result.stdout, "raw": result.stdout[:300]}

def register_user(email, password, full_name="Test User"):
    """Register a new user."""
    print(f"\n[2/5] Registering user: {email}")
    response = curl_post_json(
        f"{API_URL}/auth/register",
        {
            "email": email,
            "password": password,
            "full_name": full_name
        }
    )
    
    print(f"Response: {json.dumps(response, indent=2)[:200]}")
    
    if "access_token" in response:
        print(f"✓ Registration successful")
        return response.get("access_token")
    elif "error" in response and "already" in str(response).lower():
        print("⚠ User already exists, attempting login...")
        return login_user(email, password)
    else:
        print(f"✗ Registration failed")
        return None

def login_user(email, password):
    """Login user using form data."""
    print(f"  Logging in: {email}")
    # OAuth2PasswordRequestForm expects username and password
    response = curl_post_json(
        f"{API_URL}/auth/login",
        {}  # Will use form data in curl
    )
    # Actually use curl with form data
    cmd = [
        "curl", "-s", "-X", "POST", f"{API_URL}/auth/login",
        "-d", f"username={email}&password={password}"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        response = json.loads(result.stdout)
        if "access_token" in response:
            print(f"✓ Login successful")
            return response.get("access_token")
    except:
        pass
    print(f"✗ Login failed")
    return None

def upload_pdf(token, pdf_path):
    """Upload PDF using curl."""
    print(f"\n[3/5] Uploading PDF: {pdf_path.name}")
    
    response = curl_post_form(
        f"{API_URL}/documents/upload",
        files={"file": str(pdf_path)},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if "document_id" in response:
        doc_id = response.get("document_id")
        print(f"✓ Upload successful")
        print(f"  Document ID: {doc_id}")
        print(f"  Status: {response.get('status')}")
        return doc_id
    else:
        print(f"✗ Upload failed: {response}")
        return None

def check_status(token, doc_id, max_wait=90):
    """Check document status with polling."""
    print(f"\n[4/5] Checking processing status ({max_wait}s timeout)...")
    
    start = time.time()
    attempt = 0
    
    while time.time() - start < max_wait:
        cmd = [
            "curl", "-s", "-X", "GET", f"{API_URL}/documents/{doc_id}",
            "-H", f"Authorization: Bearer {token}"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        try:
            response = json.loads(result.stdout)
            status = response.get("status")
            print(f"  [{attempt}] Status: {status}")
            
            if status == "PENDING_REVIEW":
                print(f"✓ Processing complete!")
                return True, response
            elif status == "FAILED":
                print(f"✗ Processing failed: {response.get('error_message')}")
                return False, response
        except:
            pass
        
        time.sleep(3)
        attempt += 1
    
    print(f"✗ Timeout waiting for processing")
    return False, None

def main():
    """Run end-to-end test."""
    print("=" * 70)
    print("LAOS Upload + LLM Extraction E2E Test")
    print("=" * 70)
    
    try:
        # Step 1: Create PDF
        create_test_pdf()
        
        # Step 2: Register/Login
        token = register_user(TEST_EMAIL, TEST_PASSWORD)
        if not token:
            print("✗ Auth failed")
            return False
        
        # Step 3: Upload
        doc_id = upload_pdf(token, TEST_PDF)
        if not doc_id:
            print("✗ Upload failed")
            return False
        
        # Step 4: Check status
        success, status_data = check_status(token, doc_id)
        
        # Cleanup
        TEST_PDF.unlink(missing_ok=True)
        
        print("\n" + "=" * 70)
        if success:
            print("✓ TEST PASSED: Upload + LLM extraction working!")
        else:
            print("⚠ Upload succeeded but processing incomplete")
        print("=" * 70)
        return success
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
