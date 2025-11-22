"""
Image Preprocessing Module

Provides comprehensive image preprocessing utilities including:
- Normalization and standardization
- Image augmentation
- Resizing and cropping
- Color correction and adjustment
- Noise reduction and filtering
- Histogram equalization
- Format conversion
- Batch preprocessing pipelines

Production-ready with error handling and logging.
"""

import logging
import os
from typing import Optional, Dict, Any, List, Union, Tuple, Callable
from pathlib import Path
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ResizeMode(str, Enum):
    """Image resize modes."""
    FIT = "fit"  # Fit within bounds
    FILL = "fill"  # Fill bounds, crop if needed
    STRETCH = "stretch"  # Stretch to exact size
    PAD = "pad"  # Pad to exact size


class ColorSpace(str, Enum):
    """Color space types."""
    RGB = "RGB"
    BGR = "BGR"
    GRAY = "L"
    HSV = "HSV"
    LAB = "LAB"


class ImageNormalizer:
    """
    Normalizes images for model input.
    """

    def __init__(
        self,
        method: str = "standard",
        mean: Optional[List[float]] = None,
        std: Optional[List[float]] = None
    ):
        """
        Initialize normalizer.

        Args:
            method: Normalization method (standard, minmax, zscore)
            mean: Mean values for each channel
            std: Standard deviation for each channel
        """
        self.method = method
        self.mean = np.array(mean) if mean else np.array([0.485, 0.456, 0.406])  # ImageNet
        self.std = np.array(std) if std else np.array([0.229, 0.224, 0.225])  # ImageNet
        self.logger = logging.getLogger(f"{__name__}.ImageNormalizer")

    def normalize(
        self,
        image: Union[np.ndarray, Image.Image]
    ) -> np.ndarray:
        """
        Normalize image.

        Args:
            image: Input image

        Returns:
            Normalized image as numpy array
        """
        try:
            # Convert to numpy array
            if isinstance(image, Image.Image):
                img_array = np.array(image).astype(np.float32)
            else:
                img_array = image.astype(np.float32)

            # Ensure values are in [0, 255] range
            if img_array.max() <= 1.0:
                img_array = img_array * 255.0

            if self.method == "standard":
                # Standardize using mean and std
                img_array = img_array / 255.0
                if len(img_array.shape) == 3 and img_array.shape[2] == 3:
                    img_array = (img_array - self.mean) / self.std

            elif self.method == "minmax":
                # Min-max normalization to [0, 1]
                img_array = (img_array - img_array.min()) / (img_array.max() - img_array.min() + 1e-8)

            elif self.method == "zscore":
                # Z-score normalization
                img_array = (img_array - img_array.mean()) / (img_array.std() + 1e-8)

            else:
                raise ValueError(f"Unsupported normalization method: {self.method}")

            return img_array

        except Exception as e:
            self.logger.error(f"Error normalizing image: {e}")
            raise

    def denormalize(
        self,
        image: np.ndarray
    ) -> np.ndarray:
        """
        Denormalize image back to [0, 255] range.

        Args:
            image: Normalized image

        Returns:
            Denormalized image
        """
        try:
            if self.method == "standard":
                if len(image.shape) == 3 and image.shape[2] == 3:
                    image = image * self.std + self.mean
                image = image * 255.0

            elif self.method in ["minmax", "zscore"]:
                # Scale back to [0, 255]
                image = ((image - image.min()) / (image.max() - image.min() + 1e-8)) * 255.0

            return np.clip(image, 0, 255).astype(np.uint8)

        except Exception as e:
            self.logger.error(f"Error denormalizing image: {e}")
            raise


