"""
Image Segmentation Module

Provides comprehensive image segmentation capabilities including:
- Semantic segmentation (pixel-wise classification)
- Instance segmentation (individual object separation)
- Panoptic segmentation (combined semantic + instance)
- Mask generation and manipulation
- Background removal
- Object extraction

Integrates with NEXUS modules for storage and processing.
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
from datetime import datetime

logger = logging.getLogger(__name__)


class SegmentationMask:
    """
    Represents a segmentation mask with utilities.
    """

    def __init__(
        self,
        mask: np.ndarray,
        label: str,
        class_id: int,
        confidence: float = 1.0,
        bbox: Optional[Dict[str, float]] = None
    ):
        """
        Initialize segmentation mask.

        Args:
            mask: Binary or multi-class mask array
            label: Segment label
            class_id: Class identifier
            confidence: Prediction confidence
            bbox: Optional bounding box
        """
        self.mask = mask
        self.label = label
        self.class_id = class_id
        self.confidence = confidence
        self.bbox = bbox or self._compute_bbox()
        self.timestamp = datetime.utcnow()

    def _compute_bbox(self) -> Dict[str, float]:
        """Compute bounding box from mask."""
        try:
            rows = np.any(self.mask, axis=1)
            cols = np.any(self.mask, axis=0)
            rmin, rmax = np.where(rows)[0][[0, -1]]
            cmin, cmax = np.where(cols)[0][[0, -1]]

            return {
                'x': float(cmin),
                'y': float(rmin),
                'width': float(cmax - cmin),
                'height': float(rmax - rmin)
            }
        except:
            return {'x': 0, 'y': 0, 'width': 0, 'height': 0}

    def get_area(self) -> int:
        """Get mask area in pixels."""
        return int(np.sum(self.mask > 0))

    def get_contour(self) -> List[Tuple[int, int]]:
        """Extract mask contour points."""
        try:
            import cv2
            mask_uint8 = (self.mask * 255).astype(np.uint8)
            contours, _ = cv2.findContours(mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                contour = contours[0].reshape(-1, 2)
                return [(int(x), int(y)) for x, y in contour]
            return []
        except Exception as e:
            logging.warning(f"Error extracting contour: {e}")
            return []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'label': self.label,
            'class_id': self.class_id,
            'confidence': float(self.confidence),
            'bbox': self.bbox,
            'area': self.get_area(),
            'mask_shape': self.mask.shape,
            'timestamp': self.timestamp.isoformat()
        }

    def to_rle(self) -> Dict[str, Any]:
        """Convert mask to Run-Length Encoding (RLE)."""
        try:
            flat_mask = self.mask.flatten()
            rle = []
            current_val = flat_mask[0]
            count = 1

            for val in flat_mask[1:]:
                if val == current_val:
                    count += 1
                else:
                    rle.append(int(count))
                    current_val = val
                    count = 1
            rle.append(int(count))

            return {
                'counts': rle,
                'size': self.mask.shape,
                'label': self.label
            }
        except Exception as e:
            logging.error(f"Error creating RLE: {e}")
            return {}

    @staticmethod
    def from_rle(rle_data: Dict[str, Any]) -> 'SegmentationMask':
        """Create mask from RLE data."""
        try:
            counts = rle_data['counts']
            size = tuple(rle_data['size'])
            label = rle_data.get('label', 'unknown')

            # Decode RLE
            flat_mask = np.zeros(size[0] * size[1], dtype=np.uint8)
            pos = 0
            val = 0

            for count in counts:
                flat_mask[pos:pos + count] = val
                pos += count
                val = 1 - val

            mask = flat_mask.reshape(size)
            return SegmentationMask(mask, label, 0)

        except Exception as e:
            logging.error(f"Error decoding RLE: {e}")
            raise

    def __repr__(self) -> str:
        return f"<SegmentationMask(label={self.label}, area={self.get_area()})>"


class BaseSegmenter(ABC):
    """
    Abstract base class for segmentation models.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize segmenter.

        Args:
            model_path: Path to model weights
            config: Segmenter configuration
        """
        self.model_path = model_path
        self.config = config or {}
        self.model = None
        self.is_loaded = False
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    def load_model(self) -> bool:
        """Load the segmentation model."""
        pass

    @abstractmethod
    def segment(
        self,
        image: Union[str, np.ndarray, Image.Image],
        **kwargs
    ) -> List[SegmentationMask]:
        """
        Segment image.

        Args:
            image: Input image
            **kwargs: Segmentation parameters

        Returns:
            List of segmentation masks
        """
        pass

    def segment_batch(
        self,
        images: List[Union[str, np.ndarray, Image.Image]],
        **kwargs
    ) -> List[List[SegmentationMask]]:
        """
        Segment multiple images.

        Args:
            images: List of images
            **kwargs: Segmentation parameters

        Returns:
            List of segmentation results for each image
        """
        results = []
        for image in images:
            try:
                masks = self.segment(image, **kwargs)
                results.append(masks)
            except Exception as e:
                self.logger.error(f"Error segmenting image: {e}")
                results.append([])
        return results

    def unload_model(self) -> bool:
        """Unload model from memory."""
        try:
            self.model = None
            self.is_loaded = False
            self.logger.info("Model unloaded successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error unloading model: {e}")
            return False


class SemanticSegmenter(BaseSegmenter):
    """
    Semantic segmentation - assigns class label to each pixel.
    """

    def __init__(
        self,
        model_path: str,
        num_classes: int = 21,
        class_labels: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize semantic segmenter.

        Args:
            model_path: Path to segmentation model
            num_classes: Number of segmentation classes
            class_labels: List of class names
            config: Model configuration
        """
        super().__init__(model_path, config)
        self.num_classes = num_classes
        self.class_labels = class_labels or [f"class_{i}" for i in range(num_classes)]
        self.input_size = self.config.get('input_size', (512, 512))

    def load_model(self) -> bool:
        """Load semantic segmentation model."""
        try:
            import tensorflow as tf
            from tensorflow import keras

            self.model = keras.models.load_model(self.model_path)
            self.is_loaded = True
            self.logger.info(f"Loaded semantic segmentation model from {self.model_path}")
            return True

        except ImportError:
            self.logger.error("TensorFlow not installed. Install with: pip install tensorflow")
            return False
        except Exception as e:
            self.logger.error(f"Error loading model: {e}")
            return False

    def segment(
        self,
        image: Union[str, np.ndarray, Image.Image],
        confidence_threshold: float = 0.5,
        return_visualization: bool = False
    ) -> List[SegmentationMask]:
        """
        Perform semantic segmentation.

        Args:
            image: Input image
            confidence_threshold: Minimum confidence for each pixel
            return_visualization: Include visualization data

        Returns:
            List of segmentation masks (one per class)
        """
        if not self.is_loaded:
            self.load_model()

        try:
            import tensorflow as tf
            from tensorflow import keras

            # Load and preprocess image
            if isinstance(image, str):
                image = Image.open(image).convert('RGB')
            elif isinstance(image, np.ndarray):
                image = Image.fromarray(image)

            original_size = image.size
            image_resized = image.resize(self.input_size)

            # Convert to array and normalize
            img_array = keras.preprocessing.image.img_to_array(image_resized)
            img_array = np.expand_dims(img_array, axis=0) / 255.0

            # Run segmentation
            start_time = time.time()
            predictions = self.model.predict(img_array)[0]
            processing_time = (time.time() - start_time) * 1000

            # Get class for each pixel
            segmentation_map = np.argmax(predictions, axis=-1)

            # Resize back to original size
            segmentation_map_resized = np.array(
                Image.fromarray(segmentation_map.astype(np.uint8)).resize(
                    original_size,
                    Image.NEAREST
                )
            )

            # Extract individual class masks
            masks = []
            for class_id in range(self.num_classes):
                class_mask = (segmentation_map_resized == class_id).astype(np.uint8)

                # Skip if mask is mostly empty
                if np.sum(class_mask) < 100:
                    continue

                # Get confidence for this class
                class_confidences = predictions[:, :, class_id]
                avg_confidence = float(np.mean(class_confidences[segmentation_map == class_id]))

                if avg_confidence < confidence_threshold:
                    continue

                mask = SegmentationMask(
                    mask=class_mask,
                    label=self.class_labels[class_id],
                    class_id=class_id,
                    confidence=avg_confidence
                )
                masks.append(mask)

            self.logger.info(f"Segmented image into {len(masks)} classes in {processing_time:.2f}ms")
            return masks

        except Exception as e:
            self.logger.error(f"Error during segmentation: {e}")
            raise

    def create_visualization(
        self,
        image: Union[np.ndarray, Image.Image],
        masks: List[SegmentationMask],
        alpha: float = 0.5
    ) -> np.ndarray:
        """
        Create visualization overlay of segmentation.

        Args:
            image: Original image
            masks: Segmentation masks
            alpha: Transparency of overlay

        Returns:
            Visualization image as numpy array
        """
        try:
            # Convert image to array
            if isinstance(image, Image.Image):
                image = np.array(image)

            # Create color map
            colors = self._generate_colors(len(masks))

            # Create overlay
            overlay = np.zeros_like(image)
            for idx, mask in enumerate(masks):
                color = colors[idx]
                for c in range(3):
                    overlay[:, :, c] = np.where(
                        mask.mask > 0,
                        color[c],
                        overlay[:, :, c]
                    )

            # Blend with original image
            result = (image * (1 - alpha) + overlay * alpha).astype(np.uint8)
            return result

        except Exception as e:
            self.logger.error(f"Error creating visualization: {e}")
            return image

    def _generate_colors(self, num_colors: int) -> List[Tuple[int, int, int]]:
        """Generate distinct colors for visualization."""
        import colorsys
        colors = []
        for i in range(num_colors):
            hue = i / num_colors
            rgb = colorsys.hsv_to_rgb(hue, 0.8, 0.9)
            colors.append(tuple(int(c * 255) for c in rgb))
        return colors


