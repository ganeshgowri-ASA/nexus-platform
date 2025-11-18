"""
Text Extraction Module

Extract text with position, font, size information. Support structured data extraction.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import re
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class TextBlock:
    """Represents a text block with metadata"""
    text: str
    bbox: Tuple[int, int, int, int]
    confidence: float
    font_size: Optional[float] = None
    font_family: Optional[str] = None
    is_bold: bool = False
    is_italic: bool = False
    line_number: Optional[int] = None
    block_number: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TextExtractor:
    """Extract text with detailed metadata"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.TextExtractor")

    def extract(
        self,
        ocr_result: Any,
        preserve_formatting: bool = True
    ) -> List[TextBlock]:
        """
        Extract text blocks from OCR result

        Args:
            ocr_result: OCR engine result
            preserve_formatting: Preserve text formatting

        Returns:
            List of text blocks with metadata
        """
        try:
            text_blocks = []

            # Extract from OCR result structure
            if hasattr(ocr_result, 'blocks'):
                for i, block in enumerate(ocr_result.blocks):
                    text_blocks.append(TextBlock(
                        text=block.get('text', ''),
                        bbox=self._extract_bbox(block),
                        confidence=block.get('confidence', 0.0),
                        block_number=i
                    ))
            elif hasattr(ocr_result, 'lines'):
                for i, line in enumerate(ocr_result.lines):
                    text_blocks.append(TextBlock(
                        text=line.get('text', ''),
                        bbox=self._extract_bbox(line),
                        confidence=line.get('confidence', 0.0),
                        line_number=i
                    ))

            self.logger.info(f"Extracted {len(text_blocks)} text blocks")
            return text_blocks

        except Exception as e:
            self.logger.error(f"Error extracting text: {e}")
            return []

    def _extract_bbox(self, element: Dict[str, Any]) -> Tuple[int, int, int, int]:
        """Extract bounding box from element"""
        if 'bbox' in element:
            bbox = element['bbox']
            if isinstance(bbox, dict):
                return (
                    bbox.get('x', 0),
                    bbox.get('y', 0),
                    bbox.get('width', 0),
                    bbox.get('height', 0)
                )
            return tuple(bbox)
        return (0, 0, 0, 0)

    def extract_structured(
        self,
        text_blocks: List[TextBlock]
    ) -> Dict[str, Any]:
        """
        Extract structured data from text blocks

        Args:
            text_blocks: List of text blocks

        Returns:
            Structured data dictionary
        """
        try:
            structured = {
                'paragraphs': [],
                'headings': [],
                'lists': [],
                'metadata': {}
            }

            # Group blocks into paragraphs
            current_paragraph = []
            for block in text_blocks:
                if block.text.strip():
                    current_paragraph.append(block.text)
                elif current_paragraph:
                    structured['paragraphs'].append(' '.join(current_paragraph))
                    current_paragraph = []

            if current_paragraph:
                structured['paragraphs'].append(' '.join(current_paragraph))

            # Detect headings (simple heuristic: short lines with high y-position change)
            for i, block in enumerate(text_blocks):
                if len(block.text.strip()) < 100 and block.text.strip().isupper():
                    structured['headings'].append(block.text.strip())

            return structured

        except Exception as e:
            self.logger.error(f"Error extracting structured data: {e}")
            return {}


