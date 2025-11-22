"""
Object Detection Module for Image Recognition

Provides comprehensive object detection capabilities including:
- General object detection with YOLO
- Face detection and recognition
- Logo detection
- Product detection
- Multi-object tracking
- Bounding box management

Integrates with NEXUS modules for authentication, storage, and database.
"""

import logging
import os
import time
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Union, Tuple
from pathlib import Path
import numpy as np
from PIL import Image
import io
import base64
from datetime import datetime

from .models import YOLOModelWrapper, BaseModelWrapper, ModelFactory

logger = logging.getLogger(__name__)


class DetectionResult:
    """
    Represents a single detection result.
    """

    def __init__(
        self,
        label: str,
        confidence: float,
        bbox: Dict[str, float],
        class_id: Optional[int] = None,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize detection result.

        Args:
            label: Detected object label
            confidence: Detection confidence (0-1)
            bbox: Bounding box dict with x, y, width, height
            class_id: Class ID from model
            attributes: Additional attributes
        """
        self.label = label
        self.confidence = confidence
        self.bbox = bbox
        self.class_id = class_id
        self.attributes = attributes or {}
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'label': self.label,
            'confidence': float(self.confidence),
            'bbox': self.bbox,
            'class_id': self.class_id,
            'attributes': self.attributes,
            'timestamp': self.timestamp.isoformat()
        }

    def __repr__(self) -> str:
        return f"<DetectionResult(label={self.label}, confidence={self.confidence:.2f})>"


class BaseDetector(ABC):
    """
    Abstract base class for all detectors.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize detector.

        Args:
            model_path: Path to model weights
            config: Detector configuration
        """
        self.model_path = model_path
        self.config = config or {}
        self.model: Optional[BaseModelWrapper] = None
        self.is_loaded = False
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    def load_model(self) -> bool:
        """Load the detection model."""
        pass

    @abstractmethod
    def detect(
        self,
        image: Union[str, np.ndarray, Image.Image],
        confidence_threshold: float = 0.5,
        **kwargs
    ) -> List[DetectionResult]:
        """
        Detect objects in image.

        Args:
            image: Input image
            confidence_threshold: Minimum confidence threshold
            **kwargs: Additional detection parameters

        Returns:
            List of detection results
        """
        pass

    def detect_batch(
        self,
        images: List[Union[str, np.ndarray, Image.Image]],
        confidence_threshold: float = 0.5,
        **kwargs
    ) -> List[List[DetectionResult]]:
        """
        Detect objects in multiple images.

        Args:
            images: List of images
            confidence_threshold: Minimum confidence threshold
            **kwargs: Additional parameters

        Returns:
            List of detection results for each image
        """
        results = []
        for image in images:
            try:
                detections = self.detect(image, confidence_threshold, **kwargs)
                results.append(detections)
            except Exception as e:
                self.logger.error(f"Error detecting in image: {e}")
                results.append([])
        return results

    def unload_model(self) -> bool:
        """Unload model from memory."""
        try:
            if self.model:
                self.model.unload_model()
            self.model = None
            self.is_loaded = False
            self.logger.info("Model unloaded successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error unloading model: {e}")
            return False


class ObjectDetector(BaseDetector):
    """
    General-purpose object detector using YOLO.
    Detects multiple object categories in images.
    """

    def __init__(
        self,
        model_name: str = "yolov5",
        model_path: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize object detector.

        Args:
            model_name: YOLO model name (yolov5, yolov8, etc.)
            model_path: Path to custom model
            config: Model configuration
        """
        super().__init__(model_path, config)
        self.model_name = model_name
        self.confidence_threshold = self.config.get('confidence_threshold', 0.5)
        self.iou_threshold = self.config.get('iou_threshold', 0.45)

    def load_model(self) -> bool:
        """Load YOLO model."""
        try:
            self.model = YOLOModelWrapper(
                model_name=self.model_name,
                model_path=self.model_path,
                config=self.config
            )
            success = self.model.load_model()
            self.is_loaded = success
            if success:
                self.logger.info(f"Loaded {self.model_name} model successfully")
            return success
        except Exception as e:
            self.logger.error(f"Error loading model: {e}")
            return False

    def detect(
        self,
        image: Union[str, np.ndarray, Image.Image],
        confidence_threshold: Optional[float] = None,
        iou_threshold: Optional[float] = None,
        max_detections: int = 100,
        target_classes: Optional[List[str]] = None
    ) -> List[DetectionResult]:
        """
        Detect objects in image.

        Args:
            image: Input image
            confidence_threshold: Minimum confidence (default from config)
            iou_threshold: IoU threshold for NMS
            max_detections: Maximum number of detections to return
            target_classes: Filter results to specific classes

        Returns:
            List of detection results
        """
        if not self.is_loaded:
            self.load_model()

        try:
            # Load image if path provided
            if isinstance(image, str):
                image = Image.open(image).convert('RGB')

            # Use provided thresholds or defaults
            conf_thresh = confidence_threshold or self.confidence_threshold
            iou_thresh = iou_threshold or self.iou_threshold

            # Run detection
            results = self.model.predict(
                image,
                confidence_threshold=conf_thresh,
                iou_threshold=iou_thresh
            )

            # Parse detections
            detections = []
            for det in results.get('detections', [])[:max_detections]:
                # Filter by target classes if specified
                if target_classes and det['label'] not in target_classes:
                    continue

                detection = DetectionResult(
                    label=det['label'],
                    confidence=det['confidence'],
                    bbox=det['bbox'],
                    class_id=det.get('class_id')
                )
                detections.append(detection)

            self.logger.info(f"Detected {len(detections)} objects")
            return detections

        except Exception as e:
            self.logger.error(f"Error during detection: {e}")
            raise

    def detect_with_tracking(
        self,
        images: List[Union[str, np.ndarray, Image.Image]],
        confidence_threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Detect objects with tracking across multiple frames.

        Args:
            images: List of sequential images (frames)
            confidence_threshold: Minimum confidence

        Returns:
            List of tracked detections with track IDs
        """
        try:
            all_detections = []
            track_id_counter = 0
            previous_detections = []

            for idx, image in enumerate(images):
                detections = self.detect(image, confidence_threshold)

                # Simple tracking based on IoU overlap
                tracked_detections = []
                for detection in detections:
                    # Try to match with previous detections
                    matched = False
                    for prev_det in previous_detections:
                        iou = self._calculate_iou(detection.bbox, prev_det['bbox'])
                        if iou > 0.5 and detection.label == prev_det['label']:
                            # Same object, assign previous track ID
                            tracked_detections.append({
                                'frame': idx,
                                'track_id': prev_det['track_id'],
                                'detection': detection.to_dict()
                            })
                            matched = True
                            break

                    if not matched:
                        # New object, assign new track ID
                        tracked_detections.append({
                            'frame': idx,
                            'track_id': track_id_counter,
                            'detection': detection.to_dict()
                        })
                        track_id_counter += 1

                all_detections.extend(tracked_detections)
                previous_detections = tracked_detections

            return all_detections

        except Exception as e:
            self.logger.error(f"Error during tracking: {e}")
            raise

    def _calculate_iou(self, bbox1: Dict[str, float], bbox2: Dict[str, float]) -> float:
        """Calculate Intersection over Union between two bounding boxes."""
        x1_min = bbox1['x']
        y1_min = bbox1['y']
        x1_max = bbox1['x'] + bbox1['width']
        y1_max = bbox1['y'] + bbox1['height']

        x2_min = bbox2['x']
        y2_min = bbox2['y']
        x2_max = bbox2['x'] + bbox2['width']
        y2_max = bbox2['y'] + bbox2['height']

        # Calculate intersection
        x_left = max(x1_min, x2_min)
        y_top = max(y1_min, y2_min)
        x_right = min(x1_max, x2_max)
        y_bottom = min(y1_max, y2_max)

        if x_right < x_left or y_bottom < y_top:
            return 0.0

        intersection_area = (x_right - x_left) * (y_bottom - y_top)

        # Calculate union
        bbox1_area = bbox1['width'] * bbox1['height']
        bbox2_area = bbox2['width'] * bbox2['height']
        union_area = bbox1_area + bbox2_area - intersection_area

        return intersection_area / union_area if union_area > 0 else 0.0


class FaceDetector(BaseDetector):
    """
    Face detection and recognition system.
    Detects faces and can extract facial features.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize face detector.

        Args:
            model_path: Path to face detection model
            config: Detector configuration
        """
        super().__init__(model_path, config)
        self.min_face_size = self.config.get('min_face_size', 20)
        self.face_cascade = None

    def load_model(self) -> bool:
        """Load face detection model."""
        try:
            import cv2

            # Load Haar Cascade for face detection
            cascade_path = self.model_path or cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(cascade_path)

            if self.face_cascade.empty():
                raise ValueError("Failed to load face cascade")

            self.is_loaded = True
            self.logger.info("Face detector loaded successfully")
            return True

        except ImportError:
            self.logger.error("OpenCV not installed. Install with: pip install opencv-python")
            return False
        except Exception as e:
            self.logger.error(f"Error loading face detector: {e}")
            return False

    def detect(
        self,
        image: Union[str, np.ndarray, Image.Image],
        confidence_threshold: float = 0.5,
        detect_landmarks: bool = False,
        extract_features: bool = False
    ) -> List[DetectionResult]:
        """
        Detect faces in image.

        Args:
            image: Input image
            confidence_threshold: Minimum confidence (not used for Haar Cascade)
            detect_landmarks: Whether to detect facial landmarks
            extract_features: Whether to extract face embeddings

        Returns:
            List of face detections
        """
        if not self.is_loaded:
            self.load_model()

        try:
            import cv2

            # Load and convert image
            if isinstance(image, str):
                image = cv2.imread(image)
            elif isinstance(image, Image.Image):
                image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            elif isinstance(image, np.ndarray):
                if len(image.shape) == 3 and image.shape[2] == 3:
                    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            # Convert to grayscale for detection
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Detect faces
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(self.min_face_size, self.min_face_size)
            )

            # Convert to DetectionResult objects
            detections = []
            for idx, (x, y, w, h) in enumerate(faces):
                attributes = {}

                # Extract face region for additional processing
                if detect_landmarks or extract_features:
                    face_region = image[y:y+h, x:x+w]
                    attributes['face_region_size'] = face_region.shape[:2]

                # Add landmarks if requested (simplified)
                if detect_landmarks:
                    attributes['landmarks'] = self._estimate_landmarks(x, y, w, h)

                # Add features if requested
                if extract_features:
                    attributes['features'] = self._extract_face_features(face_region)

                detection = DetectionResult(
                    label='face',
                    confidence=1.0,  # Haar Cascade doesn't provide confidence
                    bbox={'x': float(x), 'y': float(y), 'width': float(w), 'height': float(h)},
                    class_id=0,
                    attributes=attributes
                )
                detections.append(detection)

            self.logger.info(f"Detected {len(detections)} faces")
            return detections

        except Exception as e:
            self.logger.error(f"Error detecting faces: {e}")
            raise

    def _estimate_landmarks(
        self,
        x: int,
        y: int,
        w: int,
        h: int
    ) -> Dict[str, Tuple[float, float]]:
        """
        Estimate facial landmark positions (simplified).

        Args:
            x, y, w, h: Face bounding box

        Returns:
            Dictionary of landmark positions
        """
        # Simplified landmark estimation based on face box
        return {
            'left_eye': (x + w * 0.3, y + h * 0.35),
            'right_eye': (x + w * 0.7, y + h * 0.35),
            'nose': (x + w * 0.5, y + h * 0.55),
            'mouth_left': (x + w * 0.35, y + h * 0.75),
            'mouth_right': (x + w * 0.65, y + h * 0.75)
        }

    def _extract_face_features(self, face_image: np.ndarray) -> List[float]:
        """
        Extract face feature embeddings (placeholder).

        Args:
            face_image: Face region image

        Returns:
            Feature vector
        """
        # Placeholder - in production, use a face recognition model
        # like FaceNet, ArcFace, or DeepFace
        try:
            import cv2
            # Simple feature: normalized histogram
            face_gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
            face_resized = cv2.resize(face_gray, (64, 64))
            features = face_resized.flatten().astype(float)
            # Normalize
            features = features / (np.linalg.norm(features) + 1e-7)
            return features.tolist()[:128]  # Return first 128 dimensions
        except Exception as e:
            self.logger.warning(f"Error extracting features: {e}")
            return []


class LogoDetector(BaseDetector):
    """
    Logo detection system for brand recognition.
    Can detect and classify company logos in images.
    """

    def __init__(
        self,
        model_path: str,
        logo_database: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize logo detector.

        Args:
            model_path: Path to logo detection model
            logo_database: Database of known logos
            config: Detector configuration
        """
        super().__init__(model_path, config)
        self.logo_database = logo_database or {}
        self.known_logos = list(self.logo_database.keys())

    def load_model(self) -> bool:
        """Load logo detection model."""
        try:
            # Use YOLO for logo detection
            self.model = YOLOModelWrapper(
                model_name="logo_detector",
                model_path=self.model_path,
                config=self.config
            )
            success = self.model.load_model()
            self.is_loaded = success
            if success:
                self.logger.info("Logo detector loaded successfully")
            return success
        except Exception as e:
            self.logger.error(f"Error loading logo detector: {e}")
            return False

    def detect(
        self,
        image: Union[str, np.ndarray, Image.Image],
        confidence_threshold: float = 0.6,
        return_brand_info: bool = True
    ) -> List[DetectionResult]:
        """
        Detect logos in image.

        Args:
            image: Input image
            confidence_threshold: Minimum confidence
            return_brand_info: Include brand information from database

        Returns:
            List of logo detections
        """
        if not self.is_loaded:
            self.load_model()

        try:
            # Load image if path provided
            if isinstance(image, str):
                image = Image.open(image).convert('RGB')

            # Run detection
            results = self.model.predict(
                image,
                confidence_threshold=confidence_threshold
            )

            # Parse logo detections
            detections = []
            for det in results.get('detections', []):
                attributes = {}

                # Add brand information if available
                if return_brand_info and det['label'] in self.logo_database:
                    attributes['brand_info'] = self.logo_database[det['label']]

                detection = DetectionResult(
                    label=det['label'],
                    confidence=det['confidence'],
                    bbox=det['bbox'],
                    class_id=det.get('class_id'),
                    attributes=attributes
                )
                detections.append(detection)

            self.logger.info(f"Detected {len(detections)} logos")
            return detections

        except Exception as e:
            self.logger.error(f"Error detecting logos: {e}")
            raise


class ProductDetector(BaseDetector):
    """
    Product detection system for e-commerce and retail.
    Detects and classifies products in images.
    """

    def __init__(
        self,
        model_path: str,
        product_catalog: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize product detector.

        Args:
            model_path: Path to product detection model
            product_catalog: Product catalog database
            config: Detector configuration
        """
        super().__init__(model_path, config)
        self.product_catalog = product_catalog or {}

    def load_model(self) -> bool:
        """Load product detection model."""
        try:
            self.model = YOLOModelWrapper(
                model_name="product_detector",
                model_path=self.model_path,
                config=self.config
            )
            success = self.model.load_model()
            self.is_loaded = success
            if success:
                self.logger.info("Product detector loaded successfully")
            return success
        except Exception as e:
            self.logger.error(f"Error loading product detector: {e}")
            return False

    def detect(
        self,
        image: Union[str, np.ndarray, Image.Image],
        confidence_threshold: float = 0.5,
        extract_attributes: bool = True
    ) -> List[DetectionResult]:
        """
        Detect products in image.

        Args:
            image: Input image
            confidence_threshold: Minimum confidence
            extract_attributes: Extract product attributes

        Returns:
            List of product detections
        """
        if not self.is_loaded:
            self.load_model()

        try:
            # Load image if path provided
            if isinstance(image, str):
                image = Image.open(image).convert('RGB')

            # Run detection
            results = self.model.predict(
                image,
                confidence_threshold=confidence_threshold
            )

            # Parse product detections
            detections = []
            for det in results.get('detections', []):
                attributes = {}

                # Extract product attributes if requested
                if extract_attributes:
                    attributes = self._extract_product_attributes(image, det['bbox'])

                # Add catalog information if available
                if det['label'] in self.product_catalog:
                    attributes['catalog_info'] = self.product_catalog[det['label']]

                detection = DetectionResult(
                    label=det['label'],
                    confidence=det['confidence'],
                    bbox=det['bbox'],
                    class_id=det.get('class_id'),
                    attributes=attributes
                )
                detections.append(detection)

            self.logger.info(f"Detected {len(detections)} products")
            return detections

        except Exception as e:
            self.logger.error(f"Error detecting products: {e}")
            raise

    def _extract_product_attributes(
        self,
        image: Image.Image,
        bbox: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Extract product attributes from detection.

        Args:
            image: Full image
            bbox: Product bounding box

        Returns:
            Dictionary of attributes
        """
        try:
            # Crop product region
            x, y, w, h = bbox['x'], bbox['y'], bbox['width'], bbox['height']
            product_region = image.crop((x, y, x + w, y + h))

            # Extract basic attributes
            attributes = {
                'dimensions': {'width': w, 'height': h},
                'aspect_ratio': w / h if h > 0 else 0,
                'area': w * h
            }

            # Analyze dominant colors (simplified)
            product_array = np.array(product_region.resize((100, 100)))
            avg_color = product_array.mean(axis=(0, 1))
            attributes['dominant_color'] = {
                'r': int(avg_color[0]),
                'g': int(avg_color[1]),
                'b': int(avg_color[2])
            }

            return attributes

        except Exception as e:
            self.logger.warning(f"Error extracting product attributes: {e}")
            return {}


class DetectionManager:
    """
    Manages multiple detectors and provides unified detection interface.
    """

    def __init__(self):
        """Initialize detection manager."""
        self.detectors: Dict[str, BaseDetector] = {}
        self.logger = logging.getLogger(f"{__name__}.DetectionManager")

    def register_detector(self, name: str, detector: BaseDetector) -> None:
        """
        Register a detector.

        Args:
            name: Detector name
            detector: Detector instance
        """
        self.detectors[name] = detector
        self.logger.info(f"Registered detector: {name}")

    def get_detector(self, name: str) -> Optional[BaseDetector]:
        """Get a registered detector."""
        return self.detectors.get(name)

    def detect(
        self,
        detector_name: str,
        image: Union[str, np.ndarray, Image.Image],
        **kwargs
    ) -> List[DetectionResult]:
        """
        Run detection using specified detector.

        Args:
            detector_name: Name of detector to use
            image: Input image
            **kwargs: Detection parameters

        Returns:
            List of detection results
        """
        detector = self.get_detector(detector_name)
        if not detector:
            raise ValueError(f"Detector not found: {detector_name}")

        return detector.detect(image, **kwargs)

    def detect_multi(
        self,
        image: Union[str, np.ndarray, Image.Image],
        detectors: List[str],
        **kwargs
    ) -> Dict[str, List[DetectionResult]]:
        """
        Run multiple detectors on same image.

        Args:
            image: Input image
            detectors: List of detector names
            **kwargs: Detection parameters

        Returns:
            Dictionary mapping detector names to results
        """
        results = {}
        for detector_name in detectors:
            try:
                results[detector_name] = self.detect(detector_name, image, **kwargs)
            except Exception as e:
                self.logger.error(f"Error with detector {detector_name}: {e}")
                results[detector_name] = []

        return results

    def unload_all(self) -> None:
        """Unload all detectors."""
        for name, detector in self.detectors.items():
            try:
                detector.unload_model()
                self.logger.info(f"Unloaded detector: {name}")
            except Exception as e:
                self.logger.error(f"Error unloading detector {name}: {e}")


# Global detection manager instance
detection_manager = DetectionManager()
