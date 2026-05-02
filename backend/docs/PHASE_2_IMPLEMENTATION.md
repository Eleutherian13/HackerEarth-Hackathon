# PDF Classification & Extraction Pipeline - Implementation Guide

## Overview

This guide documents the Phase 2 implementation of the PDF processing pipeline, which automatically classifies PDFs as text-based or scanned and extracts text accordingly.

## Architecture

```
Upload Document (Phase 1)
    ↓
DocumentPage created (raw storage)
    ↓
[NEW] Celery Task: process_document()
    ├─ Step 1: PDFClassifier.classify_pdf()
    │   └─ Determines: TEXT_BASED | SCANNED | HYBRID
    ├─ Step 2: Extract based on type
    │   ├─ TEXT_BASED → TextExtractor.extract_all_pages()
    │   ├─ SCANNED → PDFClassifier.extract_page_images() → OCRPipeline.process_page_image()
    │   └─ HYBRID → Mix of extraction and OCR
    └─ Step 3: Store results in DocumentPage records
        └─ raw_text (text extraction)
        └─ ocr_text (OCR results)
        └─ extraction_confidence (0.0-1.0)
```

## Services Implemented

### 1. PDFClassifier (`pdf_classifier.py`)

**Purpose**: Determine if PDF is text-based or scanned

**Key Methods**:
- `classify_pdf(file_bytes)` → `(PDFType, page_count, metrics)`
  - Returns classification and detailed metrics
  - PDFType: TEXT_BASED (>70%), SCANNED (<30%), HYBRID (30-70%)

- `extract_page_images(file_bytes, dpi=300)` → `list[(page_num, png_bytes)]`
  - Converts PDF pages to PNG images for OCR processing
  - Configurable DPI for quality/size trade-off

**Thresholds**:
- TEXT_THRESHOLD = 0.7 (70% of pages have extractable text)
- SCANNED_THRESHOLD = 0.3 (30% threshold for scanned)
- MIN_TEXT_CHARS = 50 (minimum chars/page to count as text)

**Metrics Returned**:
```python
{
    "pages_with_text": int,        # Count of pages with extractable text
    "avg_text_per_page": float,    # Average text chars per page
    "text_confidence": float,      # 0.0-1.0 confidence in classification
    "has_images": bool,            # Contains image elements
    "has_embedded_fonts": bool     # Contains embedded fonts
}
```

### 2. TextExtractor (`text_extractor.py`)

**Purpose**: Extract structured text from digital PDFs

**Key Methods**:
- `extract_all_pages(file_bytes)` → `list[PageContent]`
  - Extracts all pages with structure preservation
  - Returns: Page number, raw text, text blocks with bounding boxes

- `extract_structured_text(file_bytes)` → `dict`
  - JSON-serializable structured output
  - Includes: page count, total chars, per-page blocks

- `extract_page_text(file_bytes, page_number)` → `str`
  - Quick plain-text extraction for single page

**Data Structures**:
```python
@dataclass
class TextBlock:
    text: str
    bbox: tuple[float, float, float, float]  # (x0, y0, x1, y1)
    font_size: float
    is_header: bool                          # Detected via font size >= 14pt
    confidence: float                        # 1.0 for extracted text

@dataclass
class PageContent:
    page_number: int
    raw_text: str
    blocks: list[TextBlock]
    page_width: float
    page_height: float
```

### 3. OCRPipeline (`ocr_pipeline.py`)

**Purpose**: OCR for scanned PDFs with dual-engine support

**Key Methods**:
- `process_page_image(image_bytes)` → `OCRResult`
  - Primary: PaddleOCR (supports Chinese + English)
  - Fallback: Tesseract if PaddleOCR unavailable

- `serialize_result(result, page_number)` → `dict`
  - JSON-serializable OCR output

**Features**:
- **Image Preprocessing** (optional, enabled by default):
  - Grayscale conversion
  - Denoising (fastNlMeansDenoising)
  - Adaptive thresholding for contrast
  - Deskewing
  
- **Engine Support**:
  - PaddleOCR: Line and word-level confidence
  - Tesseract: Fallback with OCRTEXT output parsing

- **Confidence Thresholding**:
  - CONFIDENCE_THRESHOLD = 0.7
  - Pages below threshold still extracted but flagged

**Data Structures**:
```python
@dataclass
class OCRWord:
    text: str
    confidence: float        # 0.0-1.0
    bbox: tuple[float, float, float, float]

@dataclass
class OCRLine:
    text: str
    words: list[OCRWord]
    confidence: float
    bbox: tuple[float, float, float, float]

@dataclass
class OCRResult:
    page_number: int
    text: str
    lines: list[OCRLine]
    confidence_score: float  # Average line confidence
    engine: str             # "paddleocr" | "tesseract"
```