class ImageResizer:
    """
    Resizes images with various modes.
    """

    def __init__(
        self,
        target_size: Tuple[int, int],
        mode: ResizeMode = ResizeMode.FIT,
        interpolation: int = Image.LANCZOS
    ):
        """
        Initialize resizer.

        Args:
            target_size: Target size (width, height)
            mode: Resize mode
            interpolation: Interpolation method
        """
        self.target_size = target_size
        self.mode = mode
        self.interpolation = interpolation
        self.logger = logging.getLogger(f"{__name__}.ImageResizer")

    def resize(
        self,
        image: Union[np.ndarray, Image.Image],
        maintain_aspect: bool = True
    ) -> Image.Image:
        """
        Resize image.

        Args:
            image: Input image
            maintain_aspect: Whether to maintain aspect ratio

        Returns:
            Resized image
        """
        try:
            # Convert to PIL Image
            if isinstance(image, np.ndarray):
                image = Image.fromarray(image)

            target_w, target_h = self.target_size
            orig_w, orig_h = image.size

            if self.mode == ResizeMode.STRETCH:
                # Simply resize to target size
                return image.resize(self.target_size, self.interpolation)

            elif self.mode == ResizeMode.FIT:
                # Fit within bounds, maintaining aspect ratio
                if maintain_aspect:
                    image.thumbnail(self.target_size, self.interpolation)
                    return image
                else:
                    return image.resize(self.target_size, self.interpolation)

            elif self.mode == ResizeMode.FILL:
                # Fill bounds, crop if needed
                aspect_ratio = orig_w / orig_h
                target_ratio = target_w / target_h

                if aspect_ratio > target_ratio:
                    # Image is wider, fit height and crop width
                    new_h = target_h
                    new_w = int(target_h * aspect_ratio)
                else:
                    # Image is taller, fit width and crop height
                    new_w = target_w
                    new_h = int(target_w / aspect_ratio)

                # Resize
                image = image.resize((new_w, new_h), self.interpolation)

                # Center crop
                left = (new_w - target_w) // 2
                top = (new_h - target_h) // 2
                return image.crop((left, top, left + target_w, top + target_h))

            elif self.mode == ResizeMode.PAD:
                # Pad to exact size
                if maintain_aspect:
                    image.thumbnail(self.target_size, self.interpolation)

                # Create new image with target size
                new_image = Image.new('RGB', self.target_size, (0, 0, 0))

                # Paste resized image in center
                paste_x = (target_w - image.width) // 2
                paste_y = (target_h - image.height) // 2
                new_image.paste(image, (paste_x, paste_y))

                return new_image

        except Exception as e:
            self.logger.error(f"Error resizing image: {e}")
            raise


class ImageAugmenter:
    """
    Performs image augmentation for data augmentation.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize augmenter.

        Args:
            config: Augmentation configuration
        """
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.ImageAugmenter")

    def augment(
        self,
        image: Union[np.ndarray, Image.Image],
        augmentations: Optional[List[str]] = None
    ) -> Image.Image:
        """
        Apply augmentations to image.

        Args:
            image: Input image
            augmentations: List of augmentation names to apply

        Returns:
            Augmented image
        """
        try:
            # Convert to PIL Image
            if isinstance(image, np.ndarray):
                image = Image.fromarray(image)

            # Default augmentations
            if augmentations is None:
                augmentations = ['flip', 'rotate', 'brightness', 'contrast']

            # Apply each augmentation
            for aug in augmentations:
                if aug == 'flip_horizontal':
                    image = self.flip_horizontal(image)
                elif aug == 'flip_vertical':
                    image = self.flip_vertical(image)
                elif aug == 'rotate':
                    angle = np.random.uniform(-30, 30)
                    image = self.rotate(image, angle)
                elif aug == 'brightness':
                    factor = np.random.uniform(0.7, 1.3)
                    image = self.adjust_brightness(image, factor)
                elif aug == 'contrast':
                    factor = np.random.uniform(0.7, 1.3)
                    image = self.adjust_contrast(image, factor)
                elif aug == 'saturation':
                    factor = np.random.uniform(0.7, 1.3)
                    image = self.adjust_saturation(image, factor)
                elif aug == 'blur':
                    image = self.blur(image)
                elif aug == 'noise':
                    image = self.add_noise(image)
                elif aug == 'crop':
                    image = self.random_crop(image)

            return image

        except Exception as e:
            self.logger.error(f"Error augmenting image: {e}")
            raise

    def flip_horizontal(self, image: Image.Image) -> Image.Image:
        """Flip image horizontally."""
        return ImageOps.mirror(image)

    def flip_vertical(self, image: Image.Image) -> Image.Image:
        """Flip image vertically."""
        return ImageOps.flip(image)

    def rotate(self, image: Image.Image, angle: float) -> Image.Image:
        """Rotate image by angle."""
        return image.rotate(angle, fillcolor=(0, 0, 0))

    def adjust_brightness(self, image: Image.Image, factor: float) -> Image.Image:
        """Adjust image brightness."""
        enhancer = ImageEnhance.Brightness(image)
        return enhancer.enhance(factor)

    def adjust_contrast(self, image: Image.Image, factor: float) -> Image.Image:
        """Adjust image contrast."""
        enhancer = ImageEnhance.Contrast(image)
        return enhancer.enhance(factor)

    def adjust_saturation(self, image: Image.Image, factor: float) -> Image.Image:
        """Adjust image saturation."""
        enhancer = ImageEnhance.Color(image)
        return enhancer.enhance(factor)

    def blur(self, image: Image.Image, radius: float = 2.0) -> Image.Image:
        """Apply Gaussian blur."""
        return image.filter(ImageFilter.GaussianBlur(radius=radius))

    def add_noise(
        self,
        image: Image.Image,
        noise_level: float = 0.05
    ) -> Image.Image:
        """Add random noise to image."""
        img_array = np.array(image).astype(np.float32)
        noise = np.random.normal(0, noise_level * 255, img_array.shape)
        noisy = np.clip(img_array + noise, 0, 255).astype(np.uint8)
        return Image.fromarray(noisy)

    def random_crop(
        self,
        image: Image.Image,
        crop_ratio: float = 0.8
    ) -> Image.Image:
        """Randomly crop image."""
        w, h = image.size
        crop_w = int(w * crop_ratio)
        crop_h = int(h * crop_ratio)

        left = np.random.randint(0, w - crop_w + 1)
        top = np.random.randint(0, h - crop_h + 1)

        return image.crop((left, top, left + crop_w, top + crop_h))

    def augment_batch(
        self,
        images: List[Union[np.ndarray, Image.Image]],
        augmentations: Optional[List[str]] = None
    ) -> List[Image.Image]:
        """
        Augment multiple images.

        Args:
            images: List of images
            augmentations: List of augmentation names

        Returns:
            List of augmented images
        """
        return [self.augment(img, augmentations) for img in images]


