"""
Test OCR Engines
"""

import pytest
import numpy as np
from PIL import Image
from modules.ocr.engines import (
    OCREngineFactory, TesseractOCR, OCRResult
)


@pytest.fixture
def sample_image():
    """Create sample test image"""
    # Create simple image with text
    img = Image.new('RGB', (200, 50), color='white')
    return np.array(img)


class TestOCREngineFactory:
    """Test OCR engine factory"""

    def test_create_tesseract_engine(self):
        """Test creating Tesseract engine"""
        engine = OCREngineFactory.create_engine("tesseract")
        assert engine is not None
        assert isinstance(engine, TesseractOCR)

    def test_invalid_engine_type(self):
        """Test creating invalid engine"""
        with pytest.raises(ValueError):
            OCREngineFactory.create_engine("invalid_engine")


class TestTesseractOCR:
    """Test Tesseract OCR engine"""

    def test_tesseract_initialization(self):
        """Test Tesseract initialization"""
        engine = TesseractOCR()
        assert engine is not None

    def test_process_image(self, sample_image):
        """Test image processing"""
        engine = TesseractOCR()

        if engine.is_available():
            result = engine.process_image(sample_image)
            assert isinstance(result, OCRResult)
            assert isinstance(result.text, str)
            assert 0 <= result.confidence <= 1

    def test_is_available(self):
        """Test engine availability check"""
        engine = TesseractOCR()
        available = engine.is_available()
        assert isinstance(available, bool)


class TestOCRResult:
    """Test OCR result class"""

    def test_ocr_result_creation(self):
        """Test creating OCR result"""
        result = OCRResult(
            text="Test text",
            confidence=0.95,
            words=[],
            lines=[],
            blocks=[]
        )

        assert result.text == "Test text"
        assert result.confidence == 0.95
        assert isinstance(result.words, list)

    def test_ocr_result_to_dict(self):
        """Test converting result to dictionary"""
        result = OCRResult(
            text="Test",
            confidence=0.9,
            metadata={'test': 'value'}
        )

        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        assert result_dict['text'] == "Test"
        assert result_dict['confidence'] == 0.9