### 4. Celery Task (`tasks.py`)

**Purpose**: Orchestrate document processing pipeline

**Key Task**:
- `process_document(document_id)` 
  - Decorated as Celery shared_task
  - Max 3 retries with exponential backoff (60s, 120s, 240s)
  - Creates ProcessingJob record for tracking

**Processing Flow**:
1. Retrieve document from database
2. Download file from storage
3. Classify PDF type (Step 1)
4. Extract based on type (Step 2):
   - TEXT_BASED → `_extract_text_based()`
   - SCANNED → `_extract_scanned()`
   - HYBRID → `_extract_hybrid()`
5. Store results in DocumentPage records (Step 3)
6. Update document status to COMPLETED

**Extraction Helpers**:
- `_extract_text_based()`: Simple text extraction for digital PDFs
- `_extract_scanned()`: OCR all pages with error handling per page
- `_extract_hybrid()`: Prefers extraction, falls back to OCR for image-heavy pages

**Error Handling**:
- Creates ProcessingJob with status tracking
- Logs failures with context
- Retries with exponential backoff on exceptions
- Marks document as FAILED if max retries exceeded

## Data Model Integration

### Document Model Updates

```python
class Document(Base):
    ...
    is_text_based: bool = None      # Determined by classifier
    processing_status: ProcessingStatus  # COMPLETED, FAILED, etc.
    error_message: str = None       # Error details if failed
    ...
```

### DocumentPage Model

```python
class DocumentPage(Base):
    ...
    page_number: int
    raw_text: str = None           # From TextExtractor
    ocr_text: str = None           # From OCRPipeline
    extraction_confidence: float    # 0.0-1.0
    ...
```

### ProcessingJob Model

```python
class ProcessingJob(Base):
    ...
    document_id: UUID
    job_type: JobType              # CLASSIFICATION, EXTRACTION, etc.
    celery_task_id: str
    status: JobStatus              # QUEUED, IN_PROGRESS, COMPLETED, FAILED
    started_at: datetime
    completed_at: datetime = None
    output_summary: dict           # Extraction stats
    error_message: str = None
    ...
```

## Integration with Upload Workflow

### 1. Trigger Processing After Upload

In the upload endpoint (`/api/v1/documents/upload`), after document is stored:

```python
from app.worker.tasks import process_document

# After document is created and stored
document = Document(...)
db.add(document)
db.flush()

# Trigger async processing
process_document.delay(str(document.id))

# Return to user immediately
return {"document_id": str(document.id), "status": "uploaded"}
```

### 2. Track Processing Status

Frontend polls `/api/v1/documents/{document_id}/status`:

```python
@router.get("/{document_id}/status")
async def get_document_status(document_id: str, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == UUID(document_id)).first()
    
    return {
        "document_id": str(document.id),
        "status": document.processing_status,  # UPLOADED, IN_PROGRESS, COMPLETED, FAILED
        "is_text_based": document.is_text_based,
        "error": document.error_message,
        "uploaded_at": document.created_at,
    }
```

### 3. Access Extracted Text

New endpoint to retrieve extracted content:

```python
@router.get("/{document_id}/extract")
async def get_extracted_content(document_id: str, db: Session = Depends(get_db)):
    pages = db.query(DocumentPage).filter(
        DocumentPage.document_id == UUID(document_id)
    ).order_by(DocumentPage.page_number).all()
    
    return {
        "document_id": document_id,
        "pages": [
            {
                "page_number": p.page_number,
                "text": p.raw_text or p.ocr_text,
                "extraction_method": "text" if p.raw_text else "ocr",
                "confidence": p.extraction_confidence,
            }
            for p in pages
        ]
    }
```

## Setup & Configuration

### 1. Environment Variables

```bash
# PDF Processing
PREPROCESS_OCR_IMAGES=true        # Enable image preprocessing
OCR_CONFIDENCE_THRESHOLD=0.7       # Min confidence for flagging
TESSERACT_PATH=/usr/bin/tesseract # Path to Tesseract binary

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
CELERY_TASK_SERIALIZER=json
```

### 2. Install Dependencies

```bash
# Core PDF processing
pip install pymupdf                # PDF reading and conversion
pip install paddleocr              # OCR (recommended)
pip install pytesseract            # OCR fallback
pip install opencv-python          # Image preprocessing
pip install pillow                 # Image handling

# Celery
pip install celery redis           # Task queue

# Optional
apt-get install tesseract-ocr      # System OCR engine
```

