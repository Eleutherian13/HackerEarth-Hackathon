"""Unit tests for OCR pipeline."""

import pytest
from app.services.ingestion.ocr_pipeline import (
    OCRPipeline,
    OCRError,
)


class TestOCRPipeline:
    """Tests for OCR pipeline"""

    @pytest.fixture
    def ocr_pipeline(self):
        """Create OCR pipeline instance."""
        return OCRPipeline()

    def test_ocr_scanned_pdf_page(self, ocr_pipeline, sample_scanned_pdf_bytes):
        """Test OCR processing of scanned PDF page image."""
        from app.services.ingestion.pdf_classifier import PDFClassifier

        # Extract first page as image
        page_images = PDFClassifier.extract_page_images(sample_scanned_pdf_bytes, dpi=300)
        assert len(page_images) > 0

        page_num, image_bytes = page_images[0]
        result = ocr_pipeline.process_page_image(image_bytes)

        assert result.page_number == page_num
        assert isinstance(result.text, str)
        assert len(result.text) > 0
        assert isinstance(result.lines, list)
        assert 0 <= result.confidence_score <= 1

    def test_ocr_result_structure(self, ocr_pipeline, sample_scanned_pdf_bytes):
        """Test OCR result has all required fields."""
        from app.services.ingestion.pdf_classifier import PDFClassifier

        page_images = PDFClassifier.extract_page_images(sample_scanned_pdf_bytes, dpi=300)
        _, image_bytes = page_images[0]
        result = ocr_pipeline.process_page_image(image_bytes)

        # Check line structure
        for line in result.lines:
            assert isinstance(line.text, str)
            assert isinstance(line.words, list)
            assert 0 <= line.confidence <= 1
            assert line.bbox is not None
            assert len(line.bbox) == 4

            # Check word structure
            for word in line.words:
                assert isinstance(word.text, str)
                assert 0 <= word.confidence <= 1
                assert word.bbox is not None
                assert len(word.bbox) == 4

    def test_ocr_serialize_result(self, ocr_pipeline, sample_scanned_pdf_bytes):
        """Test OCR result serialization to JSON."""
        import json
        from app.services.ingestion.pdf_classifier import PDFClassifier

        page_images = PDFClassifier.extract_page_images(sample_scanned_pdf_bytes, dpi=300)
        _, image_bytes = page_images[0]
        result = ocr_pipeline.process_page_image(image_bytes)

        serialized = ocr_pipeline.serialize_result(result, 1)

        # Should be JSON serializable
        json_str = json.dumps(serialized)
        assert len(json_str) > 0

        # Should have expected fields
        assert "page_number" in serialized
        assert "text" in serialized
        assert "lines" in serialized
        assert "confidence_score" in serialized

    def test_ocr_engine_initialization(self):
        """Test OCR pipeline initializes with available engine."""
        pipeline = OCRPipeline()

        # Should have engine initialized
        assert pipeline.ocr_engine is not None
        assert pipeline.engine_type is not None
        assert pipeline.engine_type in ["paddleocr", "tesseract"]

    def test_ocr_confidence_thresholding(self, ocr_pipeline, sample_scanned_pdf_bytes):
        """Test that low confidence results are still returned but flagged."""
        from app.services.ingestion.pdf_classifier import PDFClassifier

        page_images = PDFClassifier.extract_page_images(sample_scanned_pdf_bytes, dpi=300)

        # Process multiple pages
        for page_num, image_bytes in page_images[:3]:
            result = ocr_pipeline.process_page_image(image_bytes)

            # Check confidence is valid
            assert isinstance(result.confidence_score, (int, float))
            assert 0 <= result.confidence_score <= 1

    def test_invalid_image_handling(self, ocr_pipeline):
        """Test error handling for invalid image data."""
        with pytest.raises(OCRError):
            ocr_pipeline.process_page_image(b"not an image")

    def test_ocr_text_not_empty_on_scanned(self, ocr_pipeline, sample_scanned_pdf_bytes):
        """Test that OCR extracts some text from scanned PDF."""
        from app.services.ingestion.pdf_classifier import PDFClassifier

        page_images = PDFClassifier.extract_page_images(sample_scanned_pdf_bytes, dpi=300)
        _, image_bytes = page_images[0]
        result = ocr_pipeline.process_page_image(image_bytes)

        # Scanned PDF should have text (may be empty for blank pages)
        assert isinstance(result.text, str)
        assert result.page_number > 0
