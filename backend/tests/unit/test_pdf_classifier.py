"""Unit tests for PDF classifier."""

import pytest
from app.services.ingestion.pdf_classifier import (
    PDFClassifier,
    PDFClassificationError,
    PDFType,
)


class TestPDFClassifier:
    """Tests for PDFClassifier.classify_pdf()"""

    def test_classify_text_based_pdf(self, sample_text_pdf_bytes):
        """Test classification of digital PDF with extractable text."""
        pdf_type, page_count, metrics = PDFClassifier.classify_pdf(sample_text_pdf_bytes)

        assert pdf_type == PDFType.TEXT_BASED
        assert page_count > 0
        assert metrics["pages_with_text"] > 0
        assert metrics["text_confidence"] >= PDFClassifier.TEXT_THRESHOLD

    def test_classify_scanned_pdf(self, sample_scanned_pdf_bytes):
        """Test classification of scanned PDF (image-based)."""
        pdf_type, page_count, metrics = PDFClassifier.classify_pdf(sample_scanned_pdf_bytes)

        assert pdf_type == PDFType.SCANNED
        assert page_count > 0
        assert metrics["pages_with_text"] <= PDFClassifier.SCANNED_THRESHOLD * page_count
        assert metrics["has_images"] is True

    def test_invalid_pdf_bytes(self):
        """Test error handling for invalid PDF data."""
        invalid_bytes = b"This is not a PDF"

        with pytest.raises(PDFClassificationError):
            PDFClassifier.classify_pdf(invalid_bytes)

    def test_empty_pdf(self):
        """Test error handling for empty PDF."""
        empty_pdf = b"%PDF-1.4\n"

        with pytest.raises(PDFClassificationError):
            PDFClassifier.classify_pdf(empty_pdf)

    def test_metrics_structure(self, sample_text_pdf_bytes):
        """Test that metrics dict has all required fields."""
        _, _, metrics = PDFClassifier.classify_pdf(sample_text_pdf_bytes)

        assert "pages_with_text" in metrics
        assert "avg_text_per_page" in metrics
        assert "text_confidence" in metrics
        assert "has_images" in metrics
        assert "has_embedded_fonts" in metrics

        assert isinstance(metrics["pages_with_text"], int)
        assert isinstance(metrics["avg_text_per_page"], float)
        assert isinstance(metrics["text_confidence"], float)
        assert isinstance(metrics["has_images"], bool)
        assert isinstance(metrics["has_embedded_fonts"], bool)

    def test_text_confidence_in_range(self, sample_text_pdf_bytes):
        """Test that confidence score is between 0 and 1."""
        _, _, metrics = PDFClassifier.classify_pdf(sample_text_pdf_bytes)

        assert 0 <= metrics["text_confidence"] <= 1

    def test_extract_page_images(self, sample_text_pdf_bytes):
        """Test extracting pages as images."""
        page_images = PDFClassifier.extract_page_images(sample_text_pdf_bytes, dpi=300)

        assert len(page_images) > 0
        for page_num, png_bytes in page_images:
            assert isinstance(page_num, int)
            assert page_num > 0
            assert isinstance(png_bytes, bytes)
            assert len(png_bytes) > 0
            assert png_bytes.startswith(b'\x89PNG')  # PNG magic bytes

    def test_extract_page_images_low_dpi(self, sample_text_pdf_bytes):
        """Test extracting pages with lower DPI (smaller files)."""
        page_images_low = PDFClassifier.extract_page_images(
            sample_text_pdf_bytes,
            dpi=150,
        )
        page_images_high = PDFClassifier.extract_page_images(
            sample_text_pdf_bytes,
            dpi=300,
        )

        # Both should have same number of pages
        assert len(page_images_low) == len(page_images_high)

        # High DPI images should be larger
        for (_, bytes_low), (_, bytes_high) in zip(page_images_low, page_images_high):
            assert len(bytes_high) >= len(bytes_low)

    def test_page_count_matches_extraction(self, sample_text_pdf_bytes):
        """Test that page count from classification matches image extraction."""
        _, page_count, _ = PDFClassifier.classify_pdf(sample_text_pdf_bytes)
        page_images = PDFClassifier.extract_page_images(sample_text_pdf_bytes)

        assert len(page_images) == page_count
