"""
Image Quality Assessment Module

Provides comprehensive image quality analysis including:
- Overall quality scoring
- Blur detection (motion and defocus)
- Noise detection and quantification
- Brightness and contrast analysis
- Color saturation and balance
- Resolution and sharpness assessment
- Artifact detection
- Quality recommendations

Production-ready with detailed metrics and reporting.
"""

import logging
from typing import Optional, Dict, Any, List, Union, Tuple
import numpy as np
from PIL import Image, ImageStat
from datetime import datetime

logger = logging.getLogger(__name__)


class QualityMetrics:
    """
    Represents comprehensive quality metrics for an image.
    """

    def __init__(
        self,
        overall_score: float,
        is_blurry: bool,
        blur_score: float,
        is_noisy: bool,
        noise_score: float,
        brightness: float,
        contrast: float,
        saturation: float,
        sharpness: float,
        resolution: Tuple[int, int],
        recommendations: Optional[List[str]] = None
    ):
        """
        Initialize quality metrics.

        Args:
            overall_score: Overall quality score (0-1)
            is_blurry: Whether image is blurry
            blur_score: Blur metric score
            is_noisy: Whether image is noisy
            noise_score: Noise metric score
            brightness: Brightness score (0-1)
            contrast: Contrast score (0-1)
            saturation: Color saturation (0-1)
            sharpness: Sharpness score (0-1)
            resolution: Image resolution (width, height)
            recommendations: List of improvement recommendations
        """
        self.overall_score = overall_score
        self.is_blurry = is_blurry
        self.blur_score = blur_score
        self.is_noisy = is_noisy
        self.noise_score = noise_score
        self.brightness = brightness
        self.contrast = contrast
        self.saturation = saturation
        self.sharpness = sharpness
        self.resolution = resolution
        self.recommendations = recommendations or []
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'overall_score': float(self.overall_score),
            'is_blurry': self.is_blurry,
            'blur_score': float(self.blur_score),
            'is_noisy': self.is_noisy,
            'noise_score': float(self.noise_score),
            'brightness': float(self.brightness),
            'contrast': float(self.contrast),
            'saturation': float(self.saturation),
            'sharpness': float(self.sharpness),
            'resolution': {'width': self.resolution[0], 'height': self.resolution[1]},
            'recommendations': self.recommendations,
            'timestamp': self.timestamp.isoformat()
        }

    def __repr__(self) -> str:
        return f"<QualityMetrics(score={self.overall_score:.2f}, blur={self.is_blurry}, noise={self.is_noisy})>"


class BlurDetector:
    """
    Detects and quantifies image blur.
    """

    def __init__(self, threshold: float = 100.0):
        """
        Initialize blur detector.

        Args:
            threshold: Laplacian variance threshold for blur detection
        """
        self.threshold = threshold
        self.logger = logging.getLogger(f"{__name__}.BlurDetector")

    def detect_blur(
        self,
        image: Union[np.ndarray, Image.Image]
    ) -> Tuple[bool, float]:
        """
        Detect if image is blurry.

        Args:
            image: Input image

        Returns:
            Tuple of (is_blurry, blur_score)
        """
        try:
            import cv2

            # Convert to numpy array
            if isinstance(image, Image.Image):
                img_array = np.array(image)
            else:
                img_array = image.copy()

            # Convert to grayscale
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array

            # Calculate Laplacian variance
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

            is_blurry = laplacian_var < self.threshold
            blur_score = float(laplacian_var)

            return is_blurry, blur_score

        except ImportError:
            self.logger.error("OpenCV not installed. Install with: pip install opencv-python")
            raise
        except Exception as e:
            self.logger.error(f"Error detecting blur: {e}")
            raise

    def detect_motion_blur(
        self,
        image: Union[np.ndarray, Image.Image]
    ) -> Tuple[bool, float]:
        """
        Detect motion blur specifically.

        Args:
            image: Input image

        Returns:
            Tuple of (has_motion_blur, score)
        """
        try:
            import cv2

            # Convert to numpy array
            if isinstance(image, Image.Image):
                img_array = np.array(image)
            else:
                img_array = image.copy()

            # Convert to grayscale
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array

            # Use FFT to detect directional blur
            f = np.fft.fft2(gray)
            fshift = np.fft.fftshift(f)
            magnitude_spectrum = 20 * np.log(np.abs(fshift) + 1)

            # Analyze spectrum for motion blur patterns
            # Simplified: check variance in frequency domain
            spectrum_var = float(np.var(magnitude_spectrum))
            has_motion_blur = spectrum_var < 100  # Threshold for motion blur

            return has_motion_blur, spectrum_var

        except Exception as e:
            self.logger.error(f"Error detecting motion blur: {e}")
            raise


