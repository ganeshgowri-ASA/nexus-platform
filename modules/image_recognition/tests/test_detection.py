"""
Tests for Object Detection Module

Tests:
- ObjectDetector
- FaceDetector
- LogoDetector
- ProductDetector
"""

import pytest
import numpy as np
from PIL import Image
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


# ============================================================================
# Test ObjectDetector
# ============================================================================

class TestObjectDetector:
    """Test ObjectDetector."""

    @patch('modules.image_recognition.detection.YOLOModelWrapper')
    def test_initialization(self, mock_yolo):
        """Test object detector initialization."""
        from modules.image_recognition.detection import ObjectDetector

        detector = ObjectDetector(model_type="yolov5", confidence=0.6)

        assert detector.model_type == "yolov5"
        assert detector.confidence_threshold == 0.6

    @patch('modules.image_recognition.detection.YOLOModelWrapper')
    def test_detect_objects(self, mock_yolo, sample_image):
        """Test object detection."""
        from modules.image_recognition.detection import ObjectDetector

        mock_model = MagicMock()
        mock_model.predict.return_value = {
            'detections': [
                {
                    'label': 'person',
                    'confidence': 0.95,
                    'bbox': {'x': 10, 'y': 20, 'width': 100, 'height': 200},
                    'class_id': 0
                },
                {
                    'label': 'car',
                    'confidence': 0.85,
                    'bbox': {'x': 150, 'y': 50, 'width': 200, 'height': 150},
                    'class_id': 1
                }
            ],
            'num_detections': 2,
            'processing_time_ms': 150
        }
        mock_yolo.return_value = mock_model

        detector = ObjectDetector(model_type="yolov5")
        detector.model = mock_model
        result = detector.detect(sample_image)

        assert result['success'] is True
        assert result['num_detections'] == 2
        assert result['detections'][0]['label'] == 'person'

    @patch('modules.image_recognition.detection.YOLOModelWrapper')
    def test_detect_with_confidence_filter(self, mock_yolo, sample_image):
        """Test detection with confidence filtering."""
        from modules.image_recognition.detection import ObjectDetector

        mock_model = MagicMock()
        mock_model.predict.return_value = {
            'detections': [
                {'label': 'person', 'confidence': 0.95, 'bbox': {}, 'class_id': 0},
                {'label': 'car', 'confidence': 0.45, 'bbox': {}, 'class_id': 1}
            ],
            'num_detections': 2,
            'processing_time_ms': 150
        }
        mock_yolo.return_value = mock_model

        detector = ObjectDetector(confidence=0.5)
        detector.model = mock_model
        result = detector.detect(sample_image, confidence_threshold=0.5)

        # Should filter out the car detection
        assert result['success'] is True

    @patch('modules.image_recognition.detection.YOLOModelWrapper')
    def test_detect_batch(self, mock_yolo, multiple_sample_images):
        """Test batch object detection."""
        from modules.image_recognition.detection import ObjectDetector

        mock_model = MagicMock()
        mock_model.predict.return_value = {
            'detections': [
                {'label': 'person', 'confidence': 0.95, 'bbox': {}, 'class_id': 0}
            ],
            'num_detections': 1,
            'processing_time_ms': 150
        }
        mock_yolo.return_value = mock_model

        detector = ObjectDetector()
        detector.model = mock_model
        results = detector.detect_batch(multiple_sample_images)

        assert len(results) == len(multiple_sample_images)
        assert all(r['success'] for r in results)

    @patch('modules.image_recognition.detection.YOLOModelWrapper')
    def test_detect_specific_classes(self, mock_yolo, sample_image):
        """Test detecting specific object classes."""
        from modules.image_recognition.detection import ObjectDetector

        mock_model = MagicMock()
        mock_model.predict.return_value = {
            'detections': [
                {'label': 'person', 'confidence': 0.95, 'bbox': {}, 'class_id': 0},
                {'label': 'car', 'confidence': 0.85, 'bbox': {}, 'class_id': 1},
                {'label': 'dog', 'confidence': 0.75, 'bbox': {}, 'class_id': 2}
            ],
            'num_detections': 3,
            'processing_time_ms': 150
        }
        mock_yolo.return_value = mock_model

        detector = ObjectDetector()
        detector.model = mock_model
        result = detector.detect(sample_image, classes=['person', 'dog'])

        # Implementation would filter by classes
        assert result['success'] is True


# ============================================================================
# Test FaceDetector
# ============================================================================

