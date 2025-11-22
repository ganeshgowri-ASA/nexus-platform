"""
Tests for Quality Assessment Module

Tests:
- BlurDetector
- NoiseDetector
- QualityAssessment
"""

import pytest
import numpy as np
from PIL import Image
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


# ============================================================================
# Test BlurDetector
# ============================================================================

class TestBlurDetector:
    """Test BlurDetector."""

    def test_initialization(self):
        """Test blur detector initialization."""
        from modules.image_recognition.quality import BlurDetector

        detector = BlurDetector(threshold=100.0)

        assert detector.threshold == 100.0

    def test_detect_blur_sharp_image(self, sample_image):
        """Test blur detection on sharp image."""
        from modules.image_recognition.quality import BlurDetector

        detector = BlurDetector()
        result = detector.detect(sample_image)

        assert 'is_blurry' in result
        assert 'blur_score' in result
        assert isinstance(result['is_blurry'], bool)

    def test_detect_blur_blurry_image(self):
        """Test blur detection on blurry image."""
        from modules.image_recognition.quality import BlurDetector

        # Create intentionally blurry image
        img = Image.new('RGB', (224, 224), color='gray')

        detector = BlurDetector(threshold=100.0)
        result = detector.detect(img)

        assert 'blur_score' in result

    @pytest.mark.parametrize("method", ['laplacian', 'fft', 'wavelet'])
    def test_different_blur_detection_methods(self, sample_image, method):
        """Test different blur detection methods."""
        from modules.image_recognition.quality import BlurDetector

        detector = BlurDetector(method=method)
        result = detector.detect(sample_image)

        assert result is not None

    def test_blur_detection_batch(self, multiple_sample_images):
        """Test batch blur detection."""
        from modules.image_recognition.quality import BlurDetector

        detector = BlurDetector()
        results = detector.detect_batch(multiple_sample_images)

        assert len(results) == len(multiple_sample_images)
        assert all('is_blurry' in r for r in results)

    @pytest.mark.parametrize("threshold", [50.0, 100.0, 200.0])
    def test_different_thresholds(self, sample_image, threshold):
        """Test blur detection with different thresholds."""
        from modules.image_recognition.quality import BlurDetector

        detector = BlurDetector(threshold=threshold)
        result = detector.detect(sample_image)

        assert result is not None


# ============================================================================
# Test NoiseDetector
# ============================================================================

class TestNoiseDetector:
    """Test NoiseDetector."""

    def test_initialization(self):
        """Test noise detector initialization."""
        from modules.image_recognition.quality import NoiseDetector

        detector = NoiseDetector(threshold=20.0)

        assert detector.threshold == 20.0

    def test_detect_noise_clean_image(self, sample_image):
        """Test noise detection on clean image."""
        from modules.image_recognition.quality import NoiseDetector

        detector = NoiseDetector()
        result = detector.detect(sample_image)

        assert 'is_noisy' in result
        assert 'noise_score' in result
        assert isinstance(result['is_noisy'], bool)

    def test_detect_noise_noisy_image(self, sample_image_array):
        """Test noise detection on noisy image."""
        from modules.image_recognition.quality import NoiseDetector

        # Add Gaussian noise
        noisy = sample_image_array + np.random.normal(0, 25, sample_image_array.shape)
        noisy = np.clip(noisy, 0, 255).astype(np.uint8)

        detector = NoiseDetector()
        result = detector.detect(Image.fromarray(noisy))

        assert 'noise_score' in result

    @pytest.mark.parametrize("method", ['std', 'median', 'gradient'])
    def test_different_noise_detection_methods(self, sample_image, method):
        """Test different noise detection methods."""
        from modules.image_recognition.quality import NoiseDetector

        detector = NoiseDetector(method=method)
        result = detector.detect(sample_image)

        assert result is not None

    def test_noise_detection_batch(self, multiple_sample_images):
        """Test batch noise detection."""
        from modules.image_recognition.quality import NoiseDetector

        detector = NoiseDetector()
        results = detector.detect_batch(multiple_sample_images)

        assert len(results) == len(multiple_sample_images)


# ============================================================================
# Test QualityAssessment
# ============================================================================