class NoiseDetector:
    """
    Detects and quantifies image noise.
    """

    def __init__(self, threshold: float = 20.0):
        """
        Initialize noise detector.

        Args:
            threshold: Noise threshold
        """
        self.threshold = threshold
        self.logger = logging.getLogger(f"{__name__}.NoiseDetector")

    def detect_noise(
        self,
        image: Union[np.ndarray, Image.Image]
    ) -> Tuple[bool, float]:
        """
        Detect if image is noisy.

        Args:
            image: Input image

        Returns:
            Tuple of (is_noisy, noise_score)
        """
        try:
            import cv2

            # Convert to numpy array
            if isinstance(image, Image.Image):
                img_array = np.array(image)
            else:
                img_array = image.copy()

            # Convert to grayscale
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array

            # Calculate noise using standard deviation of high-frequency content
            # Apply high-pass filter
            kernel = np.array([[-1, -1, -1],
                             [-1,  8, -1],
                             [-1, -1, -1]])
            high_freq = cv2.filter2D(gray, -1, kernel)

            # Calculate standard deviation
            noise_score = float(np.std(high_freq))
            is_noisy = noise_score > self.threshold

            return is_noisy, noise_score

        except ImportError:
            self.logger.error("OpenCV not installed. Install with: pip install opencv-python")
            raise
        except Exception as e:
            self.logger.error(f"Error detecting noise: {e}")
            raise


class BrightnessContrastAnalyzer:
    """
    Analyzes image brightness and contrast.
    """

    def __init__(self):
        """Initialize brightness/contrast analyzer."""
        self.logger = logging.getLogger(f"{__name__}.BrightnessContrastAnalyzer")

    def analyze(
        self,
        image: Union[np.ndarray, Image.Image]
    ) -> Tuple[float, float]:
        """
        Analyze brightness and contrast.

        Args:
            image: Input image

        Returns:
            Tuple of (brightness, contrast) normalized to [0, 1]
        """
        try:
            # Convert to PIL Image
            if isinstance(image, np.ndarray):
                image = Image.fromarray(image)

            # Convert to grayscale for analysis
            gray = image.convert('L')

            # Calculate statistics
            stat = ImageStat.Stat(gray)

            # Brightness: mean pixel value normalized to [0, 1]
            brightness = stat.mean[0] / 255.0

            # Contrast: standard deviation normalized
            contrast = stat.stddev[0] / 127.5  # Normalize assuming max stddev is ~127.5

            return brightness, min(contrast, 1.0)

        except Exception as e:
            self.logger.error(f"Error analyzing brightness/contrast: {e}")
            raise

    def is_well_exposed(
        self,
        brightness: float,
        optimal_range: Tuple[float, float] = (0.3, 0.7)
    ) -> bool:
        """
        Check if image is well exposed.

        Args:
            brightness: Brightness value
            optimal_range: Optimal brightness range

        Returns:
            True if well exposed
        """
        return optimal_range[0] <= brightness <= optimal_range[1]


