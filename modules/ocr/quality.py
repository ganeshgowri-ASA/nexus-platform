"""
Quality Assessment Module

Assess OCR quality, confidence scoring, and error detection.
"""

import logging
from typing import Dict, List, Any, Tuple, Optional
import numpy as np
import cv2
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class QualityMetrics:
    """Quality metrics for OCR results"""
    overall_quality: float  # 0-1
    confidence_score: float  # 0-1
    image_quality: float  # 0-1
    text_clarity: float  # 0-1
    layout_complexity: float  # 0-1
    estimated_accuracy: float  # 0-1
    issues: List[str]


class QualityAssessment:
    """Assess quality of images and OCR results"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.QualityAssessment")

    def assess_image_quality(self, image: np.ndarray) -> Dict[str, float]:
        """
        Assess input image quality

        Args:
            image: Input image

        Returns:
            Quality metrics dictionary
        """
        try:
            metrics = {}

            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()

            # 1. Sharpness/Blur detection
            metrics['sharpness'] = self._calculate_sharpness(gray)

            # 2. Contrast
            metrics['contrast'] = self._calculate_contrast(gray)

            # 3. Brightness
            metrics['brightness'] = self._calculate_brightness(gray)

            # 4. Noise level
            metrics['noise_level'] = self._estimate_noise(gray)

            # 5. Resolution check
            metrics['resolution'] = self._check_resolution(image)

            # 6. Skew detection
            metrics['skew'] = self._detect_skew(gray)

            # Overall image quality score
            metrics['overall'] = self._calculate_overall_quality(metrics)

            self.logger.info(f"Image quality assessed: {metrics['overall']:.2f}")
            return metrics

        except Exception as e:
            self.logger.error(f"Error assessing image quality: {e}")
            return {}

    def _calculate_sharpness(self, image: np.ndarray) -> float:
        """Calculate image sharpness using Laplacian variance"""
        try:
            laplacian = cv2.Laplacian(image, cv2.CV_64F)
            variance = laplacian.var()
            # Normalize to 0-1 range (empirical threshold: 500 is sharp)
            return min(variance / 500.0, 1.0)
        except:
            return 0.5

    def _calculate_contrast(self, image: np.ndarray) -> float:
        """Calculate image contrast"""
        try:
            # Use standard deviation as contrast measure
            std = np.std(image)
            # Normalize (empirical threshold: 50 is good contrast)
            return min(std / 50.0, 1.0)
        except:
            return 0.5

    def _calculate_brightness(self, image: np.ndarray) -> float:
        """Calculate brightness (1.0 is optimal, <0.5 or >0.5 is suboptimal)"""
        try:
            mean_brightness = np.mean(image) / 255.0
            # Optimal range is 0.4-0.7
            if 0.4 <= mean_brightness <= 0.7:
                return 1.0
            elif mean_brightness < 0.4:
                return mean_brightness / 0.4
            else:
                return 1.0 - (mean_brightness - 0.7) / 0.3
        except:
            return 0.5

    def _estimate_noise(self, image: np.ndarray) -> float:
        """Estimate noise level (lower is better)"""
        try:
            # Use median filter to estimate noise
            median = cv2.medianBlur(image, 5)
            noise = np.abs(image.astype(float) - median.astype(float))
            noise_level = np.mean(noise) / 255.0
            # Return inverse (1.0 = no noise, 0.0 = very noisy)
            return 1.0 - min(noise_level * 5, 1.0)
        except:
            return 0.5

    def _check_resolution(self, image: np.ndarray) -> float:
        """Check if resolution is sufficient"""
        try:
            h, w = image.shape[:2]
            total_pixels = h * w
            # Good OCR needs at least 300 DPI equivalent
            # Assuming A4: 2480 x 3508 pixels at 300 DPI
            min_pixels = 1000 * 1000  # 1MP minimum
            optimal_pixels = 8000000  # 8MP optimal

            if total_pixels >= optimal_pixels:
                return 1.0
            elif total_pixels >= min_pixels:
                return total_pixels / optimal_pixels
            else:
                return total_pixels / min_pixels * 0.5
        except:
            return 0.5

    def _detect_skew(self, image: np.ndarray) -> float:
        """Detect image skew (1.0 = no skew)"""
        try:
            # Detect lines
            edges = cv2.Canny(image, 50, 150, apertureSize=3)
            lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)

            if lines is None or len(lines) == 0:
                return 1.0

            # Calculate angles
            angles = []
            for line in lines:
                rho, theta = line[0]
                angle = np.degrees(theta) - 90
                if -45 < angle < 45:
                    angles.append(angle)

            if not angles:
                return 1.0

            # Average angle
            avg_angle = np.median(angles)

            # Return score (1.0 = no skew, 0.0 = very skewed)
            return 1.0 - min(abs(avg_angle) / 10.0, 1.0)

        except:
            return 1.0

    def _calculate_overall_quality(self, metrics: Dict[str, float]) -> float:
        """Calculate overall quality score"""
        try:
            weights = {
                'sharpness': 0.25,
                'contrast': 0.20,
                'brightness': 0.15,
                'noise_level': 0.15,
                'resolution': 0.15,
                'skew': 0.10,
            }

            overall = sum(
                metrics.get(key, 0.5) * weight
                for key, weight in weights.items()
            )

            return overall

        except:
            return 0.5

    def assess_ocr_result(
        self,
        ocr_result: Any,
        image: Optional[np.ndarray] = None
    ) -> QualityMetrics:
        """
        Assess OCR result quality

        Args:
            ocr_result: OCR result object
            image: Optional original image

        Returns:
            Quality metrics
        """
        try:
            issues = []

            # 1. Confidence score
            confidence = getattr(ocr_result, 'confidence', 0.0)

            # 2. Text clarity (word-level confidence variance)
            text_clarity = self._assess_text_clarity(ocr_result)

            # 3. Image quality (if image provided)
            if image is not None:
                image_metrics = self.assess_image_quality(image)
                image_quality = image_metrics.get('overall', 0.5)
            else:
                image_quality = 0.5

            # 4. Layout complexity
            layout_complexity = self._assess_layout_complexity(ocr_result)

            # 5. Detect potential issues
            if confidence < 0.6:
                issues.append("Low overall confidence")
            if text_clarity < 0.6:
                issues.append("Inconsistent word confidence")
            if image_quality < 0.5:
                issues.append("Poor image quality")

            # 6. Estimate accuracy
            estimated_accuracy = (confidence + text_clarity + image_quality) / 3.0

            # 7. Overall quality
            overall_quality = (
                confidence * 0.4 +
                text_clarity * 0.3 +
                image_quality * 0.2 +
                (1.0 - layout_complexity) * 0.1
            )

            return QualityMetrics(
                overall_quality=overall_quality,
                confidence_score=confidence,
                image_quality=image_quality,
                text_clarity=text_clarity,
                layout_complexity=layout_complexity,
                estimated_accuracy=estimated_accuracy,
                issues=issues
            )

        except Exception as e:
            self.logger.error(f"Error assessing OCR result: {e}")
            return QualityMetrics(
                overall_quality=0.5,
                confidence_score=0.5,
                image_quality=0.5,
                text_clarity=0.5,
                layout_complexity=0.5,
                estimated_accuracy=0.5,
                issues=["Error during assessment"]
            )

    def _assess_text_clarity(self, ocr_result: Any) -> float:
        """Assess text clarity based on word confidence variance"""
        try:
            words = getattr(ocr_result, 'words', [])
            if not words:
                return 0.5

            confidences = [w.get('confidence', 0.0) for w in words]
            if not confidences:
                return 0.5

            # Low variance = consistent confidence = good clarity
            mean_conf = np.mean(confidences)
            std_conf = np.std(confidences)

            # Penalize high variance
            clarity = mean_conf * (1.0 - min(std_conf, 0.5))

            return clarity

        except:
            return 0.5

    def _assess_layout_complexity(self, ocr_result: Any) -> float:
        """Assess layout complexity (0 = simple, 1 = complex)"""
        try:
            blocks = getattr(ocr_result, 'blocks', [])
            lines = getattr(ocr_result, 'lines', [])

            # More blocks/lines = more complex
            num_blocks = len(blocks)
            num_lines = len(lines)

            # Simple heuristic
            complexity = min((num_blocks + num_lines / 2) / 50.0, 1.0)

            return complexity

        except:
            return 0.5


class ConfidenceScoring:
    """Confidence scoring for OCR results"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.ConfidenceScoring")

    def calculate_word_confidence(
        self,
        word: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Calculate confidence for individual word

        Args:
            word: Word dictionary with OCR data
            context: Optional context information

        Returns:
            Confidence score (0-1)
        """
        try:
            base_confidence = word.get('confidence', 0.0)

            # Adjust based on factors
            adjustments = 0.0

            # 1. Word length (very short words are less reliable)
            word_text = word.get('text', '')
            if len(word_text) == 1:
                adjustments -= 0.1
            elif len(word_text) >= 5:
                adjustments += 0.05

            # 2. Contains numbers (often more reliable)
            if any(c.isdigit() for c in word_text):
                adjustments += 0.05

            # 3. All caps (often headers, more reliable)
            if word_text.isupper() and len(word_text) > 1:
                adjustments += 0.05

            # Final confidence
            final_confidence = max(0.0, min(1.0, base_confidence + adjustments))

            return final_confidence

        except Exception as e:
            self.logger.error(f"Error calculating word confidence: {e}")
            return 0.5

    def aggregate_confidence(
        self,
        items: List[Dict[str, Any]],
        method: str = "weighted_average"
    ) -> float:
        """
        Aggregate confidence from multiple items

        Args:
            items: List of items with confidence scores
            method: Aggregation method

        Returns:
            Aggregated confidence
        """
        try:
            if not items:
                return 0.0

            confidences = [item.get('confidence', 0.0) for item in items]

            if method == "average":
                return sum(confidences) / len(confidences)
            elif method == "weighted_average":
                # Weight by text length
                weights = [len(item.get('text', '')) for item in items]
                total_weight = sum(weights)
                if total_weight == 0:
                    return sum(confidences) / len(confidences)
                weighted_sum = sum(c * w for c, w in zip(confidences, weights))
                return weighted_sum / total_weight
            elif method == "minimum":
                return min(confidences)
            elif method == "median":
                return float(np.median(confidences))
            else:
                return sum(confidences) / len(confidences)

        except Exception as e:
            self.logger.error(f"Error aggregating confidence: {e}")
            return 0.0


class ErrorDetection:
    """Detect potential OCR errors"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.ErrorDetection")

    def detect_errors(
        self,
        text: str,
        ocr_result: Optional[Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect potential OCR errors in text

        Args:
            text: OCR output text
            ocr_result: Optional OCR result object

        Returns:
            List of detected errors
        """
        try:
            errors = []

            # 1. Detect malformed words
            errors.extend(self._detect_malformed_words(text))

            # 2. Detect unlikely character combinations
            errors.extend(self._detect_unlikely_combinations(text))

            # 3. Detect inconsistent spacing
            errors.extend(self._detect_spacing_issues(text))

            # 4. Detect low confidence words
            if ocr_result:
                errors.extend(self._detect_low_confidence_words(ocr_result))

            self.logger.info(f"Detected {len(errors)} potential errors")
            return errors

        except Exception as e:
            self.logger.error(f"Error detecting errors: {e}")
            return []

    def _detect_malformed_words(self, text: str) -> List[Dict[str, Any]]:
        """Detect malformed words"""
        errors = []
        words = text.split()

        for word in words:
            # Check for unusual patterns
            if len(word) > 1:
                # Too many consecutive consonants
                if len([c for c in word if c.lower() in 'bcdfghjklmnpqrstvwxyz']) > len(word) * 0.8:
                    errors.append({
                        'type': 'malformed_word',
                        'word': word,
                        'description': 'Too many consonants'
                    })

        return errors

    def _detect_unlikely_combinations(self, text: str) -> List[Dict[str, Any]]:
        """Detect unlikely character combinations"""
        errors = []

        # Common OCR confusion patterns
        unlikely_patterns = [
            r'\d[a-z](?=[A-Z])',  # digit-lowercase-uppercase
            r'[A-Z][a-z][A-Z]',    # Mixed case mid-word
        ]

        import re
        for pattern in unlikely_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                errors.append({
                    'type': 'unlikely_combination',
                    'text': match.group(),
                    'position': match.start(),
                    'description': 'Unlikely character combination'
                })

        return errors

    def _detect_spacing_issues(self, text: str) -> List[Dict[str, Any]]:
        """Detect spacing issues"""
        errors = []

        # Check for missing spaces (consecutive caps or lowercase)
        import re
        patterns = [
            r'[a-z][A-Z]',  # lowercase followed by uppercase
            r'\.[A-Z]',      # period followed by capital without space
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                errors.append({
                    'type': 'spacing_issue',
                    'text': match.group(),
                    'position': match.start(),
                    'description': 'Possible missing space'
                })

        return errors

    def _detect_low_confidence_words(self, ocr_result: Any) -> List[Dict[str, Any]]:
        """Detect words with low confidence"""
        errors = []

        try:
            words = getattr(ocr_result, 'words', [])
            for word in words:
                confidence = word.get('confidence', 1.0)
                if confidence < 0.6:
                    errors.append({
                        'type': 'low_confidence',
                        'word': word.get('text', ''),
                        'confidence': confidence,
                        'description': f'Low confidence: {confidence:.2f}'
                    })

        except:
            pass

        return errors