### 3. Start Celery Worker

```bash
# Single worker
celery -A app.worker.tasks worker --loglevel=info

# Multiple workers
celery -A app.worker.tasks worker --loglevel=info -c 4

# With task routing
celery -A app.worker.tasks worker -Q document_processing --loglevel=info
```

### 4. Configure Celery in FastAPI

In `app/core/config.py`:

```python
from celery import Celery

def create_celery():
    celery = Celery(
        __name__,
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
    )
    celery.conf.update(
        task_serializer=settings.CELERY_TASK_SERIALIZER,
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_track_started=True,
        task_time_limit=30 * 60,  # 30 minutes max
    )
    return celery

celery_app = create_celery()
```

## Testing

### Unit Tests

Run PDF classifier tests:
```bash
pytest backend/tests/unit/test_pdf_classifier.py -v
pytest backend/tests/unit/test_text_extractor.py -v
pytest backend/tests/unit/test_ocr_pipeline.py -v
```

**Test Fixtures Required**:
- `backend/tests/fixtures/sample_text.pdf` - Digital PDF with extractable text
- `backend/tests/fixtures/sample_scanned.pdf` - Scanned document (image-based)
- `backend/tests/fixtures/sample_hybrid.pdf` - Mixed content PDF

To create test fixtures:
1. Use a real text-based PDF and save as `sample_text.pdf`
2. Scan a document or create image-based PDF and save as `sample_scanned.pdf`
3. Combine both for `sample_hybrid.pdf`

### Integration Tests

Test full processing pipeline:
```python
def test_process_document_text_pdf(sample_text_pdf_bytes):
    """Full pipeline test for text PDF."""
    from app.worker.tasks import process_document
    
    # Create document
    doc = Document(storage_path="test.pdf", file_name="test.pdf")
    db.add(doc)
    db.commit()
    
    # Process
    result = process_document(str(doc.id))
    
    # Verify
    assert result["status"] == "success"
    pages = db.query(DocumentPage).filter(
        DocumentPage.document_id == doc.id
    ).all()
    assert len(pages) > 0
    assert any(p.raw_text for p in pages)
```

## Performance Considerations

### 1. Image DPI Tuning
- 300 DPI: Better quality, larger files (default)
- 150 DPI: Balance quality/speed
- 100 DPI: Faster, good for low-quality source

```python
# In _extract_scanned()
page_images = PDFClassifier.extract_page_images(file_bytes, dpi=150)
```

### 2. Preprocessing Control
```python
# Disable preprocessing for speed
from app.services.ingestion.ocr_pipeline import OCRPipeline
pipeline = OCRPipeline(preprocess=False)
```

### 3. Parallel Processing
Process multiple documents in parallel:
```bash
# 4 concurrent workers
celery -A app.worker.tasks worker --loglevel=info -c 4
```

### 4. Task Monitoring
Monitor queue status:
```python
from celery.result import AsyncResult

# Check task status
result = AsyncResult(task_id)
print(result.status)  # 'PENDING', 'STARTED', 'SUCCESS', 'FAILURE'
print(result.result)  # Task result or exception
```

## Troubleshooting

### Common Issues

**1. "ModuleNotFoundError: No module named 'fitz'"**
- PyMuPDF not installed
- Solution: `pip install pymupdf`

**2. "PaddleOCR not available, falling back to Tesseract"**
- PaddleOCR not installed
- Solution: `pip install paddleocr`
- Or ensure Tesseract is installed: `apt-get install tesseract-ocr`

**3. Celery task not processing**
- Worker not running
- Solution: Start with `celery -A app.worker.tasks worker --loglevel=info`

**4. Redis connection error**
- Redis not running
- Solution: `redis-server` or use Docker

**5. OCR confidence very low**
- Poor image quality
- Solution: Increase DPI in `extract_page_images(dpi=300)`

### Debug Logging

Enable verbose logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("app.services.ingestion")
```

Check logs:
```bash
# View Celery worker logs
celery -A app.worker.tasks worker --loglevel=debug

# View application logs
tail -f var/log/app.log
```

## Next Steps

1. **Create test fixtures** - Use sample PDFs for testing
2. **Run unit tests** - Validate all services
3. **Integrate with upload endpoint** - Trigger processing
4. **Setup Celery workers** - Configure task queue
5. **Monitor processing** - Add dashboard for job status
6. **Optimize performance** - Tune DPI and preprocessing based on workload
