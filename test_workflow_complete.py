#!/usr/bin/env python3
"""
Full workflow test: Upload PDF -> Extract -> Analyze with LLM
"""

import requests
import json
import time
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

API_URL = "http://localhost:8000/api/v1"

def create_test_pdf():
    """Create a test PDF document."""
    pdf_path = Path("test_judgment_workflow.pdf")
    
    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, "HIGH COURT OF DELHI")
    
    c.setFont("Helvetica", 12)
    c.drawString(50, 700, "CIVIL APPEAL NO. 2024-001")
    c.drawString(50, 680, "Dated: 2024-05-01")
    
    c.drawString(50, 630, "PETITIONER: State of Delhi")
    c.drawString(50, 610, "RESPONDENT: ABC Corporation")
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 550, "JUDGMENT")
    
    c.setFont("Helvetica", 11)
    y = 520
    text = [
        "This is a judgment by the High Court of Delhi.",
        "",
        "The petitioner has filed an appeal against the decision of the lower court.",
        "",
        "The court finds that:",
        "1. The respondent has violated statutory obligations",
        "2. The action taken was unjustified and arbitrary",
        "3. Compensation of Rs. 50,000 is awarded to the petitioner",
        "",
        "DIRECTIONS:",
        "1. The respondent shall comply with all statutory obligations within 30 days",
        "2. The respondent shall submit a compliance report within 45 days",
        "3. Failure to comply will result in contempt of court proceedings",
        "4. The respondent shall pay compensation within 15 days",
        "",
        "Status: Judgment Delivered",
        "Signed by: Hon'ble Justice A.K. Sharma",
    ]
    
    for line in text:
        c.drawString(50, y, line)
        y -= 15
    
    c.save()
    print(f"✅ Created test PDF: {pdf_path}")
    return pdf_path

