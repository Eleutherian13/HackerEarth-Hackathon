"""OCR pipeline for scanned PDFs using PaddleOCR or Tesseract fallback."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False

try:
    import pytesseract
    from PIL import Image
    import io
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class OCRWord:
    """Single word detected by OCR."""
    text: str
    confidence: float
    bbox: tuple[float, float, float, float]


@dataclass
class OCRLine:
    """Line of text detected by OCR."""
    text: str
    words: list[OCRWord]
    confidence: float
    bbox: tuple[float, float, float, float]


@dataclass
class OCRResult:
    """OCR result for a single page."""
    page_number: int
    text: str
    lines: list[OCRLine]
    confidence_score: float
    engine: str  # "paddleocr" or "tesseract"


class OCRError(Exception):
    """Error during OCR processing."""
    pass


class OCRPipeline:
    """OCR pipeline with preprocessing and multiple engine support."""

    CONFIDENCE_THRESHOLD = 0.7  # Flag pages with lower average confidence
    PREPROCESS = True            # Enable image preprocessing

    def __init__(self):
        """Initialize OCR engine (PaddleOCR preferred, Tesseract fallback)."""
        self.engine = self._init_engine()

    def _init_engine(self) -> str:
        """Initialize and return name of available OCR engine."""
        if PADDLEOCR_AVAILABLE:
            try:
                self.ocr = PaddleOCR(
                    use_angle_cls=True,
                    lang=['ch', 'en'],  # Support Chinese and English
                    use_gpu=False,       # CPU mode for compatibility
                )
                logger.info("Initialized PaddleOCR engine")
                return "paddleocr"
            except Exception as e:
                logger.warning(f"Failed to initialize PaddleOCR: {e}")

        if TESSERACT_AVAILABLE:
            logger.info("Initialized Tesseract engine")
            return "tesseract"

        raise OCRError(
            "No OCR engine available. Install: pip install paddleocr or pytesseract"
        )

    def process_page_image(self, image_bytes: bytes) -> OCRResult:
        """
        Process page image with OCR.

        Args:
            image_bytes: PNG/JPG image bytes

        Returns:
            OCRResult with extracted text and word-level details

        Raises:
            OCRError: If OCR fails
        """
        try:
            # Load image
            if CV2_AVAILABLE:
                import cv2
                nparr = np.frombuffer(image_bytes, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            else:
                from PIL import Image
                import io
                image = Image.open(io.BytesIO(image_bytes))
                image = np.array(image)

            # Preprocess image if available
            if self.PREPROCESS and CV2_AVAILABLE:
                image = self._preprocess_image(image)

            # Run OCR
            if self.engine == "paddleocr":
                result = self._ocr_paddleocr(image)
            else:
                result = self._ocr_tesseract(image)

            return result

        except OCRError:
            raise
        except Exception as e:
            logger.error("Error in process_page_image", exc_info=True)
            raise OCRError(f"Failed to process image: {str(e)}")

    def _preprocess_image(self, image: Any) -> Any:
        """
        Preprocess image for better OCR.

        - Convert to grayscale
        - Denoise
        - Adaptive thresholding
        - Deskew

        Args:
            image: OpenCV image

        Returns:
            Preprocessed image
        """
        if not CV2_AVAILABLE:
            return image

        try:
            import cv2

            # Grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image

            # Denoise
            denoised = cv2.fastNlMeansDenoising(gray, h=10)

            # Adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                denoised,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                11,
                2,
            )

            logger.debug("Image preprocessed successfully")
            return thresh

        except Exception as e:
            logger.warning(f"Image preprocessing failed: {e}, using original")
            return image

    def _ocr_paddleocr(self, image: Any) -> OCRResult:
        """
        Run OCR using PaddleOCR.

        Args:
            image: OpenCV image

        Returns:
            OCRResult with extracted text

        Raises:
            OCRError: If OCR fails
        """
        try:
            results = self.ocr.ocr(image, cls=True)

            if not results or not results[0]:
                return OCRResult(
                    page_number=0,
                    text="",
                    lines=[],
                    confidence_score=0.0,
                    engine="paddleocr",
                )

            # Parse PaddleOCR results
            lines = []
            full_text_parts = []
            confidences = []

            for line_idx, line_results in enumerate(results[0]):
                words = []
                line_text_parts = []
                line_confidences = []

                for bbox, (text, conf) in enumerate(line_results):
                    # bbox is 4 points, convert to (x0, y0, x1, y1)
                    points = np.array(bbox)
                    x_coords = points[:, 0]
                    y_coords = points[:, 1]
                    bbox_normalized = (
                        float(x_coords.min()),
                        float(y_coords.min()),
                        float(x_coords.max()),
                        float(y_coords.max()),
                    )

                    word = OCRWord(
                        text=text,
                        confidence=float(conf),
                        bbox=bbox_normalized,
                    )
                    words.append(word)
                    line_text_parts.append(text)
                    line_confidences.append(conf)

                line_text = " ".join(line_text_parts)
                line_confidence = sum(line_confidences) / len(line_confidences) if line_confidences else 0

                # Calculate line bbox
                all_points = np.concatenate([np.array(bbox) for bbox, _ in line_results])
                line_bbox = (
                    float(all_points[:, 0].min()),
                    float(all_points[:, 1].min()),
                    float(all_points[:, 0].max()),
                    float(all_points[:, 1].max()),
                )

                line = OCRLine(
                    text=line_text,
                    words=words,
                    confidence=line_confidence,
                    bbox=line_bbox,
                )
                lines.append(line)
                full_text_parts.append(line_text)
                confidences.extend(line_confidences)

            full_text = "\n".join(full_text_parts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0

            return OCRResult(
                page_number=0,
                text=full_text,
                lines=lines,
                confidence_score=float(avg_confidence),
                engine="paddleocr",
            )

        except Exception as e:
            raise OCRError(f"PaddleOCR failed: {str(e)}")

    def _ocr_tesseract(self, image: Any) -> OCRResult:
        """
        Run OCR using Tesseract (fallback).

        Args:
            image: Image object

        Returns:
            OCRResult with extracted text

        Raises:
            OCRError: If OCR fails
        """
        try:
            from PIL import Image
            import pytesseract
            import io

            # Convert to PIL Image if needed
            if not isinstance(image, Image.Image):
                image = Image.fromarray(image)

            # Extract text with detailed data
            text = pytesseract.image_to_string(image, lang='eng')

            # Get detailed results with confidence
            data = pytesseract.image_to_data(
                image,
                output_type=pytesseract.Output.DICT,
                lang='eng',
            )

            # Build line structure
            lines = []
            current_line_words = []
            current_line_num = -1

            for i in range(len(data['text'])):
                if data['text'][i].strip() == '':
                    if current_line_words:
                        line_text = " ".join(w['text'] for w in current_line_words)
                        line_confidence = (
                            sum(w['conf'] for w in current_line_words) /
                            len(current_line_words)
                        ) / 100.0

                        # Calculate bbox
                        xs = [w['x'] for w in current_line_words]
                        ys = [w['y'] for w in current_line_words]
                        ws = [w['width'] for w in current_line_words]
                        hs = [w['height'] for w in current_line_words]

                        bbox = (
                            float(min(xs)),
                            float(min(ys)),
                            float(max(xs) + max(ws)),
                            float(max(ys) + max(hs)),
                        )

                        words = [
                            OCRWord(
                                text=w['text'],
                                confidence=min(1.0, w['conf'] / 100.0),
                                bbox=(
                                    float(w['x']),
                                    float(w['y']),
                                    float(w['x'] + w['width']),
                                    float(w['y'] + w['height']),
                                ),
                            )
                            for w in current_line_words
                        ]

                        line = OCRLine(
                            text=line_text,
                            words=words,
                            confidence=line_confidence,
                            bbox=bbox,
                        )
                        lines.append(line)
                        current_line_words = []
                    current_line_num = -1
                else:
                    line_num = data['block_num'][i]
                    if line_num != current_line_num:
                        if current_line_words:
                            # Process previous line
                            pass
                        current_line_num = line_num

                    current_line_words.append({
                        'text': data['text'][i],
                        'conf': int(data['conf'][i]),
                        'x': int(data['left'][i]),
                        'y': int(data['top'][i]),
                        'width': int(data['width'][i]),
                        'height': int(data['height'][i]),
                    })

            confidences = [word['conf'] / 100.0 for word in current_line_words]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0

            return OCRResult(
                page_number=0,
                text=text,
                lines=lines,
                confidence_score=float(avg_confidence),
                engine="tesseract",
            )

        except Exception as e:
            raise OCRError(f"Tesseract OCR failed: {str(e)}")

    def serialize_result(self, result: OCRResult, page_number: int) -> dict[str, Any]:
        """
        Convert OCRResult to JSON-serializable dict for storage.

        Args:
            result: OCRResult from process_page_image
            page_number: 1-indexed page number

        Returns:
            JSON-serializable dictionary
        """
        return {
            "page_number": page_number,
            "text": result.text,
            "engine": result.engine,
            "confidence_score": result.confidence_score,
            "lines": [
                {
                    "text": line.text,
                    "confidence": line.confidence,
                    "bbox": list(line.bbox),
                    "words": [
                        {
                            "text": word.text,
                            "confidence": word.confidence,
                            "bbox": list(word.bbox),
                        }
                        for word in line.words
                    ],
                }
                for line in result.lines
            ],
        }