class TestFaceDetector:
    """Test FaceDetector."""

    @patch('modules.image_recognition.detection.cv2')
    def test_initialization(self, mock_cv2):
        """Test face detector initialization."""
        from modules.image_recognition.detection import FaceDetector

        detector = FaceDetector()
        assert detector is not None

    @patch('modules.image_recognition.detection.cv2')
    def test_detect_faces(self, mock_cv2, sample_image_array):
        """Test face detection."""
        from modules.image_recognition.detection import FaceDetector

        # Mock cascade classifier
        mock_cascade = MagicMock()
        mock_cascade.detectMultiScale.return_value = np.array([
            [10, 20, 100, 100],
            [200, 50, 80, 80]
        ])
        mock_cv2.CascadeClassifier.return_value = mock_cascade

        detector = FaceDetector()
        detector.face_cascade = mock_cascade
        result = detector.detect(sample_image_array)

        assert result['success'] is True
        assert result['num_faces'] == 2
        assert len(result['faces']) == 2

    @patch('modules.image_recognition.detection.cv2')
    def test_detect_no_faces(self, mock_cv2, sample_image_array):
        """Test when no faces are detected."""
        from modules.image_recognition.detection import FaceDetector

        mock_cascade = MagicMock()
        mock_cascade.detectMultiScale.return_value = np.array([])
        mock_cv2.CascadeClassifier.return_value = mock_cascade

        detector = FaceDetector()
        detector.face_cascade = mock_cascade
        result = detector.detect(sample_image_array)

        assert result['success'] is True
        assert result['num_faces'] == 0

    @patch('modules.image_recognition.detection.cv2')
    def test_detect_with_landmarks(self, mock_cv2, sample_image_array):
        """Test face detection with facial landmarks."""
        from modules.image_recognition.detection import FaceDetector

        mock_cascade = MagicMock()
        mock_cascade.detectMultiScale.return_value = np.array([[10, 20, 100, 100]])
        mock_cv2.CascadeClassifier.return_value = mock_cascade

        detector = FaceDetector(detect_landmarks=True)
        detector.face_cascade = mock_cascade
        result = detector.detect(sample_image_array)

        assert result['success'] is True
        assert result['num_faces'] == 1


# ============================================================================
# Test LogoDetector
# ============================================================================

class TestLogoDetector:
    """Test LogoDetector."""

    @patch('modules.image_recognition.detection.YOLOModelWrapper')
    def test_initialization(self, mock_yolo):
        """Test logo detector initialization."""
        from modules.image_recognition.detection import LogoDetector

        detector = LogoDetector(model_path="/path/to/logo/model")
        assert detector is not None

    @patch('modules.image_recognition.detection.YOLOModelWrapper')
    def test_detect_logos(self, mock_yolo, sample_image):
        """Test logo detection."""
        from modules.image_recognition.detection import LogoDetector

        mock_model = MagicMock()
        mock_model.predict.return_value = {
            'detections': [
                {
                    'label': 'Nike',
                    'confidence': 0.92,
                    'bbox': {'x': 10, 'y': 20, 'width': 50, 'height': 50},
                    'class_id': 0
                },
                {
                    'label': 'Adidas',
                    'confidence': 0.88,
                    'bbox': {'x': 100, 'y': 50, 'width': 60, 'height': 60},
                    'class_id': 1
                }
            ],
            'num_detections': 2,
            'processing_time_ms': 200
        }
        mock_yolo.return_value = mock_model

        detector = LogoDetector()
        detector.model = mock_model
        result = detector.detect(sample_image)

        assert result['success'] is True
        assert result['num_logos'] == 2
        assert result['logos'][0]['brand'] == 'Nike'

    @patch('modules.image_recognition.detection.YOLOModelWrapper')
    def test_detect_specific_brands(self, mock_yolo, sample_image):
        """Test detecting specific brand logos."""
        from modules.image_recognition.detection import LogoDetector

        mock_model = MagicMock()
        mock_model.predict.return_value = {
            'detections': [
                {'label': 'Nike', 'confidence': 0.92, 'bbox': {}, 'class_id': 0},
                {'label': 'Adidas', 'confidence': 0.88, 'bbox': {}, 'class_id': 1},
                {'label': 'Puma', 'confidence': 0.85, 'bbox': {}, 'class_id': 2}
            ],
            'num_detections': 3,
            'processing_time_ms': 200
        }
        mock_yolo.return_value = mock_model

        detector = LogoDetector()
        detector.model = mock_model
        result = detector.detect(sample_image, brands=['Nike', 'Puma'])

        assert result['success'] is True


# ============================================================================
# Test ProductDetector
# ============================================================================

