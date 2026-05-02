"""PDF document classification - determines if text-based or scanned."""

from __future__ import annotations

import logging
from enum import Enum
from pathlib import Path
from tempfile import NamedTemporaryFile

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

logger = logging.getLogger(__name__)


class PDFType(str, Enum):
    """Classification of PDF document type."""
    TEXT_BASED = "TEXT_BASED"      # Digital PDF with extractable text
    SCANNED = "SCANNED"            # Scanned image-based PDF
    HYBRID = "HYBRID"              # Mix of text and images


class PDFClassificationError(Exception):
    """Error during PDF classification."""
    pass


class PDFClassifier:
    """Classify PDF documents as text-based, scanned, or hybrid."""

    TEXT_THRESHOLD = 0.7           # >70% pages with text = TEXT_BASED
    SCANNED_THRESHOLD = 0.3        # <30% pages with text = SCANNED
    MIN_TEXT_CHARS = 50            # Minimum characters per page to count as "has text"

    @staticmethod
    def classify_pdf(file_bytes: bytes) -> tuple[PDFType, int, dict]:
        """
        Classify PDF document type.

        Args:
            file_bytes: Raw PDF file content

        Returns:
            Tuple of (pdf_type, page_count, metrics)
            where metrics = {
                "pages_with_text": int,
                "avg_text_per_page": float,
                "text_confidence": float,  # 0-1, how confident in classification
                "has_images": bool,
                "has_embedded_fonts": bool,
            }

        Raises:
            PDFClassificationError: If PDF cannot be classified
        """
        if not PYMUPDF_AVAILABLE:
            raise PDFClassificationError(
                "PyMuPDF not installed. Install with: pip install pymupdf"
            )

        try:
            # Open PDF from bytes
            with NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name

            try:
                doc = fitz.open(tmp_path)
                page_count = len(doc)

                if page_count == 0:
                    raise PDFClassificationError("PDF has no pages")

                # Analyze each page
                pages_with_text = 0
                total_text_length = 0
                has_images = False
                has_embedded_fonts = False

                for page_num in range(page_count):
                    page = doc[page_num]

                    # Check for text
                    text = page.get_text()
                    text_length = len(text.strip())
                    if text_length >= PDFClassifier.MIN_TEXT_CHARS:
                        pages_with_text += 1
                    total_text_length += text_length

                    # Check for images
                    image_list = page.get_images()
                    if image_list:
                        has_images = True

                    # Check for embedded fonts
                    if page.get_fonts():
                        has_embedded_fonts = True

                doc.close()
                Path(tmp_path).unlink()

                # Calculate metrics
                text_ratio = pages_with_text / page_count
                avg_text_per_page = total_text_length / page_count if page_count > 0 else 0

                # Classify based on thresholds
                if text_ratio >= PDFClassifier.TEXT_THRESHOLD:
                    pdf_type = PDFType.TEXT_BASED
                    confidence = min(text_ratio, 1.0)
                elif text_ratio <= PDFClassifier.SCANNED_THRESHOLD:
                    pdf_type = PDFType.SCANNED
                    confidence = 1.0 - text_ratio  # Higher confidence if very few pages have text
                else:
                    pdf_type = PDFType.HYBRID
                    confidence = 0.5  # Lower confidence for mixed documents

                metrics = {
                    "pages_with_text": pages_with_text,
                    "avg_text_per_page": round(avg_text_per_page, 2),
                    "text_confidence": round(confidence, 2),
                    "has_images": has_images,
                    "has_embedded_fonts": has_embedded_fonts,
                }

                logger.info(
                    "PDF classified",
                    extra={
                        "pdf_type": pdf_type.value,
                        "page_count": page_count,
                        "pages_with_text": pages_with_text,
                        "confidence": confidence,
                    },
                )

                return pdf_type, page_count, metrics

            except fitz.FileError as e:
                raise PDFClassificationError(f"Cannot open PDF: {str(e)}")
            except Exception as e:
                raise PDFClassificationError(f"Error analyzing PDF: {str(e)}")

        except PDFClassificationError:
            raise
        except Exception as e:
            logger.error(
                "Unexpected error during PDF classification",
                exc_info=True,
            )
            raise PDFClassificationError(f"Unexpected error: {str(e)}")

    @staticmethod
    def extract_page_images(file_bytes: bytes, dpi: int = 300) -> list[tuple[int, bytes]]:
        """
        Extract individual pages as PNG images.

        Used for OCR pipeline on scanned/hybrid documents.

        Args:
            file_bytes: Raw PDF file content
            dpi: Resolution in DPI (default 300 for OCR)

        Returns:
            List of (page_number, png_bytes) tuples

        Raises:
            PDFClassificationError: If images cannot be extracted
        """
        if not PYMUPDF_AVAILABLE:
            raise PDFClassificationError("PyMuPDF not installed")

        try:
            with NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name

            try:
                doc = fitz.open(tmp_path)
                page_images = []

                for page_num in range(len(doc)):
                    page = doc[page_num]

                    # Render page at high DPI
                    zoom = dpi / 72  # DPI to zoom factor
                    mat = fitz.Matrix(zoom, zoom)
                    pix = page.get_pixmap(matrix=mat, alpha=False)

                    # Convert to PNG
                    png_bytes = pix.tobytes("png")
                    page_images.append((page_num + 1, png_bytes))

                doc.close()
                Path(tmp_path).unlink()

                logger.info(
                    "Extracted page images",
                    extra={"page_count": len(page_images), "dpi": dpi},
                )

                return page_images

            except Exception as e:
                raise PDFClassificationError(f"Error extracting pages: {str(e)}")

        except PDFClassificationError:
            raise
        except Exception as e:
            logger.error("Error in extract_page_images", exc_info=True)
            raise PDFClassificationError(f"Unexpected error: {str(e)}")
