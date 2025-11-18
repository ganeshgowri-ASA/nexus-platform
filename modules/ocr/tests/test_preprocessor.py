"""
Test Image Preprocessing
"""

import pytest
import numpy as np
import cv2
from modules.ocr.preprocessor import (
    ImageEnhancer, Deskew, NoiseRemoval,
    Binarization, ContrastAdjustment, ImageProcessor
)


@pytest.fixture
def sample_image():
    """Create sample test image"""
    return np.random.randint(0, 256, (100, 100), dtype=np.uint8)


class TestImageEnhancer:
    """Test image enhancement"""

    def test_enhance(self, sample_image):
        """Test image enhancement"""
        enhancer = ImageEnhancer()
        enhanced = enhancer.enhance(sample_image)

        assert enhanced is not None
        assert enhanced.shape == sample_image.shape

    def test_auto_enhance(self, sample_image):
        """Test auto enhancement"""
        enhancer = ImageEnhancer()
        enhanced = enhancer.auto_enhance(sample_image)

        assert enhanced is not None
        assert isinstance(enhanced, np.ndarray)


class TestDeskew:
    """Test image deskewing"""

    def test_detect_angle(self, sample_image):
        """Test angle detection"""
        deskew = Deskew()
        angle = deskew.detect_angle(sample_image)

        assert isinstance(angle, float)
        assert -90 <= angle <= 90

    def test_deskew(self, sample_image):
        """Test deskewing"""
        deskew = Deskew()
        deskewed = deskew.deskew(sample_image, angle=5.0)

        assert deskewed is not None
        assert deskewed.shape == sample_image.shape


class TestNoiseRemoval:
    """Test noise removal"""

    def test_remove_noise_gaussian(self, sample_image):
        """Test Gaussian noise removal"""
        noise_removal = NoiseRemoval()
        cleaned = noise_removal.remove_noise(sample_image, method="gaussian")

        assert cleaned is not None
        assert cleaned.shape == sample_image.shape

    def test_remove_noise_median(self, sample_image):
        """Test median noise removal"""
        noise_removal = NoiseRemoval()
        cleaned = noise_removal.remove_noise(sample_image, method="median")

        assert cleaned is not None

    def test_remove_salt_pepper(self, sample_image):
        """Test salt and pepper noise removal"""
        noise_removal = NoiseRemoval()
        cleaned = noise_removal.remove_salt_pepper(sample_image)

        assert cleaned is not None


class TestBinarization:
    """Test binarization"""

    def test_binarize_otsu(self, sample_image):
        """Test Otsu binarization"""
        binarization = Binarization()
        binary = binarization.binarize(sample_image, method="otsu")

        assert binary is not None
        assert np.all((binary == 0) | (binary == 255))

    def test_binarize_adaptive(self, sample_image):
        """Test adaptive binarization"""
        binarization = Binarization()
        binary = binarization.binarize(sample_image, method="adaptive")

        assert binary is not None


class TestImageProcessor:
    """Test main image processor"""

    def test_preprocess(self, sample_image):
        """Test preprocessing pipeline"""
        processor = ImageProcessor()
        processed = processor.preprocess(sample_image)

        assert processed is not None
        assert isinstance(processed, np.ndarray)

    def test_preprocess_for_ocr(self, sample_image):
        """Test OCR-specific preprocessing"""
        processor = ImageProcessor()
        processed = processor.preprocess_for_ocr(sample_image, ocr_engine="tesseract")

        assert processed is not None