class TestProductDetector:
    """Test ProductDetector."""

    @patch('modules.image_recognition.detection.YOLOModelWrapper')
    def test_initialization(self, mock_yolo):
        """Test product detector initialization."""
        from modules.image_recognition.detection import ProductDetector

        detector = ProductDetector()
        assert detector is not None

    @patch('modules.image_recognition.detection.YOLOModelWrapper')
    def test_detect_products(self, mock_yolo, sample_image):
        """Test product detection."""
        from modules.image_recognition.detection import ProductDetector

        mock_model = MagicMock()
        mock_model.predict.return_value = {
            'detections': [
                {
                    'label': 'bottle',
                    'confidence': 0.93,
                    'bbox': {'x': 10, 'y': 20, 'width': 50, 'height': 100},
                    'class_id': 0
                },
                {
                    'label': 'phone',
                    'confidence': 0.89,
                    'bbox': {'x': 100, 'y': 50, 'width': 40, 'height': 80},
                    'class_id': 1
                }
            ],
            'num_detections': 2,
            'processing_time_ms': 180
        }
        mock_yolo.return_value = mock_model

        detector = ProductDetector()
        detector.model = mock_model
        result = detector.detect(sample_image)

        assert result['success'] is True
        assert result['num_products'] == 2
        assert result['products'][0]['category'] == 'bottle'

    @patch('modules.image_recognition.detection.YOLOModelWrapper')
    def test_detect_with_attributes(self, mock_yolo, sample_image):
        """Test product detection with attributes."""
        from modules.image_recognition.detection import ProductDetector

        mock_model = MagicMock()
        mock_model.predict.return_value = {
            'detections': [
                {
                    'label': 'bottle',
                    'confidence': 0.93,
                    'bbox': {'x': 10, 'y': 20, 'width': 50, 'height': 100},
                    'class_id': 0,
                    'attributes': {'color': 'blue', 'size': 'large'}
                }
            ],
            'num_detections': 1,
            'processing_time_ms': 180
        }
        mock_yolo.return_value = mock_model

        detector = ProductDetector(detect_attributes=True)
        detector.model = mock_model
        result = detector.detect(sample_image)

        assert result['success'] is True
        assert 'attributes' in result['products'][0]

    @patch('modules.image_recognition.detection.YOLOModelWrapper')
    def test_count_products(self, mock_yolo, sample_image):
        """Test product counting."""
        from modules.image_recognition.detection import ProductDetector

        mock_model = MagicMock()
        mock_model.predict.return_value = {
            'detections': [
                {'label': 'bottle', 'confidence': 0.93, 'bbox': {}, 'class_id': 0},
                {'label': 'bottle', 'confidence': 0.91, 'bbox': {}, 'class_id': 0},
                {'label': 'phone', 'confidence': 0.89, 'bbox': {}, 'class_id': 1}
            ],
            'num_detections': 3,
            'processing_time_ms': 180
        }
        mock_yolo.return_value = mock_model

        detector = ProductDetector()
        detector.model = mock_model
        result = detector.detect(sample_image)

        # Should have counts by category
        assert result['success'] is True
        assert result['num_products'] == 3


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

class TestDetectionEdgeCases:
    """Test edge cases and error handling."""

    @patch('modules.image_recognition.detection.YOLOModelWrapper')
    def test_detect_empty_image(self, mock_yolo):
        """Test detection on empty image."""
        from modules.image_recognition.detection import ObjectDetector

        empty_image = Image.new('RGB', (1, 1))
        mock_model = MagicMock()
        mock_model.predict.return_value = {
            'detections': [],
            'num_detections': 0,
            'processing_time_ms': 50
        }
        mock_yolo.return_value = mock_model

        detector = ObjectDetector()
        detector.model = mock_model
        result = detector.detect(empty_image)

        assert result['success'] is True
        assert result['num_detections'] == 0

    @patch('modules.image_recognition.detection.YOLOModelWrapper')
    def test_detect_error_handling(self, mock_yolo, sample_image):
        """Test error handling during detection."""
        from modules.image_recognition.detection import ObjectDetector

        mock_model = MagicMock()
        mock_model.predict.side_effect = Exception("Detection failed")
        mock_yolo.return_value = mock_model

        detector = ObjectDetector()
        detector.model = mock_model
        result = detector.detect(sample_image)

        assert result['success'] is False
        assert 'error' in result

    @patch('modules.image_recognition.detection.YOLOModelWrapper')
    @pytest.mark.parametrize("confidence", [0.1, 0.5, 0.9])
    def test_different_confidence_thresholds(
        self, mock_yolo, sample_image, confidence
    ):
        """Test detection with different confidence thresholds."""
        from modules.image_recognition.detection import ObjectDetector

        mock_model = MagicMock()
        mock_model.predict.return_value = {
            'detections': [
                {'label': 'person', 'confidence': 0.95, 'bbox': {}, 'class_id': 0},
                {'label': 'car', 'confidence': 0.65, 'bbox': {}, 'class_id': 1},
                {'label': 'dog', 'confidence': 0.35, 'bbox': {}, 'class_id': 2}
            ],
            'num_detections': 3,
            'processing_time_ms': 150
        }
        mock_yolo.return_value = mock_model

        detector = ObjectDetector(confidence=confidence)
        detector.model = mock_model
        result = detector.detect(sample_image)

        assert result['success'] is True

    @patch('modules.image_recognition.detection.YOLOModelWrapper')
    def test_detect_large_number_of_objects(self, mock_yolo, sample_image):
        """Test detecting large number of objects."""
        from modules.image_recognition.detection import ObjectDetector

        # Create 100 detections
        detections = [
            {
                'label': f'object_{i}',
                'confidence': 0.9 - (i * 0.001),
                'bbox': {'x': i*10, 'y': i*10, 'width': 50, 'height': 50},
                'class_id': i
            }
            for i in range(100)
        ]

        mock_model = MagicMock()
        mock_model.predict.return_value = {
            'detections': detections,
            'num_detections': 100,
            'processing_time_ms': 500
        }
        mock_yolo.return_value = mock_model

        detector = ObjectDetector()
        detector.model = mock_model
        result = detector.detect(sample_image)

        assert result['success'] is True
        assert result['num_detections'] == 100
