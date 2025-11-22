"""OCR processing logic with support for multiple engines"""
import time
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image
import pytesseract
import cv2
import numpy as np
from pathlib import Path
import io
import json

from app.core.config import settings
from app.core.logging import get_logger
from app.utils.exceptions import OCRProcessingError, APIKeyMissingError
from app.modules.ocr.utils import preprocess_image, is_handwriting

logger = get_logger(__name__)


class OCRProcessor:
    """Main OCR processing class supporting multiple engines"""

    def __init__(self, engine: str = "tesseract"):
        self.engine = engine
        self._setup_engine()

    def _setup_engine(self):
        """Setup OCR engine"""
        if self.engine == "tesseract":
            # Set Tesseract command path if configured
            if settings.TESSERACT_CMD:
                pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
        elif self.engine == "google_vision":
            if not settings.GOOGLE_CLOUD_API_KEY:
                raise APIKeyMissingError("Google Cloud API key is required")
        elif self.engine == "aws_textract":
            if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY:
                raise APIKeyMissingError("AWS credentials are required")

    async def extract_text(
        self,
        image_path: str,
        detect_language: bool = True,
        extract_tables: bool = True,
        detect_handwriting: bool = True,
        analyze_layout: bool = True
    ) -> Dict[str, Any]:
        """Extract text from image using configured OCR engine"""
        start_time = time.time()

        try:
            # Load image
            image = Image.open(image_path)
            image = preprocess_image(image)

            # Extract text based on engine
            if self.engine == "tesseract":
                result = await self._extract_with_tesseract(
                    image, detect_language, extract_tables, detect_handwriting, analyze_layout
                )
            elif self.engine == "google_vision":
                result = await self._extract_with_google_vision(
                    image, detect_language, extract_tables, detect_handwriting, analyze_layout
                )
            elif self.engine == "aws_textract":
                result = await self._extract_with_aws_textract(
                    image_path, detect_language, extract_tables, detect_handwriting, analyze_layout
                )
            else:
                raise OCRProcessingError(f"Unsupported OCR engine: {self.engine}")

            # Calculate processing time
            processing_time = time.time() - start_time
            result["processing_time"] = processing_time

            return result

        except Exception as e:
            logger.error(f"OCR processing error: {e}", exc_info=True)
            raise OCRProcessingError(f"Failed to extract text: {str(e)}")

    async def _extract_with_tesseract(
        self,
        image: Image.Image,
        detect_language: bool,
        extract_tables: bool,
        detect_handwriting: bool,
        analyze_layout: bool
    ) -> Dict[str, Any]:
        """Extract text using Tesseract OCR"""
        result = {
            "extracted_text": "",
            "confidence_score": 0.0,
            "detected_language": None,
            "languages": [],
            "handwriting_detected": False,
            "tables_detected": 0,
            "table_data": [],
            "layout_analysis": None
        }

        try:
            # Convert PIL Image to numpy array for OpenCV
            img_array = np.array(image)

            # Detect language
            if detect_language:
                try:
                    lang_data = pytesseract.image_to_osd(image)
                    # Parse OSD output to get language
                    for line in lang_data.split('\n'):
                        if 'Script:' in line:
                            script = line.split(':')[1].strip()
                            result["detected_language"] = script.lower()[:2]
                            result["languages"] = [{"language": script, "confidence": 0.9}]
                except Exception as e:
                    logger.warning(f"Language detection failed: {e}")
                    result["detected_language"] = "en"

            # Extract text with confidence
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            text = pytesseract.image_to_string(image)
            result["extracted_text"] = text.strip()

            # Calculate average confidence
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            if confidences:
                result["confidence_score"] = sum(confidences) / len(confidences) / 100.0

            # Detect handwriting (simple heuristic)
            if detect_handwriting:
                result["handwriting_detected"] = is_handwriting(
                    text, result["confidence_score"]
                )

            # Extract tables
            if extract_tables:
                tables = await self._detect_tables_tesseract(img_array)
                result["tables_detected"] = len(tables)
                result["table_data"] = tables

            # Layout analysis
            if analyze_layout:
                result["layout_analysis"] = self._analyze_layout_tesseract(data)

            return result

        except Exception as e:
            logger.error(f"Tesseract OCR error: {e}", exc_info=True)
            raise OCRProcessingError(f"Tesseract processing failed: {str(e)}")

    async def _extract_with_google_vision(
        self,
        image: Image.Image,
        detect_language: bool,
        extract_tables: bool,
        detect_handwriting: bool,
        analyze_layout: bool
    ) -> Dict[str, Any]:
        """Extract text using Google Cloud Vision API"""
        # This is a placeholder for Google Vision API integration
        # In production, you would use the actual Google Cloud Vision client

        result = {
            "extracted_text": "",
            "confidence_score": 0.0,
            "detected_language": None,
            "languages": [],
            "handwriting_detected": False,
            "tables_detected": 0,
            "table_data": [],
            "layout_analysis": None
        }

        try:
            # Placeholder: Would use Google Cloud Vision API here
            # from google.cloud import vision
            # client = vision.ImageAnnotatorClient()

            logger.warning("Google Vision API integration not fully implemented. Using Tesseract fallback.")
            return await self._extract_with_tesseract(
                image, detect_language, extract_tables, detect_handwriting, analyze_layout
            )

        except Exception as e:
            logger.error(f"Google Vision error: {e}", exc_info=True)
            raise OCRProcessingError(f"Google Vision processing failed: {str(e)}")

    async def _extract_with_aws_textract(
        self,
        image_path: str,
        detect_language: bool,
        extract_tables: bool,
        detect_handwriting: bool,
        analyze_layout: bool
    ) -> Dict[str, Any]:
        """Extract text using AWS Textract"""
        # This is a placeholder for AWS Textract integration

        result = {
            "extracted_text": "",
            "confidence_score": 0.0,
            "detected_language": None,
            "languages": [],
            "handwriting_detected": False,
            "tables_detected": 0,
            "table_data": [],
            "layout_analysis": None
        }

        try:
            # Placeholder: Would use boto3 and AWS Textract here
            # import boto3
            # textract = boto3.client('textract')

            logger.warning("AWS Textract integration not fully implemented. Using Tesseract fallback.")
            image = Image.open(image_path)
            return await self._extract_with_tesseract(
                image, detect_language, extract_tables, detect_handwriting, analyze_layout
            )

        except Exception as e:
            logger.error(f"AWS Textract error: {e}", exc_info=True)
            raise OCRProcessingError(f"AWS Textract processing failed: {str(e)}")

    async def _detect_tables_tesseract(self, img_array: np.ndarray) -> List[Dict[str, Any]]:
        """Detect and extract tables from image"""
        tables = []

        try:
            # Convert to grayscale
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

            # Apply threshold
            thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

            # Detect horizontal and vertical lines
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))

            horizontal_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
            vertical_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vertical_kernel, iterations=2)

            # Combine lines
            table_structure = cv2.addWeighted(horizontal_lines, 0.5, vertical_lines, 0.5, 0.0)

            # Find contours
            contours, _ = cv2.findContours(table_structure, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

            # Filter for table-like contours
            for idx, contour in enumerate(contours):
                x, y, w, h = cv2.boundingRect(contour)
                if w > 100 and h > 100:  # Minimum table size
                    tables.append({
                        "table_index": idx,
                        "x": int(x),
                        "y": int(y),
                        "width": int(w),
                        "height": int(h),
                        "rows": 0,  # Would need more sophisticated detection
                        "columns": 0,
                        "data": []  # Would extract cell data
                    })

        except Exception as e:
            logger.error(f"Table detection error: {e}", exc_info=True)

        return tables

    def _analyze_layout_tesseract(self, data: Dict[str, List]) -> Dict[str, Any]:
        """Analyze document layout"""
        layout = {
            "blocks": [],
            "paragraphs": [],
            "lines": len([x for x in data['text'] if x.strip()]),
            "words": len([x for x in data['text'] if x.strip()]),
            "text_regions": []
        }

        try:
            # Group text by blocks
            current_block = None
            for i in range(len(data['text'])):
                if int(data['conf'][i]) > 0:
                    block_num = data['block_num'][i]
                    if current_block != block_num:
                        current_block = block_num
                        layout["blocks"].append({
                            "block_num": block_num,
                            "left": int(data['left'][i]),
                            "top": int(data['top'][i]),
                            "width": int(data['width'][i]),
                            "height": int(data['height'][i])
                        })

        except Exception as e:
            logger.error(f"Layout analysis error: {e}", exc_info=True)

        return layout

    async def extract_from_pdf(
        self,
        pdf_path: str,
        detect_language: bool = True,
        extract_tables: bool = True,
        detect_handwriting: bool = True,
        analyze_layout: bool = True
    ) -> List[Dict[str, Any]]:
        """Extract text from all pages of a PDF"""
        from pdf2image import convert_from_path

        results = []

        try:
            # Convert PDF pages to images
            images = convert_from_path(pdf_path)

            for page_num, image in enumerate(images, 1):
                logger.info(f"Processing PDF page {page_num}/{len(images)}")

                # Save temporary image
                temp_path = f"/tmp/page_{page_num}.png"
                image.save(temp_path)

                # Extract text from page
                page_result = await self.extract_text(
                    temp_path, detect_language, extract_tables,
                    detect_handwriting, analyze_layout
                )
                page_result["page_number"] = page_num

                results.append(page_result)

            return results

        except Exception as e:
            logger.error(f"PDF processing error: {e}", exc_info=True)
            raise OCRProcessingError(f"Failed to process PDF: {str(e)}")
