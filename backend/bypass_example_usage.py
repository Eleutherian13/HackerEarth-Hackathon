#!/usr/bin/env python3
"""
Example: Using LAOS LLM Features with Authentication Bypass

This example shows how to interact with the LAOS API when AUTH_BYPASS is enabled.
No authentication tokens are required.

Features demonstrated:
1. Document upload (PDF)
2. Document extraction and processing
3. LLM-based analysis and extraction
4. Review and feedback
"""

import requests
import json
from pathlib import Path
from typing import Optional

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

class LAOSBypassClient:
    """Client for LAOS API in bypass mode (no auth required)."""
    
    def __init__(self, base_url: str = API_BASE):
        self.base_url = base_url
        self.session = requests.Session()
    
    def health_check(self) -> dict:
        """Check if the server is running."""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def upload_document(
        self, 
        pdf_path: str, 
        metadata: Optional[dict] = None
    ) -> dict:
        """Upload a PDF document for processing."""
        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        files = {"file": open(pdf_file, "rb")}
        data = {}
        if metadata:
            data["metadata"] = json.dumps(metadata)
        
        response = self.session.post(
            f"{self.base_url}/documents/upload",
            files=files,
            data=data
        )
        response.raise_for_status()
        return response.json()
    
    def get_document_status(self, document_id: str) -> dict:
        """Get the processing status of a document."""
        response = self.session.get(
            f"{self.base_url}/documents/{document_id}/status"
        )
        response.raise_for_status()
        return response.json()
    
    def get_extracted_fields(self, document_id: str) -> dict:
        """Get extracted fields from a document."""
        response = self.session.get(
            f"{self.base_url}/documents/{document_id}/extracted-fields"
        )
        response.raise_for_status()
        return response.json()
    
    def get_document_extraction(self, document_id: str) -> dict:
        """Get full extraction data from a document."""
        response = self.session.get(
            f"{self.base_url}/documents/{document_id}/extraction"
        )
        response.raise_for_status()
        return response.json()
    
    def list_documents(self, skip: int = 0, limit: int = 10) -> dict:
        """List all uploaded documents."""
        response = self.session.get(
            f"{self.base_url}/documents",
            params={"skip": skip, "limit": limit}
        )
        response.raise_for_status()
        return response.json()
    
    def start_llm_analysis(
        self, 
        document_id: str, 
        prompt: str
    ) -> dict:
        """Start LLM analysis on extracted document content."""
        response = self.session.post(
            f"{self.base_url}/documents/{document_id}/llm-analysis",
            json={"prompt": prompt}
        )
        response.raise_for_status()
        return response.json()
    
    def get_llm_analysis_result(
        self, 
        document_id: str, 
        task_id: str
    ) -> dict:
        """Get the result of an LLM analysis task."""
        response = self.session.get(
            f"{self.base_url}/documents/{document_id}/llm-analysis/{task_id}"
        )
        response.raise_for_status()
        return response.json()


def example_workflow():
    """Example workflow demonstrating the LAOS system."""
    
    print("=" * 60)
    print("LAOS Authentication Bypass - Example Workflow")
    print("=" * 60)
    
    client = LAOSBypassClient()
    
    # Step 1: Health check
    print("\n1️⃣  Health Check")
    print("-" * 40)
    try:
        health = client.health_check()
        print(f"✅ Server Status: {health.get('status', 'unknown')}")
        print(f"   Database: {health.get('database', 'unknown')}")
        print(f"   Redis: {health.get('redis', 'unknown')}")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("   Make sure the backend is running on http://localhost:8000")
        return
    
    # Step 2: List existing documents
    print("\n2️⃣  List Documents")
    print("-" * 40)
    try:
        docs = client.list_documents(limit=5)
        print(f"✅ Found {len(docs.get('items', []))} documents")
        for doc in docs.get('items', [])[:3]:
            print(f"   • {doc['original_filename']} (ID: {doc['id']})")
    except Exception as e:
        print(f"⚠️  Could not list documents: {e}")
    
    # Step 3: Upload document (if you have a sample PDF)
    print("\n3️⃣  Document Upload")
    print("-" * 40)
    sample_pdf = Path("sample_judgment.pdf")
    if sample_pdf.exists():
        try:
            result = client.upload_document(str(sample_pdf))
            doc_id = result.get('document_id')
            print(f"✅ Document uploaded: {doc_id}")
            print(f"   Filename: {result.get('filename')}")
            print(f"   Status: {result.get('status')}")
            
            # Step 4: Check extraction status
            print("\n4️⃣  Check Extraction Status")
            print("-" * 40)
            status = client.get_document_status(doc_id)
            print(f"✅ Processing Status: {status.get('status')}")
            
            # Step 5: Get extracted fields
            print("\n5️⃣  Extracted Fields")
            print("-" * 40)
            try:
                fields = client.get_extracted_fields(doc_id)
                print(f"✅ Extracted {len(fields.get('fields', []))} fields:")
                for field in fields.get('fields', [])[:5]:
                    print(f"   • {field['key']}: {field['value'][:50]}...")
            except Exception as e:
                print(f"⚠️  Fields not ready yet: {e}")
            
            # Step 6: LLM Analysis
            print("\n6️⃣  LLM Analysis")
            print("-" * 40)
            try:
                analysis_prompt = "Summarize the key points of this judgment in 3 bullet points"
                result = client.start_llm_analysis(doc_id, analysis_prompt)
                task_id = result.get('task_id')
                print(f"✅ Analysis started: {task_id}")
                print(f"   Status: {result.get('status')}")
                
                # Try to get result
                try:
                    analysis = client.get_llm_analysis_result(doc_id, task_id)
                    print(f"\n   Result: {analysis.get('result')}")
                except Exception as e:
                    print(f"   Result: {e} (may not be ready yet)")
            except Exception as e:
                print(f"⚠️  LLM Analysis error: {e}")
        
        except Exception as e:
            print(f"❌ Error uploading document: {e}")
    else:
        print("⚠️  No sample PDF found at 'sample_judgment.pdf'")
        print("   Create a test PDF file to try document upload")
    
    print("\n" + "=" * 60)
    print("API Notes:")
    print("=" * 60)
    print("""
✨ Key Features Available (No Auth Required):
   • POST   /api/v1/documents/upload         - Upload PDF
   • GET    /api/v1/documents                - List documents
   • GET    /api/v1/documents/{id}/status    - Check status
   • GET    /api/v1/documents/{id}/extraction - Get extracted content
   • POST   /api/v1/documents/{id}/llm-analysis - Start LLM analysis
   • GET    /api/v1/documents/{id}/review    - Get review results

🔗 OpenAPI Documentation:
   • Swagger UI: {BASE_URL}/docs
   • ReDoc: {BASE_URL}/redoc

📊 System User (Active when AUTH_BYPASS=true):
   • ID: 00000000-0000-0000-0000-000000000001
   • Email: bypass@system.local
   • Role: SUPERADMIN (full access)
   • Name: System Bypass User
""".format(BASE_URL=BASE_URL))


if __name__ == "__main__":
    example_workflow()