class TestQualityAssessment:
    """Test QualityAssessment."""

    def test_initialization(self):
        """Test quality assessment initialization."""
        from modules.image_recognition.quality import QualityAssessment

        qa = QualityAssessment()

        assert qa is not None

    def test_assess_quality(self, sample_image):
        """Test comprehensive quality assessment."""
        from modules.image_recognition.quality import QualityAssessment

        qa = QualityAssessment()
        result = qa.assess(sample_image)

        assert 'quality_score' in result
        assert 'is_blurry' in result
        assert 'is_noisy' in result
        assert 'brightness' in result
        assert 'contrast' in result
        assert 0 <= result['quality_score'] <= 1

    def test_assess_brightness(self, sample_image):
        """Test brightness assessment."""
        from modules.image_recognition.quality import QualityAssessment

        qa = QualityAssessment()
        brightness = qa.assess_brightness(sample_image)

        assert 0 <= brightness <= 1

    def test_assess_contrast(self, sample_image):
        """Test contrast assessment."""
        from modules.image_recognition.quality import QualityAssessment

        qa = QualityAssessment()
        contrast = qa.assess_contrast(sample_image)

        assert contrast >= 0

    def test_assess_sharpness(self, sample_image):
        """Test sharpness assessment."""
        from modules.image_recognition.quality import QualityAssessment

        qa = QualityAssessment()
        sharpness = qa.assess_sharpness(sample_image)

        assert sharpness >= 0

    def test_assess_exposure(self, sample_image):
        """Test exposure assessment."""
        from modules.image_recognition.quality import QualityAssessment

        qa = QualityAssessment()
        result = qa.assess_exposure(sample_image)

        assert 'is_overexposed' in result
        assert 'is_underexposed' in result

    def test_assess_color_distribution(self, sample_image):
        """Test color distribution assessment."""
        from modules.image_recognition.quality import QualityAssessment

        qa = QualityAssessment()
        result = qa.assess_color_distribution(sample_image)

        assert 'histogram' in result or 'mean_rgb' in result

    def test_assess_resolution(self, sample_image):
        """Test resolution assessment."""
        from modules.image_recognition.quality import QualityAssessment

        qa = QualityAssessment()
        result = qa.assess_resolution(sample_image)

        assert 'width' in result
        assert 'height' in result
        assert 'megapixels' in result

    def test_comprehensive_assessment(self, sample_image):
        """Test full comprehensive quality assessment."""
        from modules.image_recognition.quality import QualityAssessment

        qa = QualityAssessment()
        result = qa.assess(sample_image, comprehensive=True)

        expected_keys = [
            'quality_score', 'is_blurry', 'is_noisy',
            'brightness', 'contrast', 'sharpness'
        ]

        for key in expected_keys:
            assert key in result

    def test_quality_classification(self, sample_image):
        """Test quality classification (excellent/good/poor)."""
        from modules.image_recognition.quality import QualityAssessment

        qa = QualityAssessment()
        result = qa.assess(sample_image)

        quality_class = qa.classify_quality(result['quality_score'])

        assert quality_class in ['excellent', 'good', 'fair', 'poor']

    def test_batch_assessment(self, multiple_sample_images):
        """Test batch quality assessment."""
        from modules.image_recognition.quality import QualityAssessment

        qa = QualityAssessment()
        results = qa.assess_batch(multiple_sample_images)

        assert len(results) == len(multiple_sample_images)
        assert all('quality_score' in r for r in results)

    @pytest.mark.parametrize("image_type", ['bright', 'dark', 'normal'])
    def test_different_image_types(self, image_type):
        """Test quality assessment on different image types."""
        from modules.image_recognition.quality import QualityAssessment

        if image_type == 'bright':
            img = Image.new('RGB', (224, 224), color=(250, 250, 250))
        elif image_type == 'dark':
            img = Image.new('RGB', (224, 224), color=(10, 10, 10))
        else:
            img = Image.new('RGB', (224, 224), color=(128, 128, 128))

        qa = QualityAssessment()
        result = qa.assess(img)

        assert result is not None
        assert 'quality_score' in result


# ============================================================================
# Edge Cases
# ============================================================================

class TestQualityEdgeCases:
    """Test edge cases."""

    def test_assess_tiny_image(self):
        """Test quality assessment on very small image."""
        from modules.image_recognition.quality import QualityAssessment

        tiny_img = Image.new('RGB', (10, 10))
        qa = QualityAssessment()
        result = qa.assess(tiny_img)

        assert result is not None

    def test_assess_large_image(self):
        """Test quality assessment on very large image."""
        from modules.image_recognition.quality import QualityAssessment

        large_img = Image.new('RGB', (4000, 3000))
        qa = QualityAssessment()
        result = qa.assess(large_img)

        assert result is not None

    def test_assess_grayscale_image(self):
        """Test quality assessment on grayscale image."""
        from modules.image_recognition.quality import QualityAssessment

        gray_img = Image.new('L', (224, 224))
        qa = QualityAssessment()
        result = qa.assess(gray_img)

        assert result is not None

    def test_assess_solid_color_image(self):
        """Test quality assessment on solid color image."""
        from modules.image_recognition.quality import QualityAssessment

        solid_img = Image.new('RGB', (224, 224), color='red')
        qa = QualityAssessment()
        result = qa.assess(solid_img)

        assert result is not None
        assert 'quality_score' in result

    def test_assess_black_image(self):
        """Test quality assessment on all-black image."""
        from modules.image_recognition.quality import QualityAssessment

        black_img = Image.new('RGB', (224, 224), color='black')
        qa = QualityAssessment()
        result = qa.assess(black_img)

        assert result is not None
        assert result['brightness'] == 0 or result['brightness'] < 0.1

    def test_assess_white_image(self):
        """Test quality assessment on all-white image."""
        from modules.image_recognition.quality import QualityAssessment

        white_img = Image.new('RGB', (224, 224), color='white')
        qa = QualityAssessment()
        result = qa.assess(white_img)

        assert result is not None
        assert result['brightness'] == 1.0 or result['brightness'] > 0.9
