"""
Image Preprocessing Module

Provides image enhancement, deskewing, noise removal, binarization,
and contrast adjustment for improved OCR accuracy.
"""

import logging
from typing import Tuple, Optional, Any
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import cv2

logger = logging.getLogger(__name__)


class ImageEnhancer:
    """Enhanced image preprocessing for better OCR results"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.ImageEnhancer")

    def enhance(
        self,
        image: np.ndarray,
        enhance_contrast: bool = True,
        enhance_sharpness: bool = True,
        denoise: bool = True,
        brightness_factor: float = 1.0,
    ) -> np.ndarray:
        """
        Apply multiple enhancement techniques to improve OCR accuracy

        Args:
            image: Input image as numpy array
            enhance_contrast: Apply contrast enhancement
            enhance_sharpness: Apply sharpness enhancement
            denoise: Apply denoising
            brightness_factor: Brightness adjustment factor

        Returns:
            Enhanced image as numpy array
        """
        try:
            # Convert to PIL Image
            if isinstance(image, np.ndarray):
                if len(image.shape) == 2:  # Grayscale
                    pil_image = Image.fromarray(image, mode='L')
                else:
                    pil_image = Image.fromarray(image)
            else:
                pil_image = image

            # Brightness adjustment
            if brightness_factor != 1.0:
                enhancer = ImageEnhance.Brightness(pil_image)
                pil_image = enhancer.enhance(brightness_factor)

            # Contrast enhancement
            if enhance_contrast:
                enhancer = ImageEnhance.Contrast(pil_image)
                pil_image = enhancer.enhance(1.5)

            # Sharpness enhancement
            if enhance_sharpness:
                enhancer = ImageEnhance.Sharpness(pil_image)
                pil_image = enhancer.enhance(2.0)

            # Convert back to numpy array
            enhanced = np.array(pil_image)

            # Denoising
            if denoise:
                if len(enhanced.shape) == 3:
                    enhanced = cv2.fastNlMeansDenoisingColored(enhanced, None, 10, 10, 7, 21)
                else:
                    enhanced = cv2.fastNlMeansDenoising(enhanced, None, 10, 7, 21)

            return enhanced

        except Exception as e:
            self.logger.error(f"Error enhancing image: {e}")
            return image

    def auto_enhance(self, image: np.ndarray) -> np.ndarray:
        """
        Automatically enhance image using adaptive techniques

        Args:
            image: Input image

        Returns:
            Enhanced image
        """
        try:
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()

            # Calculate image statistics
            mean_intensity = np.mean(gray)
            std_intensity = np.std(gray)

            # Determine enhancement strategy based on statistics
            if mean_intensity < 100:  # Dark image
                brightness_factor = 1.5
            elif mean_intensity > 180:  # Bright image
                brightness_factor = 0.8
            else:
                brightness_factor = 1.0

            # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)

            # Apply bilateral filter for edge-preserving smoothing
            enhanced = cv2.bilateralFilter(enhanced, 9, 75, 75)

            return enhanced

        except Exception as e:
            self.logger.error(f"Error in auto-enhance: {e}")
            return image


class Deskew:
    """Deskew images to correct rotation"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.Deskew")

    def detect_angle(self, image: np.ndarray) -> float:
        """
        Detect skew angle using Hough Line Transform

        Args:
            image: Input image

        Returns:
            Detected skew angle in degrees
        """
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()

            # Apply edge detection
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)

            # Detect lines using Hough Transform
            lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)

            if lines is None or len(lines) == 0:
                return 0.0

            # Calculate angles
            angles = []
            for line in lines:
                rho, theta = line[0]
                angle = np.degrees(theta) - 90
                if -45 < angle < 45:
                    angles.append(angle)

            if not angles:
                return 0.0

            # Return median angle
            return float(np.median(angles))

        except Exception as e:
            self.logger.error(f"Error detecting angle: {e}")
            return 0.0

    def deskew(self, image: np.ndarray, angle: Optional[float] = None) -> np.ndarray:
        """
        Deskew image by rotating it

        Args:
            image: Input image
            angle: Rotation angle (auto-detect if None)

        Returns:
            Deskewed image
        """
        try:
            if angle is None:
                angle = self.detect_angle(image)

            if abs(angle) < 0.5:  # Skip if angle is too small
                return image

            # Get image dimensions
            h, w = image.shape[:2]

            # Calculate rotation matrix
            center = (w // 2, h // 2)
            matrix = cv2.getRotationMatrix2D(center, angle, 1.0)

            # Perform rotation
            rotated = cv2.warpAffine(
                image,
                matrix,
                (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE
            )

            self.logger.info(f"Deskewed image by {angle:.2f} degrees")
            return rotated

        except Exception as e:
            self.logger.error(f"Error deskewing image: {e}")
            return image


class NoiseRemoval:
    """Remove noise from images"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.NoiseRemoval")

    def remove_noise(
        self,
        image: np.ndarray,
        method: str = "gaussian",
        **kwargs
    ) -> np.ndarray:
        """
        Remove noise from image using various methods

        Args:
            image: Input image
            method: Noise removal method ('gaussian', 'median', 'bilateral', 'nlm')
            **kwargs: Additional parameters for the method

        Returns:
            Denoised image
        """
        try:
            if method == "gaussian":
                kernel_size = kwargs.get("kernel_size", 5)
                return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)

            elif method == "median":
                kernel_size = kwargs.get("kernel_size", 5)
                return cv2.medianBlur(image, kernel_size)

            elif method == "bilateral":
                d = kwargs.get("d", 9)
                sigma_color = kwargs.get("sigma_color", 75)
                sigma_space = kwargs.get("sigma_space", 75)
                return cv2.bilateralFilter(image, d, sigma_color, sigma_space)

            elif method == "nlm":
                # Non-local means denoising
                if len(image.shape) == 3:
                    return cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
                else:
                    return cv2.fastNlMeansDenoising(image, None, 10, 7, 21)

            else:
                self.logger.warning(f"Unknown denoising method: {method}")
                return image

        except Exception as e:
            self.logger.error(f"Error removing noise: {e}")
            return image

    def remove_salt_pepper(self, image: np.ndarray) -> np.ndarray:
        """
        Remove salt and pepper noise using morphological operations

        Args:
            image: Input image

        Returns:
            Cleaned image
        """
        try:
            # Apply median filter
            denoised = cv2.medianBlur(image, 5)

            # Morphological operations
            kernel = np.ones((3, 3), np.uint8)
            opening = cv2.morphologyEx(denoised, cv2.MORPH_OPEN, kernel, iterations=1)
            closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel, iterations=1)

            return closing

        except Exception as e:
            self.logger.error(f"Error removing salt-pepper noise: {e}")
            return image


class Binarization:
    """Convert images to binary (black and white) for better OCR"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.Binarization")

    def binarize(
        self,
        image: np.ndarray,
        method: str = "otsu",
        **kwargs
    ) -> np.ndarray:
        """
        Binarize image using various methods

        Args:
            image: Input image
            method: Binarization method ('otsu', 'adaptive', 'threshold')
            **kwargs: Additional parameters

        Returns:
            Binary image
        """
        try:
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()

            if method == "otsu":
                # Otsu's binarization
                _, binary = cv2.threshold(
                    gray, 0, 255,
                    cv2.THRESH_BINARY + cv2.THRESH_OTSU
                )
                return binary

            elif method == "adaptive":
                # Adaptive thresholding
                block_size = kwargs.get("block_size", 11)
                c = kwargs.get("c", 2)
                return cv2.adaptiveThreshold(
                    gray, 255,
                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY,
                    block_size, c
                )

            elif method == "threshold":
                # Simple thresholding
                threshold_value = kwargs.get("threshold", 127)
                _, binary = cv2.threshold(
                    gray, threshold_value, 255,
                    cv2.THRESH_BINARY
                )
                return binary

            elif method == "sauvola":
                # Sauvola's method for local thresholding
                return self._sauvola_threshold(gray, **kwargs)

            else:
                self.logger.warning(f"Unknown binarization method: {method}")
                return gray

        except Exception as e:
            self.logger.error(f"Error binarizing image: {e}")
            return image

    def _sauvola_threshold(
        self,
        image: np.ndarray,
        window_size: int = 15,
        k: float = 0.2,
        r: float = 128
    ) -> np.ndarray:
        """
        Apply Sauvola's local thresholding method

        Args:
            image: Grayscale input image
            window_size: Local window size
            k: Sauvola parameter
            r: Dynamic range of standard deviation

        Returns:
            Binary image
        """
        try:
            # Calculate local mean and standard deviation
            mean = cv2.blur(image.astype(np.float64), (window_size, window_size))
            mean_sq = cv2.blur(
                np.square(image.astype(np.float64)),
                (window_size, window_size)
            )
            std = np.sqrt(mean_sq - np.square(mean))

            # Calculate threshold
            threshold = mean * (1 + k * ((std / r) - 1))

            # Apply threshold
            binary = np.where(image > threshold, 255, 0).astype(np.uint8)
            return binary

        except Exception as e:
            self.logger.error(f"Error in Sauvola threshold: {e}")
            return image


class ContrastAdjustment:
    """Adjust image contrast for better OCR"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.ContrastAdjustment")

    def adjust_contrast(
        self,
        image: np.ndarray,
        method: str = "clahe",
        **kwargs
    ) -> np.ndarray:
        """
        Adjust image contrast using various methods

        Args:
            image: Input image
            method: Contrast adjustment method ('clahe', 'histogram', 'gamma')
            **kwargs: Additional parameters

        Returns:
            Contrast-adjusted image
        """
        try:
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()

            if method == "clahe":
                # CLAHE (Contrast Limited Adaptive Histogram Equalization)
                clip_limit = kwargs.get("clip_limit", 2.0)
                tile_grid_size = kwargs.get("tile_grid_size", (8, 8))
                clahe = cv2.createCLAHE(
                    clipLimit=clip_limit,
                    tileGridSize=tile_grid_size
                )
                return clahe.apply(gray)

            elif method == "histogram":
                # Histogram equalization
                return cv2.equalizeHist(gray)

            elif method == "gamma":
                # Gamma correction
                gamma = kwargs.get("gamma", 1.5)
                inv_gamma = 1.0 / gamma
                table = np.array([
                    ((i / 255.0) ** inv_gamma) * 255
                    for i in range(256)
                ]).astype(np.uint8)
                return cv2.LUT(gray, table)

            elif method == "auto":
                # Automatic contrast adjustment
                return self._auto_contrast(gray)

            else:
                self.logger.warning(f"Unknown contrast method: {method}")
                return gray

        except Exception as e:
            self.logger.error(f"Error adjusting contrast: {e}")
            return image

    def _auto_contrast(self, image: np.ndarray) -> np.ndarray:
        """
        Automatically adjust contrast based on image statistics

        Args:
            image: Grayscale input image

        Returns:
            Contrast-adjusted image
        """
        try:
            # Calculate percentiles
            p2, p98 = np.percentile(image, (2, 98))

            # Stretch contrast
            stretched = np.clip((image - p2) * (255.0 / (p98 - p2)), 0, 255)
            return stretched.astype(np.uint8)

        except Exception as e:
            self.logger.error(f"Error in auto contrast: {e}")
            return image


class ImageProcessor:
    """Main image processor combining all preprocessing techniques"""

    def __init__(self):
        self.enhancer = ImageEnhancer()
        self.deskew = Deskew()
        self.noise_removal = NoiseRemoval()
        self.binarization = Binarization()
        self.contrast = ContrastAdjustment()
        self.logger = logging.getLogger(f"{__name__}.ImageProcessor")

    def preprocess(
        self,
        image: np.ndarray,
        deskew: bool = True,
        enhance: bool = True,
        denoise: bool = True,
        binarize: bool = False,
        adjust_contrast: bool = True,
    ) -> np.ndarray:
        """
        Apply complete preprocessing pipeline

        Args:
            image: Input image
            deskew: Apply deskewing
            enhance: Apply enhancement
            denoise: Apply denoising
            binarize: Apply binarization
            adjust_contrast: Apply contrast adjustment

        Returns:
            Preprocessed image
        """
        try:
            processed = image.copy()

            # Deskew
            if deskew:
                processed = self.deskew.deskew(processed)

            # Adjust contrast
            if adjust_contrast:
                processed = self.contrast.adjust_contrast(processed, method="clahe")

            # Enhance
            if enhance:
                processed = self.enhancer.auto_enhance(processed)

            # Denoise
            if denoise:
                processed = self.noise_removal.remove_noise(processed, method="bilateral")

            # Binarize (usually done last)
            if binarize:
                processed = self.binarization.binarize(processed, method="otsu")

            self.logger.info("Image preprocessing completed")
            return processed

        except Exception as e:
            self.logger.error(f"Error in preprocessing pipeline: {e}")
            return image

    def preprocess_for_ocr(self, image: np.ndarray, ocr_engine: str = "tesseract") -> np.ndarray:
        """
        Preprocess image optimized for specific OCR engine

        Args:
            image: Input image
            ocr_engine: Target OCR engine

        Returns:
            Preprocessed image
        """
        try:
            if ocr_engine.lower() == "tesseract":
                # Tesseract works best with binary images
                return self.preprocess(
                    image,
                    deskew=True,
                    enhance=True,
                    denoise=True,
                    binarize=True,
                    adjust_contrast=True
                )
            else:
                # Cloud services prefer clean grayscale
                return self.preprocess(
                    image,
                    deskew=True,
                    enhance=True,
                    denoise=True,
                    binarize=False,
                    adjust_contrast=True
                )

        except Exception as e:
            self.logger.error(f"Error preprocessing for OCR: {e}")
            return image