class ColorCorrector:
    """
    Performs color correction and adjustment.
    """

    def __init__(self):
        """Initialize color corrector."""
        self.logger = logging.getLogger(f"{__name__}.ColorCorrector")

    def auto_adjust(self, image: Union[np.ndarray, Image.Image]) -> Image.Image:
        """
        Automatically adjust image colors.

        Args:
            image: Input image

        Returns:
            Color-corrected image
        """
        try:
            # Convert to PIL Image
            if isinstance(image, np.ndarray):
                image = Image.fromarray(image)

            # Auto contrast
            image = ImageOps.autocontrast(image)

            # Equalize histogram
            image = ImageOps.equalize(image)

            return image

        except Exception as e:
            self.logger.error(f"Error auto-adjusting image: {e}")
            raise

    def white_balance(self, image: Union[np.ndarray, Image.Image]) -> Image.Image:
        """
        Apply white balance correction.

        Args:
            image: Input image

        Returns:
            White-balanced image
        """
        try:
            # Convert to numpy array
            if isinstance(image, Image.Image):
                img_array = np.array(image)
            else:
                img_array = image.copy()

            # Calculate average values for each channel
            avg_r = np.mean(img_array[:, :, 0])
            avg_g = np.mean(img_array[:, :, 1])
            avg_b = np.mean(img_array[:, :, 2])

            # Calculate overall average
            avg_gray = (avg_r + avg_g + avg_b) / 3

            # Calculate scaling factors
            scale_r = avg_gray / (avg_r + 1e-8)
            scale_g = avg_gray / (avg_g + 1e-8)
            scale_b = avg_gray / (avg_b + 1e-8)

            # Apply scaling
            img_array[:, :, 0] = np.clip(img_array[:, :, 0] * scale_r, 0, 255)
            img_array[:, :, 1] = np.clip(img_array[:, :, 1] * scale_g, 0, 255)
            img_array[:, :, 2] = np.clip(img_array[:, :, 2] * scale_b, 0, 255)

            return Image.fromarray(img_array.astype(np.uint8))

        except Exception as e:
            self.logger.error(f"Error applying white balance: {e}")
            raise

    def adjust_hue(
        self,
        image: Union[np.ndarray, Image.Image],
        hue_shift: float
    ) -> Image.Image:
        """
        Adjust image hue.

        Args:
            image: Input image
            hue_shift: Hue shift amount (-180 to 180)

        Returns:
            Hue-adjusted image
        """
        try:
            import cv2

            # Convert to numpy array
            if isinstance(image, Image.Image):
                img_array = np.array(image)
            else:
                img_array = image.copy()

            # Convert to HSV
            hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)

            # Adjust hue
            hsv[:, :, 0] = (hsv[:, :, 0] + hue_shift) % 180

            # Convert back to RGB
            rgb = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)

            return Image.fromarray(rgb)

        except ImportError:
            self.logger.error("OpenCV not installed. Install with: pip install opencv-python")
            raise
        except Exception as e:
            self.logger.error(f"Error adjusting hue: {e}")
            raise

    def gamma_correction(
        self,
        image: Union[np.ndarray, Image.Image],
        gamma: float = 1.0
    ) -> Image.Image:
        """
        Apply gamma correction.

        Args:
            image: Input image
            gamma: Gamma value

        Returns:
            Gamma-corrected image
        """
        try:
            # Convert to numpy array
            if isinstance(image, Image.Image):
                img_array = np.array(image)
            else:
                img_array = image.copy()

            # Normalize to [0, 1]
            img_normalized = img_array.astype(np.float32) / 255.0

            # Apply gamma correction
            img_corrected = np.power(img_normalized, gamma)

            # Convert back to [0, 255]
            img_corrected = (img_corrected * 255).astype(np.uint8)

            return Image.fromarray(img_corrected)

        except Exception as e:
            self.logger.error(f"Error applying gamma correction: {e}")
            raise


