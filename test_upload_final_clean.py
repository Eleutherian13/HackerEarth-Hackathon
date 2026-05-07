"""
Create a test user directly in the database to bypass registration issues.
Then run upload + ingestion test.
"""

import sys
import time
import json
import requests
import subprocess
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Add backend to path
sys.path.insert(0, r"c:\Users\manas\OneDrive\Desktop\LAOS\backend")

from app.db.session import SessionLocal
from app.models.domain.models import User, Department
from app.models.enums import UserRole
import bcrypt
API_URL = "http://localhost:8000/api/v1"
TEST_PDF = Path("test_judgment.pdf")
# Test account - use seeded account to avoid auth issues
TEST_EMAIL = "admin@laos.gov.in"
TEST_PASSWORD = "Admin@123456"

def create_user_in_db(email, password, full_name="Test Upload User"):
    """Create a user directly in the database."""
    print(f"[1/5] Creating user in database: {email}")
    
    db = SessionLocal()
    try:
        # Check if user exists
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"✓ User already exists")
            db.close()
            return True
        
        # Get or create a default department
        dept = db.query(Department).first()
        if not dept:
            # Create a default department if none exists
            dept = Department(
                name="General",
                code="GEN"
            )
            db.add(dept)
            db.commit()
        
        # Hash password using bcrypt directly
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        
        # Create user
        user = User(
            email=email,
            full_name=full_name,
            hashed_password=hashed,
            department_id=dept.id,
            role=UserRole.REVIEWER,
            is_active=True
        )
        
        db.add(user)
        db.commit()
        print(f"✓ User created successfully")
        db.close()
        return True
    except Exception as e:
        print(f"[ERROR] Failed to create user: {e}")
        db.rollback()
        db.close()
        return False

def create_test_pdf():
    """Create a valid test PDF."""
    print("[2/5] Creating test PDF...")
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

def login_user(email, password):
    """Login and get token."""
    print(f"[3/5] Logging in: {email}")
    
    # Use form data for OAuth2PasswordRequestForm
    response = requests.post(
        f"{API_URL}/auth/login",
        data={"username": email, "password": password},
        timeout=10
    )
    
    print(f"  Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        print(f"✓ Login successful")
        return token
    else:
        print(f"✗ Login failed: {response.text[:300]}")
        return None

def upload_pdf(token, pdf_path):
    """Upload PDF document."""
    print(f"[4/5] Uploading PDF: {pdf_path.name}")
    
    with open(pdf_path, 'rb') as f:
        files = {'file': f}
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.post(
            f"{API_URL}/documents/upload",
            files=files,
            headers=headers,
            timeout=30
        )
    
    print(f"  Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        doc_id = data.get("document_id")
        print(f"✓ Upload successful: {doc_id}")
        return doc_id
    else:
        print(f"✗ Upload failed: {response.text[:300]}")
        return None

def check_status(token, doc_id, max_wait=90):
    """Check processing status."""
    print(f"[5/5] Checking processing (waiting up to {max_wait}s)...")
    
    headers = {'Authorization': f'Bearer {token}'}
    start = time.time()
    attempt = 0
    
    while time.time() - start < max_wait:
        response = requests.get(
            f"{API_URL}/documents/{doc_id}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            status = data.get("status")
            print(f"  [{attempt}] {status}")
            
            if status == "PENDING_REVIEW":
                print(f"✓ Processing complete! Document ready for review")
                return True
            elif status == "FAILED":
                print(f"✗ Processing failed: {data.get('error_message')}")
                return False
        
        time.sleep(3)
        attempt += 1
    
    print(f"✗ Timeout")
    return False

def main():
    """Run test."""
    print("=" * 70)
    print("LAOS Upload + LLM Ingestion Test")
    print("=" * 70 + "\n")
    
    try:
        # Step 1: Skip user creation - using seeded account
        print(f"[1/5] Using seeded account: {TEST_EMAIL}\n")
        
        # Step 2: Create PDF
        create_test_pdf()
        
        # Step 3: Login
        token = login_user(TEST_EMAIL, TEST_PASSWORD)
        if not token:
            return False
        
        # Step 4: Upload
        doc_id = upload_pdf(token, TEST_PDF)
        if not doc_id:
            return False
        
        # Step 5: Check status
        success = check_status(token, doc_id)
        
        # Cleanup
        TEST_PDF.unlink(missing_ok=True)
        
        print("\n" + "=" * 70)
        if success:
            print("✓ SUCCESS: Document uploaded and LLM extraction completed!")
            print("The ingestion pipeline is working end-to-end.")
        else:
            print("⚠ Upload succeeded but processing did not complete")
        print("=" * 70)
        return success
        
    except Exception as e:
        print(f"\n[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