class ColorAnalyzer:
    """
    Analyzes image color properties.
    """

    def __init__(self):
        """Initialize color analyzer."""
        self.logger = logging.getLogger(f"{__name__}.ColorAnalyzer")

    def analyze_saturation(
        self,
        image: Union[np.ndarray, Image.Image]
    ) -> float:
        """
        Analyze color saturation.

        Args:
            image: Input image

        Returns:
            Saturation score (0-1)
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

            # Get saturation channel
            saturation = hsv[:, :, 1]

            # Calculate average saturation
            avg_saturation = float(np.mean(saturation)) / 255.0

            return avg_saturation

        except ImportError:
            self.logger.error("OpenCV not installed. Install with: pip install opencv-python")
            raise
        except Exception as e:
            self.logger.error(f"Error analyzing saturation: {e}")
            raise

    def analyze_color_balance(
        self,
        image: Union[np.ndarray, Image.Image]
    ) -> Dict[str, float]:
        """
        Analyze color balance.

        Args:
            image: Input image

        Returns:
            Dictionary with R, G, B balance scores
        """
        try:
            # Convert to numpy array
            if isinstance(image, Image.Image):
                img_array = np.array(image)
            else:
                img_array = image.copy()

            # Calculate mean for each channel
            r_mean = float(np.mean(img_array[:, :, 0]))
            g_mean = float(np.mean(img_array[:, :, 1]))
            b_mean = float(np.mean(img_array[:, :, 2]))

            # Normalize
            total = r_mean + g_mean + b_mean
            if total > 0:
                return {
                    'red': r_mean / total,
                    'green': g_mean / total,
                    'blue': b_mean / total
                }
            else:
                return {'red': 0.33, 'green': 0.33, 'blue': 0.33}

        except Exception as e:
            self.logger.error(f"Error analyzing color balance: {e}")
            raise


class SharpnessAnalyzer:
    """
    Analyzes image sharpness.
    """

    def __init__(self):
        """Initialize sharpness analyzer."""
        self.logger = logging.getLogger(f"{__name__}.SharpnessAnalyzer")

    def analyze_sharpness(
        self,
        image: Union[np.ndarray, Image.Image]
    ) -> float:
        """
        Analyze image sharpness.

        Args:
            image: Input image

        Returns:
            Sharpness score (0-1)
        """
        try:
            import cv2

            # Convert to numpy array
            if isinstance(image, Image.Image):
                img_array = np.array(image)
            else:
                img_array = image.copy()

            # Convert to grayscale
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array

            # Calculate Sobel gradients
            sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)

            # Calculate gradient magnitude
            magnitude = np.sqrt(sobelx**2 + sobely**2)

            # Normalize sharpness score
            sharpness = float(np.mean(magnitude)) / 255.0

            return min(sharpness, 1.0)

        except ImportError:
            self.logger.error("OpenCV not installed. Install with: pip install opencv-python")
            raise
        except Exception as e:
            self.logger.error(f"Error analyzing sharpness: {e}")
            raise


class QualityAssessment:
    """
    Comprehensive image quality assessment system.
    """

    def __init__(self):
        """Initialize quality assessment system."""
        self.blur_detector = BlurDetector()
        self.noise_detector = NoiseDetector()
        self.brightness_contrast_analyzer = BrightnessContrastAnalyzer()
        self.color_analyzer = ColorAnalyzer()
        self.sharpness_analyzer = SharpnessAnalyzer()
        self.logger = logging.getLogger(f"{__name__}.QualityAssessment")

    def assess_quality(
        self,
        image: Union[str, np.ndarray, Image.Image],
        detailed: bool = True
    ) -> QualityMetrics:
        """
        Perform comprehensive quality assessment.

        Args:
            image: Input image
            detailed: Whether to perform detailed analysis

        Returns:
            Quality metrics
        """
        try:
            # Load image
            if isinstance(image, str):
                image = Image.open(image).convert('RGB')
            elif isinstance(image, np.ndarray):
                image = Image.fromarray(image)

            # Get resolution
            resolution = image.size

            # Detect blur
            is_blurry, blur_score = self.blur_detector.detect_blur(image)

            # Detect noise
            is_noisy, noise_score = self.noise_detector.detect_noise(image)

            # Analyze brightness and contrast
            brightness, contrast = self.brightness_contrast_analyzer.analyze(image)

            # Analyze saturation
            saturation = self.color_analyzer.analyze_saturation(image)

            # Analyze sharpness
            sharpness = self.sharpness_analyzer.analyze_sharpness(image)

            # Calculate overall quality score
            overall_score = self._calculate_overall_score(
                is_blurry,
                is_noisy,
                brightness,
                contrast,
                saturation,
                sharpness
            )

            # Generate recommendations
            recommendations = self._generate_recommendations(
                is_blurry,
                is_noisy,
                brightness,
                contrast,
                saturation,
                sharpness
            )

            # Create quality metrics
            metrics = QualityMetrics(
                overall_score=overall_score,
                is_blurry=is_blurry,
                blur_score=blur_score,
                is_noisy=is_noisy,
                noise_score=noise_score,
                brightness=brightness,
                contrast=contrast,
                saturation=saturation,
                sharpness=sharpness,
                resolution=resolution,
                recommendations=recommendations
            )

            self.logger.info(f"Quality assessment completed: score={overall_score:.2f}")
            return metrics

        except Exception as e:
            self.logger.error(f"Error assessing quality: {e}")
            raise

    def _calculate_overall_score(
        self,
        is_blurry: bool,
        is_noisy: bool,
        brightness: float,
        contrast: float,
        saturation: float,
        sharpness: float
    ) -> float:
        """Calculate overall quality score."""
        # Start with perfect score
        score = 1.0

        # Penalize for blur
        if is_blurry:
            score -= 0.3

        # Penalize for noise
        if is_noisy:
            score -= 0.2

        # Penalize for poor brightness
        if brightness < 0.2 or brightness > 0.8:
            score -= 0.15

        # Penalize for poor contrast
        if contrast < 0.2:
            score -= 0.15

        # Penalize for poor saturation
        if saturation < 0.1:
            score -= 0.1

        # Penalize for low sharpness
        if sharpness < 0.2:
            score -= 0.1

        return max(0.0, score)

    def _generate_recommendations(
        self,
        is_blurry: bool,
        is_noisy: bool,
        brightness: float,
        contrast: float,
        saturation: float,
        sharpness: float
    ) -> List[str]:
        """Generate quality improvement recommendations."""
        recommendations = []

        if is_blurry:
            recommendations.append("Image is blurry - consider using a tripod or faster shutter speed")

        if is_noisy:
            recommendations.append("Image has noise - consider using lower ISO or noise reduction")

        if brightness < 0.3:
            recommendations.append("Image is too dark - increase exposure or brightness")
        elif brightness > 0.7:
            recommendations.append("Image is too bright - decrease exposure")

        if contrast < 0.2:
            recommendations.append("Low contrast - consider adjusting contrast or using better lighting")

        if saturation < 0.1:
            recommendations.append("Low color saturation - image appears washed out")

        if sharpness < 0.2:
            recommendations.append("Low sharpness - consider using sharpening filter")

        if not recommendations:
            recommendations.append("Image quality is good")

        return recommendations

    def batch_assess(
        self,
        images: List[Union[str, np.ndarray, Image.Image]]
    ) -> List[QualityMetrics]:
        """
        Assess quality for multiple images.

        Args:
            images: List of images

        Returns:
            List of quality metrics
        """
        results = []
        for idx, image in enumerate(images):
            try:
                metrics = self.assess_quality(image)
                results.append(metrics)
            except Exception as e:
                self.logger.error(f"Error assessing image {idx}: {e}")
                continue

        return results


# Global quality assessment instance
quality_assessment = QualityAssessment()