def upload_document(pdf_path: Path):
    """Upload document without authentication."""
    print(f"\n📤 Uploading document: {pdf_path.name}")
    
    with open(pdf_path, "rb") as f:
        files = {"file": f}
        response = requests.post(
            f"{API_URL}/documents/upload",
            files=files
        )
    
    print(f"   Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"   Error: {response.text[:300]}")
        return None
    
    data = response.json()
    doc_id = data.get("document_id")
    print(f"   ✅ Document uploaded: {doc_id}")
    print(f"   Filename: {data.get('filename')}")
    print(f"   Status: {data.get('status')}")
    
    return doc_id

def check_document_status(doc_id: str):
    """Check document processing status."""
    print(f"\n📊 Checking document status...")
    
    response = requests.get(
        f"{API_URL}/documents/{doc_id}/status"
    )
    
    if response.status_code != 200:
        print(f"   Error: {response.text[:300]}")
        return None
    
    data = response.json()
    status = data.get("status")
    print(f"   Status: {status}")
    
    if status == "VERIFIED":
        print(f"   ✅ Document verified and ready for analysis")
    elif status == "PROCESSING":
        print(f"   ⏳ Document still processing...")
    elif status == "FAILED":
        print(f"   ❌ Processing failed: {data.get('error')}")
        return None
    
    return status

def get_extracted_fields(doc_id: str):
    """Get extracted fields from document."""
    print(f"\n📋 Getting extracted fields...")
    
    response = requests.get(
        f"{API_URL}/documents/{doc_id}/extracted-fields"
    )
    
    if response.status_code != 200:
        print(f"   Error (Status {response.status_code}): {response.text[:300]}")
        return None
    
    data = response.json()
    fields = data.get("fields", [])
    
    print(f"   ✅ Extracted {len(fields)} fields:")
    for field in fields[:10]:
        name = field.get("key", "unknown")
        value = field.get("value", "")[:60]
        print(f"      • {name}: {value}...")
    
    return fields

def get_full_extraction(doc_id: str):
    """Get full extraction data."""
    print(f"\n📄 Getting full extraction...")
    
    response = requests.get(
        f"{API_URL}/documents/{doc_id}/extraction"
    )
    
    if response.status_code != 200:
        print(f"   Error (Status {response.status_code}): {response.text[:300]}")
        return None
    
    data = response.json()
    print(f"   ✅ Extraction retrieved")
    print(f"   Pages: {data.get('total_pages')}")
    print(f"   Content preview: {data.get('raw_text', '')[:100]}...")
    
    return data

def run_llm_analysis(doc_id: str, prompt: str):
    """Run LLM analysis on document."""
    print(f"\n🤖 Running LLM analysis...")
    print(f"   Prompt: {prompt}")
    
    response = requests.post(
        f"{API_URL}/documents/{doc_id}/llm-analysis",
        json={"prompt": prompt}
    )
    
    if response.status_code != 200 and response.status_code != 202:
        print(f"   Error (Status {response.status_code}): {response.text[:300]}")
        return None
    
    data = response.json()
    print(f"   ✅ Analysis started")
    print(f"   Task ID: {data.get('task_id')}")
    print(f"   Status: {data.get('status')}")
    
    return data.get("task_id")

def get_llm_result(doc_id: str, task_id: str):
    """Get LLM analysis result."""
    print(f"\n📝 Getting LLM result (Task: {task_id[:8]}...)...")
    
    response = requests.get(
        f"{API_URL}/documents/{doc_id}/llm-analysis/{task_id}"
    )
    
    if response.status_code != 200:
        print(f"   Error (Status {response.status_code}): {response.text[:300]}")
        return None
    
    data = response.json()
    result = data.get("result")
    
    print(f"   ✅ Result retrieved")
    print(f"   Status: {data.get('status')}")
    
    if result:
        print(f"\n   Analysis Result:")
        print(f"   {result[:500]}...")
    
    return result

def main():
    """Run full workflow test."""
    print("=" * 70)
    print("LAOS DOCUMENT UPLOAD & ANALYSIS WORKFLOW TEST")
    print("=" * 70)
    
    # Step 1: Create test PDF
    pdf_path = create_test_pdf()
    
    # Step 2: Upload document
    doc_id = upload_document(pdf_path)
    if not doc_id:
        print("\n❌ Failed to upload document")
        return
    
    # Step 3: Wait a bit for processing to start
    print("\n⏳ Waiting for initial processing...")
    time.sleep(3)
    
    # Step 4: Check status
    status = check_document_status(doc_id)
    if status == "FAILED":
        print("\n❌ Document processing failed")
        return
    
    # Step 5: Get extracted fields
    print("\n⏳ Waiting for extraction to complete...")
    time.sleep(2)
    fields = get_extracted_fields(doc_id)
    
    # Step 6: Get full extraction
    extraction = get_full_extraction(doc_id)
    
    # Step 7: Run LLM analysis
    prompts = [
        "Summarize the key judgments and orders in 3 bullet points",
        "What are the main statutory violations mentioned?",
        "Extract the compensation amount and compliance timeline"
    ]
    
    task_ids = []
    for prompt in prompts:
        task_id = run_llm_analysis(doc_id, prompt)
        if task_id:
            task_ids.append((task_id, prompt))
    
    # Step 8: Get LLM results
    print("\n⏳ Waiting for LLM analysis to complete...")
    time.sleep(5)
    
    for task_id, prompt in task_ids:
        print(f"\n📌 Prompt: {prompt}")
        result = get_llm_result(doc_id, task_id)
    
    print("\n" + "=" * 70)
    print("✅ WORKFLOW TEST COMPLETE")
    print("=" * 70)
    print(f"\nDocument ID: {doc_id}")
    print(f"API Base: {API_URL}")
    print(f"\nEndpoints available:")
    print(f"  • GET  /documents/{doc_id} - Document details")
    print(f"  • GET  /documents/{doc_id}/status - Processing status")
    print(f"  • GET  /documents/{doc_id}/extracted-fields - Extracted fields")
    print(f"  • GET  /documents/{doc_id}/extraction - Full extraction")
    print(f"  • POST /documents/{doc_id}/llm-analysis - Run analysis")
    print(f"  • GET  /documents/{doc_id}/llm-analysis/<task_id> - Get result")

if __name__ == "__main__":
    main()
