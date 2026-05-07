"""
Test: Verify document upload, processing, and retrieval work end-to-end
"""
import requests
import json
import time
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

API_URL = "http://localhost:8000/api/v1"

def create_test_pdf(filename="test_doc.pdf"):
    """Create a simple test PDF"""
    pdf_path = Path(filename)
    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    
    # Add text
    c.drawString(100, 750, "Court Judgment - Test Document")
    c.drawString(100, 730, "Case: ABC v. DEF")
    c.drawString(100, 710, "Court: District Court")
    c.drawString(100, 690, "Judge: John Doe")
    c.drawString(100, 670, "Date: 2024-01-15")
    c.drawString(100, 650, "The court hereby orders...")
    
    # Add more pages
    for i in range(4):
        c.showPage()
        c.drawString(100, 750, f"Page {i+2}")
        c.drawString(100, 730, "Additional content for testing...")
    
    c.save()
    return pdf_path

def test_complete_workflow():
    """Test complete upload and processing workflow"""
    pdf_path = create_test_pdf("test_workflow.pdf")
    print(f"✓ Created test PDF: {pdf_path}\n")
    
    try:
        # Step 1: Upload document
        print("="*60)
        print("STEP 1: Upload Document")
        print("="*60)
        print(f"Uploading to {API_URL}/documents/upload...")
        start_time = time.time()
        
        with open(pdf_path, 'rb') as f:
            files = {'file': ('test.pdf', f, 'application/pdf')}
            response = requests.post(
                f"{API_URL}/documents/upload",
                files=files,
                timeout=120  # Longer timeout to allow processing
            )
        
        elapsed = time.time() - start_time
        print(f"✓ Response received in {elapsed:.2f}s")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"✗ Upload failed!")
            print(f"Response: {response.text}")
            return
        
        data = response.json()
        doc_id = data.get('document_id')
        print(f"✓ Document ID: {doc_id}")
        print(f"✓ Status: {data.get('status')}")
        print(f"✓ Pages: {data.get('page_count')}")
        print(f"✓ Text-based: {data.get('is_text_based')}")
        
        # Step 2: Get document details
        print("\n" + "="*60)
        print("STEP 2: Get Document Details")
        print("="*60)
        print(f"Getting {API_URL}/documents/{doc_id}...")
        
        response = requests.get(
            f"{API_URL}/documents/{doc_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✓ Document details retrieved")
            data = response.json()
            print(json.dumps(data, indent=2))
        else:
            print(f"✗ Failed to get document: {response.status_code}")
            print(f"Response: {response.text}")
        
        # Step 3: Get document status
        print("\n" + "="*60)
        print("STEP 3: Get Document Status")
        print("="*60)
        print(f"Getting {API_URL}/documents/{doc_id}/status...")
        
        response = requests.get(
            f"{API_URL}/documents/{doc_id}/status",
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✓ Document status retrieved")
            data = response.json()
            print(json.dumps(data, indent=2))
        else:
            print(f"✗ Failed to get status: {response.status_code}")
            print(f"Response: {response.text}")
        
        # Step 4: Check extracted fields
        print("\n" + "="*60)
        print("STEP 4: Get Extracted Fields")
        print("="*60)
        print(f"Getting {API_URL}/documents/{doc_id}/extracted-fields...")
        
        response = requests.get(
            f"{API_URL}/documents/{doc_id}/extracted-fields",
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✓ Extracted fields retrieved")
            data = response.json()
            print(json.dumps(data, indent=2))
        else:
            print(f"✗ Failed to get extracted fields: {response.status_code}")
            print(f"Response: {response.text}")
        
        print("\n" + "="*60)
        print("✓ WORKFLOW COMPLETE")
        print("="*60)
        
    except requests.exceptions.ReadTimeout as e:
        elapsed = time.time() - start_time
        print(f"✗ Timeout after {elapsed:.2f}s: {e}")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        pdf_path.unlink(missing_ok=True)

if __name__ == "__main__":
    test_complete_workflow()
