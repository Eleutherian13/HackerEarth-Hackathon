"""Text extraction from PDF documents using PyMuPDF."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from tempfile import NamedTemporaryFile
from pathlib import Path
from typing import Any

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class TextBlock:
    """Text block extracted from PDF page."""
    text: str
    bbox: tuple[float, float, float, float]  # (x0, y0, x1, y1)
    font_size: float | None
    is_header: bool = False
    confidence: float = 1.0


@dataclass
class PageContent:
    """Extracted content from a PDF page."""
    page_number: int
    raw_text: str
    blocks: list[TextBlock]
    page_height: float
    page_width: float


class TextExtractionError(Exception):
    """Error during text extraction."""
    pass


class TextExtractor:
    """Extract text from PDF documents while preserving structure."""

    HEADER_FONT_SIZE_THRESHOLD = 14  # Text larger than this is likely a header
    MIN_TEXT_LENGTH = 10              # Minimum characters for a meaningful block

    @staticmethod
    def extract_all_pages(file_bytes: bytes) -> list[PageContent]:
        """
        Extract text from all pages in PDF.

        Args:
            file_bytes: Raw PDF file content

        Returns:
            List of PageContent objects, one per page

        Raises:
            TextExtractionError: If extraction fails
        """
        if not PYMUPDF_AVAILABLE:
            raise TextExtractionError("PyMuPDF not installed")

        try:
            with NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name

            try:
                doc = fitz.open(tmp_path)
                pages = []

                for page_num in range(len(doc)):
                    page_content = TextExtractor._extract_page(doc, page_num)
                    pages.append(page_content)

                doc.close()
                Path(tmp_path).unlink()

                logger.info(
                    "Extracted text from all pages",
                    extra={"page_count": len(pages)},
                )

                return pages

            except Exception as e:
                raise TextExtractionError(f"Error extracting pages: {str(e)}")

        except TextExtractionError:
            raise
        except Exception as e:
            logger.error("Error in extract_all_pages", exc_info=True)
            raise TextExtractionError(f"Unexpected error: {str(e)}")

    @staticmethod
    def _extract_page(doc: Any, page_num: int) -> PageContent:
        """
        Extract text and structure from single page.

        Args:
            doc: Open PyMuPDF document
            page_num: Zero-indexed page number

        Returns:
            PageContent with extracted blocks
        """
        page = doc[page_num]
        page_rect = page.rect
        raw_text = page.get_text()

        # Get detailed text blocks with bounding boxes
        text_dict = page.get_text("dict")
        blocks = []

        if "blocks" in text_dict:
            # Process each block (paragraph, line, etc.)
            for block_data in text_dict["blocks"]:
                if block_data.get("type") == 0:  # Text block
                    TextExtractor._process_text_block(
                        block_data,
                        blocks,
                        page_rect,
                    )

        return PageContent(
            page_number=page_num + 1,
            raw_text=raw_text,
            blocks=blocks,
            page_height=page_rect.height,
            page_width=page_rect.width,
        )

    @staticmethod
    def _process_text_block(
        block_data: dict[str, Any],
        blocks: list[TextBlock],
        page_rect: Any,
    ) -> None:
        """
        Process a text block from PyMuPDF.

        Extracts lines and handles font sizing for header detection.

        Args:
            block_data: Block data from PyMuPDF get_text("dict")
            blocks: List to append extracted blocks to
            page_rect: Page rectangle for sizing context
        """
        for line_data in block_data.get("lines", []):
            for span_data in line_data.get("spans", []):
                text = span_data.get("text", "").strip()

                if len(text) < TextExtractor.MIN_TEXT_LENGTH:
                    continue

                # Extract bounding box
                bbox = (
                    span_data.get("x0", 0),
                    span_data.get("y0", 0),
                    span_data.get("x1", page_rect.width),
                    span_data.get("y1", page_rect.height),
                )

                # Extract font size
                font_size = span_data.get("size")

                # Determine if header based on font size
                is_header = (
                    font_size is not None
                    and font_size >= TextExtractor.HEADER_FONT_SIZE_THRESHOLD
                )

                block = TextBlock(
                    text=text,
                    bbox=bbox,
                    font_size=font_size,
                    is_header=is_header,
                    confidence=1.0,
                )

                blocks.append(block)

    @staticmethod
    def extract_structured_text(file_bytes: bytes) -> dict[str, Any]:
        """
        Extract text with full structural information.

        Returns JSON-serializable dict for storage.

        Args:
            file_bytes: Raw PDF file content

        Returns:
            Dictionary with:
            {
                "pages": [
                    {
                        "page_number": 1,
                        "raw_text": "...",
                        "blocks": [
                            {
                                "text": "...",
                                "bbox": [x0, y0, x1, y1],
                                "font_size": 12.5,
                                "is_header": false,
                                "confidence": 1.0
                            }
                        ],
                        "page_height": 792,
                        "page_width": 612
                    }
                ],
                "total_pages": 10,
                "total_chars": 50000
            }
        """
        pages_data = TextExtractor.extract_all_pages(file_bytes)

        # Convert to serializable format
        pages_json = []
        total_chars = 0

        for page in pages_data:
            total_chars += len(page.raw_text)

            page_json = {
                "page_number": page.page_number,
                "raw_text": page.raw_text,
                "blocks": [
                    {
                        "text": block.text,
                        "bbox": list(block.bbox),
                        "font_size": block.font_size,
                        "is_header": block.is_header,
                        "confidence": block.confidence,
                    }
                    for block in page.blocks
                ],
                "page_height": page.page_height,
                "page_width": page.page_width,
            }

            pages_json.append(page_json)

        return {
            "pages": pages_json,
            "total_pages": len(pages_json),
            "total_chars": total_chars,
        }

    @staticmethod
    def extract_page_text(file_bytes: bytes, page_number: int) -> str:
        """
        Extract plain text from specific page.

        Args:
            file_bytes: Raw PDF file content
            page_number: 1-indexed page number

        Returns:
            Plain text from the page

        Raises:
            TextExtractionError: If page doesn't exist or extraction fails
        """
        if not PYMUPDF_AVAILABLE:
            raise TextExtractionError("PyMuPDF not installed")

        try:
            with NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name

            try:
                doc = fitz.open(tmp_path)

                if page_number < 1 or page_number > len(doc):
                    raise TextExtractionError(
                        f"Page {page_number} not found (document has {len(doc)} pages)"
                    )

                page = doc[page_number - 1]
                text = page.get_text()
                doc.close()
                Path(tmp_path).unlink()

                return text

            except TextExtractionError:
                raise
            except Exception as e:
                raise TextExtractionError(f"Error extracting page: {str(e)}")

        except TextExtractionError:
            raise
        except Exception as e:
            logger.error("Error in extract_page_text", exc_info=True)
            raise TextExtractionError(f"Unexpected error: {str(e)}")