class StructuredExtractor:
    """Extract structured data like forms, invoices, receipts"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.StructuredExtractor")

    def extract_key_value_pairs(self, text: str) -> Dict[str, str]:
        """
        Extract key-value pairs from text

        Args:
            text: Input text

        Returns:
            Dictionary of key-value pairs
        """
        try:
            pairs = {}
            lines = text.split('\n')

            for line in lines:
                # Look for patterns like "Key: Value" or "Key = Value"
                match = re.match(r'^([^:=]+)[:=]\s*(.+)$', line.strip())
                if match:
                    key = match.group(1).strip()
                    value = match.group(2).strip()
                    pairs[key] = value

            self.logger.info(f"Extracted {len(pairs)} key-value pairs")
            return pairs

        except Exception as e:
            self.logger.error(f"Error extracting key-value pairs: {e}")
            return {}

    def extract_dates(self, text: str) -> List[str]:
        """Extract dates from text"""
        try:
            # Common date patterns
            patterns = [
                r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}',  # DD/MM/YYYY or MM/DD/YYYY
                r'\d{4}[-/]\d{1,2}[-/]\d{1,2}',    # YYYY/MM/DD
                r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b',
            ]

            dates = []
            for pattern in patterns:
                dates.extend(re.findall(pattern, text, re.IGNORECASE))

            return dates

        except Exception as e:
            self.logger.error(f"Error extracting dates: {e}")
            return []

    def extract_amounts(self, text: str) -> List[float]:
        """Extract monetary amounts from text"""
        try:
            # Pattern for currency amounts
            pattern = r'[$€£¥]\s*[\d,]+\.?\d*|\d+\.?\d*\s*(?:USD|EUR|GBP|JPY)'
            matches = re.findall(pattern, text)

            amounts = []
            for match in matches:
                # Extract numeric value
                numeric = re.findall(r'[\d,.]+', match)[0]
                numeric = numeric.replace(',', '')
                try:
                    amounts.append(float(numeric))
                except ValueError:
                    pass

            return amounts

        except Exception as e:
            self.logger.error(f"Error extracting amounts: {e}")
            return []

    def extract_emails(self, text: str) -> List[str]:
        """Extract email addresses from text"""
        try:
            pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            return re.findall(pattern, text)
        except Exception as e:
            self.logger.error(f"Error extracting emails: {e}")
            return []

    def extract_phone_numbers(self, text: str) -> List[str]:
        """Extract phone numbers from text"""
        try:
            # Various phone number patterns
            patterns = [
                r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
                r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            ]

            phones = []
            for pattern in patterns:
                phones.extend(re.findall(pattern, text))

            return phones

        except Exception as e:
            self.logger.error(f"Error extracting phone numbers: {e}")
            return []


class FormExtractor:
    """Extract data from forms"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.FormExtractor")

    def extract_form_fields(
        self,
        text_blocks: List[TextBlock]
    ) -> Dict[str, Any]:
        """
        Extract form fields and their values

        Args:
            text_blocks: List of text blocks

        Returns:
            Dictionary of form fields
        """
        try:
            form_data = {}

            # Look for label-value patterns based on spatial proximity
            for i, block in enumerate(text_blocks):
                text = block.text.strip()

                # Check if this looks like a label (ends with :)
                if text.endswith(':'):
                    label = text[:-1].strip()

                    # Look for value in next block or same line
                    if i + 1 < len(text_blocks):
                        next_block = text_blocks[i + 1]

                        # Check if next block is close horizontally or vertically
                        if self._are_blocks_close(block, next_block):
                            form_data[label] = next_block.text.strip()

            self.logger.info(f"Extracted {len(form_data)} form fields")
            return form_data

        except Exception as e:
            self.logger.error(f"Error extracting form fields: {e}")
            return {}

    def _are_blocks_close(
        self,
        block1: TextBlock,
        block2: TextBlock,
        threshold: int = 50
    ) -> bool:
        """Check if two blocks are spatially close"""
        x1, y1, w1, h1 = block1.bbox
        x2, y2, w2, h2 = block2.bbox

        # Check horizontal proximity (same line)
        if abs(y1 - y2) < h1:
            return abs(x2 - (x1 + w1)) < threshold

        # Check vertical proximity (below)
        if abs(x1 - x2) < w1:
            return abs(y2 - (y1 + h1)) < threshold

        return False

    def detect_checkboxes(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect checkboxes in form

        Args:
            image: Input image

        Returns:
            List of checkbox detections
        """
        try:
            import cv2

            checkboxes = []

            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()

            # Detect small squares (potential checkboxes)
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            contours, _ = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)

                # Check if it's approximately square and reasonable size
                aspect_ratio = float(w) / h if h > 0 else 0
                if 10 < w < 50 and 10 < h < 50 and 0.8 < aspect_ratio < 1.2:
                    # Check if it's filled (checked)
                    roi = binary[y:y+h, x:x+w]
                    fill_ratio = np.sum(roi > 0) / (w * h) if w * h > 0 else 0

                    checkboxes.append({
                        'bbox': (x, y, w, h),
                        'checked': fill_ratio > 0.3,
                        'confidence': 0.7
                    })

            self.logger.info(f"Detected {len(checkboxes)} checkboxes")
            return checkboxes

        except Exception as e:
            self.logger.error(f"Error detecting checkboxes: {e}")
            return []
