"""
Quick test: Upload document and return immediately without waiting for processing.
"""
import requests
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import time

API_URL = "http://localhost:8000/api/v1"

def create_test_pdf():
    """Create a simple test PDF"""
    pdf_path = Path("test_simple.pdf")
    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    
    # Add text
    c.drawString(100, 750, "Court Judgment")
    c.drawString(100, 730, "Case: ABC v. DEF")
    c.drawString(100, 710, "Court: District Court")
    c.drawString(100, 690, "Judge: John Doe")
    c.drawString(100, 670, "Date: 2024-01-15")
    c.drawString(100, 650, "The court hereby orders...")
    
    # Add more pages for testing
    for i in range(4):  # Total 5 pages
        c.showPage()
        c.drawString(100, 750, f"Page {i+2}")
        c.drawString(100, 730, "Additional content for testing...")
    
    c.save()
    return pdf_path

def upload_document():
    """Upload document and return immediately"""
    pdf_path = create_test_pdf()
    print(f"✓ Created test PDF: {pdf_path}")
    
    try:
        print(f"⏱ Uploading to {API_URL}/documents/upload...")
        start_time = time.time()
        
        with open(pdf_path, 'rb') as f:
            files = {'file': ('test.pdf', f, 'application/pdf')}
            
            # Use a long timeout to see if the server ever responds
            response = requests.post(
                f"{API_URL}/documents/upload",
                files=files,
                timeout=60  # Longer timeout
            )
        
        elapsed = time.time() - start_time
        print(f"✓ Upload response received in {elapsed:.2f}s")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            doc_id = response.json().get('document_id')
            print(f"✓ Document ID: {doc_id}")
            
            # Now check status
            print(f"\nChecking document status...")
            status_response = requests.get(
                f"{API_URL}/documents/{doc_id}/status",
                timeout=10
            )
            print(f"Status response: {status_response.json()}")
            
    except requests.exceptions.ReadTimeout as e:
        elapsed = time.time() - start_time
        print(f"✗ Timeout after {elapsed:.2f}s: {e}")
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        pdf_path.unlink(missing_ok=True)

if __name__ == "__main__":
    upload_document()