class InstanceSegmenter(BaseSegmenter):
    """
    Instance segmentation - separates individual object instances.
    """

    def __init__(
        self,
        model_path: str,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize instance segmenter.

        Args:
            model_path: Path to instance segmentation model
            config: Model configuration
        """
        super().__init__(model_path, config)
        self.confidence_threshold = self.config.get('confidence_threshold', 0.5)
        self.mask_threshold = self.config.get('mask_threshold', 0.5)

    def load_model(self) -> bool:
        """Load instance segmentation model (e.g., Mask R-CNN)."""
        try:
            import torch
            import torchvision

            # Load Mask R-CNN model
            if self.model_path and os.path.exists(self.model_path):
                self.model = torch.load(self.model_path)
            else:
                # Load pretrained Mask R-CNN
                self.model = torchvision.models.detection.maskrcnn_resnet50_fpn(pretrained=True)

            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            self.model.to(self.device)
            self.model.eval()

            self.is_loaded = True
            self.logger.info("Loaded instance segmentation model")
            return True

        except ImportError:
            self.logger.error("PyTorch not installed. Install with: pip install torch torchvision")
            return False
        except Exception as e:
            self.logger.error(f"Error loading model: {e}")
            return False

    def segment(
        self,
        image: Union[str, np.ndarray, Image.Image],
        confidence_threshold: Optional[float] = None,
        max_instances: int = 100
    ) -> List[SegmentationMask]:
        """
        Perform instance segmentation.

        Args:
            image: Input image
            confidence_threshold: Minimum confidence
            max_instances: Maximum number of instances

        Returns:
            List of instance masks
        """
        if not self.is_loaded:
            self.load_model()

        try:
            import torch
            import torchvision.transforms as T

            # Load image
            if isinstance(image, str):
                image = Image.open(image).convert('RGB')
            elif isinstance(image, np.ndarray):
                image = Image.fromarray(image)

            # Preprocess
            transform = T.Compose([T.ToTensor()])
            img_tensor = transform(image).to(self.device)

            # Run inference
            start_time = time.time()
            with torch.no_grad():
                predictions = self.model([img_tensor])[0]
            processing_time = (time.time() - start_time) * 1000

            # Extract masks
            conf_thresh = confidence_threshold or self.confidence_threshold
            masks = []

            scores = predictions['scores'].cpu().numpy()
            labels = predictions['labels'].cpu().numpy()
            boxes = predictions['boxes'].cpu().numpy()
            pred_masks = predictions['masks'].cpu().numpy()

            for idx in range(min(len(scores), max_instances)):
                if scores[idx] < conf_thresh:
                    continue

                # Get mask (threshold at 0.5)
                mask = (pred_masks[idx, 0] > self.mask_threshold).astype(np.uint8)

                # Get bounding box
                box = boxes[idx]
                bbox = {
                    'x': float(box[0]),
                    'y': float(box[1]),
                    'width': float(box[2] - box[0]),
                    'height': float(box[3] - box[1])
                }

                # COCO class names (simplified)
                class_names = self._get_coco_classes()
                label = class_names.get(int(labels[idx]), f"class_{labels[idx]}")

                seg_mask = SegmentationMask(
                    mask=mask,
                    label=label,
                    class_id=int(labels[idx]),
                    confidence=float(scores[idx]),
                    bbox=bbox
                )
                masks.append(seg_mask)

            self.logger.info(f"Detected {len(masks)} instances in {processing_time:.2f}ms")
            return masks

        except Exception as e:
            self.logger.error(f"Error during instance segmentation: {e}")
            raise

    def _get_coco_classes(self) -> Dict[int, str]:
        """Get COCO class names (simplified)."""
        return {
            1: 'person', 2: 'bicycle', 3: 'car', 4: 'motorcycle', 5: 'airplane',
            6: 'bus', 7: 'train', 8: 'truck', 9: 'boat', 10: 'traffic light',
            # Add more as needed...
        }


class BackgroundRemover:
    """
    Removes background from images using segmentation.
    """

    def __init__(
        self,
        segmenter: Optional[BaseSegmenter] = None,
        method: str = "grabcut"
    ):
        """
        Initialize background remover.

        Args:
            segmenter: Optional segmenter to use
            method: Method to use (grabcut, threshold, segmentation)
        """
        self.segmenter = segmenter
        self.method = method
        self.logger = logging.getLogger(f"{__name__}.BackgroundRemover")

    def remove_background(
        self,
        image: Union[str, np.ndarray, Image.Image],
        foreground_hint: Optional[Dict[str, int]] = None,
        return_mask: bool = False
    ) -> Union[Image.Image, Tuple[Image.Image, np.ndarray]]:
        """
        Remove background from image.

        Args:
            image: Input image
            foreground_hint: Optional hint for foreground region (bbox)
            return_mask: Whether to return the mask

        Returns:
            Image with transparent background (and mask if requested)
        """
        try:
            # Load image
            if isinstance(image, str):
                image = Image.open(image).convert('RGB')
            elif isinstance(image, np.ndarray):
                image = Image.fromarray(image)

            img_array = np.array(image)

            if self.method == "grabcut":
                mask = self._grabcut_segmentation(img_array, foreground_hint)
            elif self.method == "segmentation" and self.segmenter:
                mask = self._segmenter_based(image)
            else:
                mask = self._simple_threshold(img_array)

            # Apply mask to create transparent background
            result = Image.fromarray(img_array).convert('RGBA')
            result.putalpha(Image.fromarray((mask * 255).astype(np.uint8)))

            if return_mask:
                return result, mask
            return result

        except Exception as e:
            self.logger.error(f"Error removing background: {e}")
            raise

    def _grabcut_segmentation(
        self,
        image: np.ndarray,
        foreground_hint: Optional[Dict[str, int]] = None
    ) -> np.ndarray:
        """Use GrabCut algorithm for background removal."""
        try:
            import cv2

            mask = np.zeros(image.shape[:2], np.uint8)
            bgd_model = np.zeros((1, 65), np.float64)
            fgd_model = np.zeros((1, 65), np.float64)

            # Define rectangle containing foreground
            if foreground_hint:
                rect = (
                    foreground_hint['x'],
                    foreground_hint['y'],
                    foreground_hint['width'],
                    foreground_hint['height']
                )
            else:
                # Use center region as hint
                h, w = image.shape[:2]
                margin = min(h, w) // 10
                rect = (margin, margin, w - 2 * margin, h - 2 * margin)

            # Run GrabCut
            cv2.grabCut(image, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)

            # Create binary mask
            binary_mask = np.where((mask == 2) | (mask == 0), 0, 1).astype(np.uint8)

            return binary_mask

        except ImportError:
            self.logger.error("OpenCV not installed. Install with: pip install opencv-python")
            raise
        except Exception as e:
            self.logger.error(f"Error in GrabCut: {e}")
            raise

    def _segmenter_based(self, image: Image.Image) -> np.ndarray:
        """Use segmentation model for background removal."""
        if not self.segmenter:
            raise ValueError("No segmenter provided")

        masks = self.segmenter.segment(image)

        # Combine foreground masks
        combined_mask = np.zeros(masks[0].mask.shape, dtype=np.uint8)
        for mask in masks:
            if mask.label != 'background':
                combined_mask = np.maximum(combined_mask, mask.mask)

        return combined_mask

    def _simple_threshold(self, image: np.ndarray) -> np.ndarray:
        """Simple threshold-based background removal."""
        try:
            import cv2

            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

            # Apply threshold
            _, mask = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)

            return (mask > 0).astype(np.uint8)

        except Exception as e:
            self.logger.error(f"Error in threshold method: {e}")
            raise


class MaskProcessor:
    """
    Utilities for processing and manipulating segmentation masks.
    """

    def __init__(self):
        """Initialize mask processor."""
        self.logger = logging.getLogger(f"{__name__}.MaskProcessor")

    def merge_masks(
        self,
        masks: List[SegmentationMask],
        overlap_strategy: str = "union"
    ) -> SegmentationMask:
        """
        Merge multiple masks into one.

        Args:
            masks: List of masks to merge
            overlap_strategy: How to handle overlaps (union, intersection, average)

        Returns:
            Merged mask
        """
        if not masks:
            raise ValueError("No masks provided")

        if len(masks) == 1:
            return masks[0]

        # Get common shape
        shape = masks[0].mask.shape
        merged = np.zeros(shape, dtype=np.float32)

        if overlap_strategy == "union":
            for mask in masks:
                merged = np.maximum(merged, mask.mask.astype(np.float32))
        elif overlap_strategy == "intersection":
            merged = np.ones(shape, dtype=np.float32)
            for mask in masks:
                merged = np.minimum(merged, mask.mask.astype(np.float32))
        elif overlap_strategy == "average":
            for mask in masks:
                merged += mask.mask.astype(np.float32)
            merged /= len(masks)

        return SegmentationMask(
            mask=(merged > 0.5).astype(np.uint8),
            label="merged",
            class_id=-1
        )

    def refine_mask(
        self,
        mask: SegmentationMask,
        method: str = "morphology",
        kernel_size: int = 5
    ) -> SegmentationMask:
        """
        Refine mask boundaries.

        Args:
            mask: Input mask
            method: Refinement method
            kernel_size: Kernel size for morphological operations

        Returns:
            Refined mask
        """
        try:
            import cv2

            refined = mask.mask.copy()

            if method == "morphology":
                kernel = np.ones((kernel_size, kernel_size), np.uint8)
                # Close small holes
                refined = cv2.morphologyEx(refined, cv2.MORPH_CLOSE, kernel)
                # Remove small noise
                refined = cv2.morphologyEx(refined, cv2.MORPH_OPEN, kernel)

            elif method == "smooth":
                refined = cv2.GaussianBlur(refined.astype(np.float32), (kernel_size, kernel_size), 0)
                refined = (refined > 0.5).astype(np.uint8)

            return SegmentationMask(
                mask=refined,
                label=mask.label,
                class_id=mask.class_id,
                confidence=mask.confidence
            )

        except Exception as e:
            self.logger.error(f"Error refining mask: {e}")
            return mask

    def extract_largest_component(self, mask: SegmentationMask) -> SegmentationMask:
        """Extract the largest connected component from mask."""
        try:
            import cv2

            # Find connected components
            num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask.mask, connectivity=8)

            if num_labels <= 1:
                return mask

            # Find largest component (excluding background)
            largest_label = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])

            # Create new mask with only largest component
            largest_mask = (labels == largest_label).astype(np.uint8)

            return SegmentationMask(
                mask=largest_mask,
                label=mask.label,
                class_id=mask.class_id,
                confidence=mask.confidence
            )

        except Exception as e:
            self.logger.error(f"Error extracting largest component: {e}")
            return mask


# Global instances
mask_processor = MaskProcessor()
