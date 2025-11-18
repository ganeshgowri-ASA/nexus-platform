"""
Annotation Tools Module

Provides comprehensive annotation capabilities including:
- Bounding box annotation
- Polygon and segmentation mask annotation
- Point and landmark annotation
- Label management and categorization
- Annotation validation and quality control
- Annotation import/export
- Collaborative annotation support
- Annotation statistics and reporting

Integrates with NEXUS database for annotation storage.
"""

import logging
import json
from typing import Optional, Dict, Any, List, Union, Tuple
from pathlib import Path
from datetime import datetime
from enum import Enum
import numpy as np
from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)


class AnnotationType(str, Enum):
    """Annotation types."""
    BOUNDING_BOX = "bbox"
    POLYGON = "polygon"
    SEGMENTATION_MASK = "mask"
    POINT = "point"
    POLYLINE = "polyline"
    KEYPOINT = "keypoint"


class Annotation:
    """
    Represents a single annotation.
    """

    def __init__(
        self,
        annotation_id: str,
        image_id: str,
        annotation_type: AnnotationType,
        label: str,
        data: Dict[str, Any],
        annotator_id: Optional[str] = None,
        confidence: float = 1.0,
        verified: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize annotation.

        Args:
            annotation_id: Unique annotation identifier
            image_id: Associated image identifier
            annotation_type: Type of annotation
            label: Label/category
            data: Annotation data (bbox, polygon points, etc.)
            annotator_id: ID of person who created annotation
            confidence: Confidence score
            verified: Whether annotation is verified
            metadata: Additional metadata
        """
        self.annotation_id = annotation_id
        self.image_id = image_id
        self.annotation_type = annotation_type
        self.label = label
        self.data = data
        self.annotator_id = annotator_id
        self.confidence = confidence
        self.verified = verified
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'annotation_id': self.annotation_id,
            'image_id': self.image_id,
            'annotation_type': self.annotation_type.value if isinstance(self.annotation_type, AnnotationType) else self.annotation_type,
            'label': self.label,
            'data': self.data,
            'annotator_id': self.annotator_id,
            'confidence': self.confidence,
            'verified': self.verified,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Annotation':
        """Create annotation from dictionary."""
        ann = Annotation(
            annotation_id=data['annotation_id'],
            image_id=data['image_id'],
            annotation_type=AnnotationType(data['annotation_type']),
            label=data['label'],
            data=data['data'],
            annotator_id=data.get('annotator_id'),
            confidence=data.get('confidence', 1.0),
            verified=data.get('verified', False),
            metadata=data.get('metadata', {})
        )

        if 'created_at' in data:
            ann.created_at = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data:
            ann.updated_at = datetime.fromisoformat(data['updated_at'])

        return ann

    def __repr__(self) -> str:
        return f"<Annotation(id={self.annotation_id}, type={self.annotation_type}, label={self.label})>"


class BoundingBoxAnnotator:
    """
    Creates and manages bounding box annotations.
    """

    def __init__(self):
        """Initialize bounding box annotator."""
        self.logger = logging.getLogger(f"{__name__}.BoundingBoxAnnotator")

    def create_annotation(
        self,
        annotation_id: str,
        image_id: str,
        label: str,
        x: float,
        y: float,
        width: float,
        height: float,
        **kwargs
    ) -> Annotation:
        """
        Create bounding box annotation.

        Args:
            annotation_id: Annotation identifier
            image_id: Image identifier
            label: Object label
            x: Top-left x coordinate
            y: Top-left y coordinate
            width: Box width
            height: Box height
            **kwargs: Additional parameters

        Returns:
            Annotation object
        """
        data = {
            'x': x,
            'y': y,
            'width': width,
            'height': height
        }

        return Annotation(
            annotation_id=annotation_id,
            image_id=image_id,
            annotation_type=AnnotationType.BOUNDING_BOX,
            label=label,
            data=data,
            **kwargs
        )

    def validate_bbox(
        self,
        bbox: Dict[str, float],
        image_width: int,
        image_height: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate bounding box.

        Args:
            bbox: Bounding box dict
            image_width: Image width
            image_height: Image height

        Returns:
            Tuple of (is_valid, error_message)
        """
        x = bbox.get('x', 0)
        y = bbox.get('y', 0)
        w = bbox.get('width', 0)
        h = bbox.get('height', 0)

        if x < 0 or y < 0:
            return False, "Coordinates cannot be negative"

        if w <= 0 or h <= 0:
            return False, "Width and height must be positive"

        if x + w > image_width or y + h > image_height:
            return False, "Bounding box extends beyond image boundaries"

        return True, None

    def draw_bbox(
        self,
        image: Union[np.ndarray, Image.Image],
        bbox: Dict[str, float],
        label: Optional[str] = None,
        color: Tuple[int, int, int] = (255, 0, 0),
        thickness: int = 2
    ) -> Image.Image:
        """
        Draw bounding box on image.

        Args:
            image: Input image
            bbox: Bounding box dict
            label: Optional label to draw
            color: Box color
            thickness: Line thickness

        Returns:
            Image with drawn box
        """
        # Convert to PIL Image
        if isinstance(image, np.ndarray):
            image = Image.fromarray(image)
        else:
            image = image.copy()

        draw = ImageDraw.Draw(image)

        # Draw rectangle
        x, y, w, h = bbox['x'], bbox['y'], bbox['width'], bbox['height']
        draw.rectangle(
            [x, y, x + w, y + h],
            outline=color,
            width=thickness
        )

        # Draw label if provided
        if label:
            draw.text((x, y - 15), label, fill=color)

        return image


class PolygonAnnotator:
    """
    Creates and manages polygon annotations.
    """

    def __init__(self):
        """Initialize polygon annotator."""
        self.logger = logging.getLogger(f"{__name__}.PolygonAnnotator")

    def create_annotation(
        self,
        annotation_id: str,
        image_id: str,
        label: str,
        points: List[Tuple[float, float]],
        **kwargs
    ) -> Annotation:
        """
        Create polygon annotation.

        Args:
            annotation_id: Annotation identifier
            image_id: Image identifier
            label: Object label
            points: List of (x, y) points
            **kwargs: Additional parameters

        Returns:
            Annotation object
        """
        data = {
            'points': points,
            'num_points': len(points)
        }

        return Annotation(
            annotation_id=annotation_id,
            image_id=image_id,
            annotation_type=AnnotationType.POLYGON,
            label=label,
            data=data,
            **kwargs
        )

    def validate_polygon(
        self,
        points: List[Tuple[float, float]],
        image_width: int,
        image_height: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate polygon.

        Args:
            points: List of points
            image_width: Image width
            image_height: Image height

        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(points) < 3:
            return False, "Polygon must have at least 3 points"

        for x, y in points:
            if x < 0 or y < 0 or x > image_width or y > image_height:
                return False, "Points must be within image boundaries"

        return True, None

    def draw_polygon(
        self,
        image: Union[np.ndarray, Image.Image],
        points: List[Tuple[float, float]],
        label: Optional[str] = None,
        color: Tuple[int, int, int] = (0, 255, 0),
        thickness: int = 2
    ) -> Image.Image:
        """
        Draw polygon on image.

        Args:
            image: Input image
            points: List of polygon points
            label: Optional label
            color: Polygon color
            thickness: Line thickness

        Returns:
            Image with drawn polygon
        """
        # Convert to PIL Image
        if isinstance(image, np.ndarray):
            image = Image.fromarray(image)
        else:
            image = image.copy()

        draw = ImageDraw.Draw(image)

        # Draw polygon
        draw.polygon(points, outline=color, width=thickness)

        # Draw label if provided
        if label and points:
            draw.text(points[0], label, fill=color)

        return image

    def polygon_to_mask(
        self,
        points: List[Tuple[float, float]],
        image_width: int,
        image_height: int
    ) -> np.ndarray:
        """
        Convert polygon to binary mask.

        Args:
            points: Polygon points
            image_width: Mask width
            image_height: Mask height

        Returns:
            Binary mask array
        """
        # Create blank image
        mask_img = Image.new('L', (image_width, image_height), 0)
        draw = ImageDraw.Draw(mask_img)

        # Draw filled polygon
        draw.polygon(points, fill=255)

        # Convert to array
        mask = np.array(mask_img) > 0
        return mask.astype(np.uint8)


class LabelManager:
    """
    Manages annotation labels and categories.
    """

    def __init__(self):
        """Initialize label manager."""
        self.labels: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(f"{__name__}.LabelManager")

    def add_label(
        self,
        label_name: str,
        display_name: str,
        color: Optional[Tuple[int, int, int]] = None,
        category: Optional[str] = None,
        description: Optional[str] = None
    ) -> bool:
        """
        Add a new label.

        Args:
            label_name: Internal label name
            display_name: Display name
            color: RGB color for visualization
            category: Label category
            description: Label description

        Returns:
            True if successful
        """
        try:
            if label_name in self.labels:
                self.logger.warning(f"Label already exists: {label_name}")
                return False

            self.labels[label_name] = {
                'display_name': display_name,
                'color': color or self._generate_color(),
                'category': category,
                'description': description,
                'created_at': datetime.utcnow().isoformat()
            }

            self.logger.info(f"Added label: {label_name}")
            return True

        except Exception as e:
            self.logger.error(f"Error adding label: {e}")
            return False

    def get_label(self, label_name: str) -> Optional[Dict[str, Any]]:
        """Get label information."""
        return self.labels.get(label_name)

    def list_labels(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all labels.

        Args:
            category: Filter by category

        Returns:
            List of labels
        """
        labels = []
        for name, info in self.labels.items():
            if category is None or info.get('category') == category:
                labels.append({
                    'name': name,
                    **info
                })
        return labels

    def delete_label(self, label_name: str) -> bool:
        """Delete a label."""
        if label_name in self.labels:
            del self.labels[label_name]
            self.logger.info(f"Deleted label: {label_name}")
            return True
        return False

    def _generate_color(self) -> Tuple[int, int, int]:
        """Generate random color for label."""
        import random
        return (
            random.randint(50, 255),
            random.randint(50, 255),
            random.randint(50, 255)
        )

    def export_labels(self, output_path: str) -> bool:
        """
        Export labels to JSON file.

        Args:
            output_path: Output file path

        Returns:
            True if successful
        """
        try:
            with open(output_path, 'w') as f:
                json.dump(self.labels, f, indent=2)

            self.logger.info(f"Exported labels to {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error exporting labels: {e}")
            return False

    def import_labels(self, input_path: str) -> bool:
        """
        Import labels from JSON file.

        Args:
            input_path: Input file path

        Returns:
            True if successful
        """
        try:
            with open(input_path, 'r') as f:
                imported_labels = json.load(f)

            self.labels.update(imported_labels)
            self.logger.info(f"Imported {len(imported_labels)} labels from {input_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error importing labels: {e}")
            return False


class AnnotationValidator:
    """
    Validates annotation quality and consistency.
    """

    def __init__(self):
        """Initialize annotation validator."""
        self.logger = logging.getLogger(f"{__name__}.AnnotationValidator")

    def validate_annotation(
        self,
        annotation: Annotation,
        image_width: int,
        image_height: int
    ) -> Tuple[bool, List[str]]:
        """
        Validate annotation.

        Args:
            annotation: Annotation to validate
            image_width: Image width
            image_height: Image height

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        # Validate based on type
        if annotation.annotation_type == AnnotationType.BOUNDING_BOX:
            bbox_validator = BoundingBoxAnnotator()
            valid, error = bbox_validator.validate_bbox(
                annotation.data,
                image_width,
                image_height
            )
            if not valid:
                issues.append(error)

        elif annotation.annotation_type == AnnotationType.POLYGON:
            polygon_validator = PolygonAnnotator()
            valid, error = polygon_validator.validate_polygon(
                annotation.data.get('points', []),
                image_width,
                image_height
            )
            if not valid:
                issues.append(error)

        # Validate confidence
        if annotation.confidence < 0 or annotation.confidence > 1:
            issues.append("Confidence must be between 0 and 1")

        # Validate label
        if not annotation.label or annotation.label.strip() == "":
            issues.append("Label cannot be empty")

        return len(issues) == 0, issues


class AnnotationStatistics:
    """
    Computes statistics on annotations.
    """

    def __init__(self):
        """Initialize annotation statistics."""
        self.logger = logging.getLogger(f"{__name__}.AnnotationStatistics")

    def compute_statistics(
        self,
        annotations: List[Annotation]
    ) -> Dict[str, Any]:
        """
        Compute statistics on annotations.

        Args:
            annotations: List of annotations

        Returns:
            Statistics dictionary
        """
        if not annotations:
            return {}

        # Count by type
        type_counts = {}
        for ann in annotations:
            ann_type = ann.annotation_type.value if isinstance(ann.annotation_type, AnnotationType) else ann.annotation_type
            type_counts[ann_type] = type_counts.get(ann_type, 0) + 1

        # Count by label
        label_counts = {}
        for ann in annotations:
            label_counts[ann.label] = label_counts.get(ann.label, 0) + 1

        # Count by annotator
        annotator_counts = {}
        for ann in annotations:
            if ann.annotator_id:
                annotator_counts[ann.annotator_id] = annotator_counts.get(ann.annotator_id, 0) + 1

        # Verification stats
        verified_count = sum(1 for ann in annotations if ann.verified)

        # Confidence stats
        confidences = [ann.confidence for ann in annotations]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0

        return {
            'total_annotations': len(annotations),
            'by_type': type_counts,
            'by_label': label_counts,
            'by_annotator': annotator_counts,
            'verified_count': verified_count,
            'verification_rate': verified_count / len(annotations) if annotations else 0,
            'average_confidence': avg_confidence,
            'unique_images': len(set(ann.image_id for ann in annotations)),
            'unique_labels': len(label_counts)
        }


class AnnotationTool:
    """
    Complete annotation tool with all functionality.
    """

    def __init__(self):
        """Initialize annotation tool."""
        self.bbox_annotator = BoundingBoxAnnotator()
        self.polygon_annotator = PolygonAnnotator()
        self.label_manager = LabelManager()
        self.validator = AnnotationValidator()
        self.statistics = AnnotationStatistics()
        self.annotations: Dict[str, List[Annotation]] = {}  # image_id -> annotations
        self.logger = logging.getLogger(f"{__name__}.AnnotationTool")

    def add_annotation(self, annotation: Annotation) -> bool:
        """
        Add annotation.

        Args:
            annotation: Annotation object

        Returns:
            True if successful
        """
        try:
            if annotation.image_id not in self.annotations:
                self.annotations[annotation.image_id] = []

            self.annotations[annotation.image_id].append(annotation)
            self.logger.info(f"Added annotation: {annotation.annotation_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error adding annotation: {e}")
            return False

    def get_annotations(
        self,
        image_id: str,
        label: Optional[str] = None
    ) -> List[Annotation]:
        """
        Get annotations for image.

        Args:
            image_id: Image identifier
            label: Filter by label

        Returns:
            List of annotations
        """
        annotations = self.annotations.get(image_id, [])

        if label:
            annotations = [ann for ann in annotations if ann.label == label]

        return annotations

    def delete_annotation(self, annotation_id: str) -> bool:
        """Delete annotation by ID."""
        for image_id, annotations in self.annotations.items():
            for idx, ann in enumerate(annotations):
                if ann.annotation_id == annotation_id:
                    del annotations[idx]
                    self.logger.info(f"Deleted annotation: {annotation_id}")
                    return True
        return False

    def export_annotations(
        self,
        output_path: str,
        image_ids: Optional[List[str]] = None
    ) -> bool:
        """
        Export annotations to JSON file.

        Args:
            output_path: Output file path
            image_ids: Optional list of image IDs to export

        Returns:
            True if successful
        """
        try:
            export_data = {}

            for image_id, annotations in self.annotations.items():
                if image_ids is None or image_id in image_ids:
                    export_data[image_id] = [
                        ann.to_dict() for ann in annotations
                    ]

            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2)

            self.logger.info(f"Exported annotations to {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error exporting annotations: {e}")
            return False

    def import_annotations(self, input_path: str) -> bool:
        """
        Import annotations from JSON file.

        Args:
            input_path: Input file path

        Returns:
            True if successful
        """
        try:
            with open(input_path, 'r') as f:
                import_data = json.load(f)

            for image_id, annotations_data in import_data.items():
                if image_id not in self.annotations:
                    self.annotations[image_id] = []

                for ann_data in annotations_data:
                    ann = Annotation.from_dict(ann_data)
                    self.annotations[image_id].append(ann)

            self.logger.info(f"Imported annotations from {input_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error importing annotations: {e}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """Get annotation statistics."""
        all_annotations = []
        for annotations in self.annotations.values():
            all_annotations.extend(annotations)

        return self.statistics.compute_statistics(all_annotations)


# Global annotation tool instance
annotation_tool = AnnotationTool()
