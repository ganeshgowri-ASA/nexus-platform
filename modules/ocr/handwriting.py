"""
Handwriting Recognition Module

Support handwritten text recognition and signature detection.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import cv2

logger = logging.getLogger(__name__)


class HandwritingRecognizer:
    """Recognize handwritten text"""

    def __init__(self, ocr_engine=None):
        self.ocr_engine = ocr_engine
        self.logger = logging.getLogger(f"{__name__}.HandwritingRecognizer")

    def recognize_handwriting(
        self,
        image: np.ndarray,
        language: str = "eng"
    ) -> Dict[str, Any]:
        """
        Recognize handwritten text in image

        Args:
            image: Input image
            language: Language code

        Returns:
            Recognition result with text and confidence
        """
        try:
            # Preprocess for handwriting
            preprocessed = self._preprocess_handwriting(image)

            # Use OCR engine if available
            if self.ocr_engine:
                result = self.ocr_engine.process_image(preprocessed, language)
                return {
                    'text': result.text,
                    'confidence': result.confidence,
                    'words': result.words,
                }
            else:
                self.logger.warning("No OCR engine available")
                return {
                    'text': '',
                    'confidence': 0.0,
                    'words': [],
                }

        except Exception as e:
            self.logger.error(f"Error recognizing handwriting: {e}")
            return {
                'text': '',
                'confidence': 0.0,
                'words': [],
            }

    def _preprocess_handwriting(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for handwriting recognition

        Args:
            image: Input image

        Returns:
            Preprocessed image
        """
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()

            # Normalize intensity
            normalized = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)

            # Apply bilateral filter for edge preservation
            filtered = cv2.bilateralFilter(normalized, 9, 75, 75)

            # Adaptive thresholding
            binary = cv2.adaptiveThreshold(
                filtered,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                11,
                2
            )

            return binary

        except Exception as e:
            self.logger.error(f"Error preprocessing handwriting: {e}")
            return image

    def detect_handwriting_regions(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect regions containing handwriting

        Args:
            image: Input image

        Returns:
            List of bounding boxes (x, y, width, height)
        """
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()

            # Threshold
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

            # Find contours
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Filter and return bounding boxes
            regions = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)

                # Filter by size
                if w > 20 and h > 10:
                    regions.append((x, y, w, h))

            self.logger.info(f"Detected {len(regions)} handwriting regions")
            return regions

        except Exception as e:
            self.logger.error(f"Error detecting handwriting regions: {e}")
            return []

    def is_handwritten(self, image: np.ndarray) -> Tuple[bool, float]:
        """
        Detect if image contains handwritten text

        Args:
            image: Input image

        Returns:
            (is_handwritten, confidence)
        """
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()

            # Calculate features
            # 1. Stroke width variation (handwriting has more variation)
            edges = cv2.Canny(gray, 50, 150)
            stroke_variation = np.std(edges[edges > 0]) if np.any(edges > 0) else 0

            # 2. Text line straightness (printed text is straighter)
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            straightness_scores = []
            for contour in contours:
                if len(contour) >= 5:
                    ellipse = cv2.fitEllipse(contour)
                    straightness_scores.append(ellipse[1][0] / ellipse[1][1] if ellipse[1][1] > 0 else 0)

            avg_straightness = np.mean(straightness_scores) if straightness_scores else 0

            # Simple heuristic
            is_handwritten = stroke_variation > 20 or avg_straightness < 3
            confidence = min(stroke_variation / 50, 1.0)

            return is_handwritten, confidence

        except Exception as e:
            self.logger.error(f"Error detecting handwriting: {e}")
            return False, 0.0


class SignatureDetection:
    """Detect and extract signatures from documents"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.SignatureDetection")

    def detect_signatures(
        self,
        image: np.ndarray,
        min_area: int = 1000,
        max_area: int = 50000
    ) -> List[Dict[str, Any]]:
        """
        Detect signature regions in document

        Args:
            image: Input image
            min_area: Minimum signature area
            max_area: Maximum signature area

        Returns:
            List of signature detections
        """
        try:
            signatures = []

            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()

            # Threshold
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

            # Find contours
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for contour in contours:
                area = cv2.contourArea(contour)

                # Filter by area
                if min_area < area < max_area:
                    x, y, w, h = cv2.boundingRect(contour)

                    # Check if it looks like a signature
                    # Signatures typically have: irregular shape, medium size, cursive strokes
                    if self._is_signature_like(binary[y:y+h, x:x+w]):
                        signatures.append({
                            'bbox': (x, y, w, h),
                            'area': area,
                            'confidence': 0.7,  # Basic confidence
                        })

            self.logger.info(f"Detected {len(signatures)} potential signatures")
            return signatures

        except Exception as e:
            self.logger.error(f"Error detecting signatures: {e}")
            return []

    def _is_signature_like(self, roi: np.ndarray) -> bool:
        """
        Check if region looks like a signature

        Args:
            roi: Region of interest

        Returns:
            Whether it looks like a signature
        """
        try:
            # Calculate density (signatures are usually not too dense)
            density = np.sum(roi > 0) / (roi.shape[0] * roi.shape[1])
            if density < 0.05 or density > 0.5:
                return False

            # Check for cursive-like characteristics
            # Signatures usually have connected strokes
            contours, _ = cv2.findContours(roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if len(contours) < 1 or len(contours) > 10:
                return False

            # Check aspect ratio (signatures are usually wider)
            h, w = roi.shape
            aspect_ratio = w / h if h > 0 else 0
            if aspect_ratio < 1.5 or aspect_ratio > 8:
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error checking signature: {e}")
            return False

    def extract_signature(
        self,
        image: np.ndarray,
        bbox: Tuple[int, int, int, int]
    ) -> np.ndarray:
        """
        Extract signature from image

        Args:
            image: Input image
            bbox: Bounding box (x, y, width, height)

        Returns:
            Extracted signature image
        """
        try:
            x, y, w, h = bbox
            signature = image[y:y+h, x:x+w]
            return signature

        except Exception as e:
            self.logger.error(f"Error extracting signature: {e}")
            return np.array([])

    def compare_signatures(
        self,
        signature1: np.ndarray,
        signature2: np.ndarray
    ) -> float:
        """
        Compare two signatures for similarity

        Args:
            signature1: First signature
            signature2: Second signature

        Returns:
            Similarity score (0-1)
        """
        try:
            # Resize to same size
            h = max(signature1.shape[0], signature2.shape[0])
            w = max(signature1.shape[1], signature2.shape[1])

            sig1_resized = cv2.resize(signature1, (w, h))
            sig2_resized = cv2.resize(signature2, (w, h))

            # Convert to grayscale if needed
            if len(sig1_resized.shape) == 3:
                sig1_resized = cv2.cvtColor(sig1_resized, cv2.COLOR_BGR2GRAY)
            if len(sig2_resized.shape) == 3:
                sig2_resized = cv2.cvtColor(sig2_resized, cv2.COLOR_BGR2GRAY)

            # Calculate similarity using correlation
            correlation = cv2.matchTemplate(sig1_resized, sig2_resized, cv2.TM_CCOEFF_NORMED)
            similarity = float(np.max(correlation))

            return max(0.0, min(1.0, similarity))

        except Exception as e:
            self.logger.error(f"Error comparing signatures: {e}")
            return 0.0