class NoiseReducer:
    """
    Reduces noise in images.
    """

    def __init__(self):
        """Initialize noise reducer."""
        self.logger = logging.getLogger(f"{__name__}.NoiseReducer")

    def denoise(
        self,
        image: Union[np.ndarray, Image.Image],
        method: str = "gaussian",
        strength: float = 5.0
    ) -> Image.Image:
        """
        Reduce noise in image.

        Args:
            image: Input image
            method: Denoising method (gaussian, bilateral, median, nlm)
            strength: Denoising strength

        Returns:
            Denoised image
        """
        try:
            import cv2

            # Convert to numpy array
            if isinstance(image, Image.Image):
                img_array = np.array(image)
            else:
                img_array = image.copy()

            if method == "gaussian":
                # Gaussian blur
                kernel_size = int(strength) * 2 + 1
                denoised = cv2.GaussianBlur(img_array, (kernel_size, kernel_size), 0)

            elif method == "bilateral":
                # Bilateral filter (preserves edges)
                denoised = cv2.bilateralFilter(img_array, int(strength), strength * 2, strength * 2)

            elif method == "median":
                # Median filter
                kernel_size = int(strength) * 2 + 1
                denoised = cv2.medianBlur(img_array, kernel_size)

            elif method == "nlm":
                # Non-local means denoising
                denoised = cv2.fastNlMeansDenoisingColored(
                    img_array,
                    None,
                    h=strength,
                    hColor=strength,
                    templateWindowSize=7,
                    searchWindowSize=21
                )

            else:
                raise ValueError(f"Unsupported denoising method: {method}")

            return Image.fromarray(denoised)

        except ImportError:
            self.logger.error("OpenCV not installed. Install with: pip install opencv-python")
            raise
        except Exception as e:
            self.logger.error(f"Error denoising image: {e}")
            raise


