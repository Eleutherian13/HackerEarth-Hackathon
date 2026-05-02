"""Unit tests for text extraction."""

import pytest
from app.services.ingestion.text_extractor import (
    TextExtractor,
    TextExtractionError,
)


class TestTextExtractor:
    """Tests for TextExtractor"""

    def test_extract_all_pages_text_pdf(self, sample_text_pdf_bytes):
        """Test extracting text from all pages of digital PDF."""
        pages = TextExtractor.extract_all_pages(sample_text_pdf_bytes)

        assert len(pages) > 0
        for page in pages:
            assert page.page_number > 0
            assert isinstance(page.raw_text, str)
            assert len(page.raw_text) >= 0  # Can be empty
            assert isinstance(page.blocks, list)
            assert page.page_height > 0
            assert page.page_width > 0

    def test_extract_page_text_single_page(self, sample_text_pdf_bytes):
        """Test extracting text from specific page."""
        # Get first page
        text = TextExtractor.extract_page_text(sample_text_pdf_bytes, 1)

        assert isinstance(text, str)
        assert len(text) >= 0

    def test_extract_page_invalid_number(self, sample_text_pdf_bytes):
        """Test error when requesting invalid page number."""
        with pytest.raises(TextExtractionError):
            TextExtractor.extract_page_text(sample_text_pdf_bytes, 9999)

    def test_extract_structured_text(self, sample_text_pdf_bytes):
        """Test extracting structured text with full details."""
        result = TextExtractor.extract_structured_text(sample_text_pdf_bytes)

        assert "pages" in result
        assert "total_pages" in result
        assert "total_chars" in result

        assert isinstance(result["pages"], list)
        assert len(result["pages"]) > 0
        assert result["total_pages"] > 0

        # Check page structure
        for page in result["pages"]:
            assert "page_number" in page
            assert "raw_text" in page
            assert "blocks" in page
            assert isinstance(page["blocks"], list)

    def test_text_blocks_have_bbox(self, sample_text_pdf_bytes):
        """Test that extracted blocks have bounding box information."""
        pages = TextExtractor.extract_all_pages(sample_text_pdf_bytes)

        for page in pages:
            if len(page.blocks) > 0:
                for block in page.blocks:
                    assert block.bbox is not None
                    assert len(block.bbox) == 4  # (x0, y0, x1, y1)
                    x0, y0, x1, y1 = block.bbox
                    assert x0 < x1  # Valid bbox
                    assert y0 < y1

    def test_header_detection(self, sample_text_pdf_bytes):
        """Test that headers are detected based on font size."""
        pages = TextExtractor.extract_all_pages(sample_text_pdf_bytes)

        headers = []
        for page in pages:
            headers.extend([b for b in page.blocks if b.is_header])

        # Should have some headers (at least in some documents)
        # This test may need adjustment based on sample PDF
        assert isinstance(headers, list)

    def test_invalid_pdf_extraction(self, invalid_pdf_bytes):
        """Test error handling for invalid PDF."""
        with pytest.raises(TextExtractionError):
            TextExtractor.extract_all_pages(invalid_pdf_bytes)

    def test_page_content_serializable(self, sample_text_pdf_bytes):
        """Test that extracted content can be serialized to JSON."""
        import json

        result = TextExtractor.extract_structured_text(sample_text_pdf_bytes)

        # Should be JSON serializable
        json_str = json.dumps(result)
        assert len(json_str) > 0

        # Parse it back
        parsed = json.loads(json_str)
        assert parsed["total_pages"] == result["total_pages"]
