"""
Pytest Configuration and Fixtures
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import numpy as np
from PIL import Image


@pytest.fixture(scope="session")
def temp_dir():
    """Create temporary directory for tests"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_text_image(temp_dir):
    """Create sample image with text"""
    img = Image.new('RGB', (400, 100), color='white')
    # In real tests, would add text using PIL.ImageDraw
    path = temp_dir / "test_image.png"
    img.save(path)
    return path


@pytest.fixture
def sample_pdf(temp_dir):
    """Create sample PDF for testing"""
    # Would create actual PDF in real tests
    path = temp_dir / "test.pdf"
    path.touch()
    return path


@pytest.fixture
def mock_ocr_result():
    """Mock OCR result"""
    from modules.ocr.engines import OCRResult
    return OCRResult(
        text="Test OCR result text",
        confidence=0.95,
        words=[
            {'text': 'Test', 'confidence': 0.98},
            {'text': 'OCR', 'confidence': 0.92},
        ],
        lines=[],
        blocks=[],
        metadata={'engine': 'test'}
    )