class PreprocessingPipeline:
    """
    Combines multiple preprocessing operations into a pipeline.
    """

    def __init__(self):
        """Initialize preprocessing pipeline."""
        self.operations: List[Tuple[str, Callable, Dict[str, Any]]] = []
        self.logger = logging.getLogger(f"{__name__}.PreprocessingPipeline")

    def add_operation(
        self,
        name: str,
        operation: Callable,
        params: Optional[Dict[str, Any]] = None
    ) -> 'PreprocessingPipeline':
        """
        Add preprocessing operation to pipeline.

        Args:
            name: Operation name
            operation: Operation function
            params: Operation parameters

        Returns:
            Self for chaining
        """
        self.operations.append((name, operation, params or {}))
        return self

    def process(
        self,
        image: Union[np.ndarray, Image.Image]
    ) -> Union[np.ndarray, Image.Image]:
        """
        Process image through pipeline.

        Args:
            image: Input image

        Returns:
            Processed image
        """
        try:
            result = image

            for name, operation, params in self.operations:
                try:
                    result = operation(result, **params)
                    self.logger.debug(f"Applied {name}")
                except Exception as e:
                    self.logger.error(f"Error in operation {name}: {e}")
                    raise

            return result

        except Exception as e:
            self.logger.error(f"Error processing pipeline: {e}")
            raise

    def process_batch(
        self,
        images: List[Union[np.ndarray, Image.Image]]
    ) -> List[Union[np.ndarray, Image.Image]]:
        """
        Process multiple images through pipeline.

        Args:
            images: List of input images

        Returns:
            List of processed images
        """
        results = []
        for idx, image in enumerate(images):
            try:
                processed = self.process(image)
                results.append(processed)
            except Exception as e:
                self.logger.error(f"Error processing image {idx}: {e}")
                results.append(image)  # Return original on error

        return results

    def clear(self) -> None:
        """Clear all operations from pipeline."""
        self.operations.clear()

    def get_operations(self) -> List[str]:
        """Get list of operation names in pipeline."""
        return [name for name, _, _ in self.operations]


class ImageConverter:
    """
    Converts images between different formats and color spaces.
    """

    def __init__(self):
        """Initialize image converter."""
        self.logger = logging.getLogger(f"{__name__}.ImageConverter")

    def convert_color_space(
        self,
        image: Union[np.ndarray, Image.Image],
        target_space: ColorSpace
    ) -> Union[np.ndarray, Image.Image]:
        """
        Convert image to different color space.

        Args:
            image: Input image
            target_space: Target color space

        Returns:
            Converted image
        """
        try:
            # Convert to PIL Image if numpy array
            is_numpy = isinstance(image, np.ndarray)
            if is_numpy:
                image = Image.fromarray(image)

            # Convert color space
            if target_space == ColorSpace.RGB:
                result = image.convert('RGB')
            elif target_space == ColorSpace.GRAY:
                result = image.convert('L')
            elif target_space == ColorSpace.BGR:
                import cv2
                rgb_array = np.array(image)
                bgr_array = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2BGR)
                result = bgr_array if is_numpy else Image.fromarray(bgr_array)
            elif target_space == ColorSpace.HSV:
                import cv2
                rgb_array = np.array(image)
                hsv_array = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2HSV)
                result = hsv_array if is_numpy else Image.fromarray(hsv_array)
            else:
                raise ValueError(f"Unsupported color space: {target_space}")

            # Return in same format as input
            if is_numpy and isinstance(result, Image.Image):
                return np.array(result)
            elif not is_numpy and isinstance(result, np.ndarray):
                return Image.fromarray(result)
            return result

        except Exception as e:
            self.logger.error(f"Error converting color space: {e}")
            raise

    def convert_format(
        self,
        image_path: str,
        output_path: str,
        output_format: str = "PNG",
        quality: int = 95
    ) -> bool:
        """
        Convert image file format.

        Args:
            image_path: Input image path
            output_path: Output image path
            output_format: Output format (PNG, JPEG, etc.)
            quality: Quality for lossy formats

        Returns:
            True if successful
        """
        try:
            image = Image.open(image_path)

            # Convert RGBA to RGB for JPEG
            if output_format.upper() == 'JPEG' and image.mode == 'RGBA':
                rgb_image = Image.new('RGB', image.size, (255, 255, 255))
                rgb_image.paste(image, mask=image.split()[3])
                image = rgb_image

            # Save with format
            image.save(output_path, format=output_format, quality=quality)

            self.logger.info(f"Converted {image_path} to {output_format}")
            return True

        except Exception as e:
            self.logger.error(f"Error converting format: {e}")
            return False


# Global instances
normalizer = ImageNormalizer()
augmenter = ImageAugmenter()
color_corrector = ColorCorrector()
noise_reducer = NoiseReducer()
converter = ImageConverter()
