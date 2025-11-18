"""
Test Quality Assessment
"""

import pytest
import numpy as np
from modules.ocr.quality import (
    QualityAssessment, ConfidenceScoring, ErrorDetection, QualityMetrics
)
from modules.ocr.engines import OCRResult


@pytest.fixture
def sample_image():
    """Create sample test image"""
    return np.random.randint(0, 256, (100, 100), dtype=np.uint8)


@pytest.fixture
def sample_ocr_result():
    """Create sample OCR result"""
    return OCRResult(
        text="Sample text for testing",
        confidence=0.85,
        words=[
            {'text': 'Sample', 'confidence': 0.9},
            {'text': 'text', 'confidence': 0.8},
        ],
        lines=[],
        blocks=[]
    )


class TestQualityAssessment:
    """Test quality assessment"""

    def test_assess_image_quality(self, sample_image):
        """Test image quality assessment"""
        assessor = QualityAssessment()
        metrics = assessor.assess_image_quality(sample_image)

        assert isinstance(metrics, dict)
        assert 'overall' in metrics
        assert 0 <= metrics['overall'] <= 1

    def test_assess_ocr_result(self, sample_ocr_result, sample_image):
        """Test OCR result assessment"""
        assessor = QualityAssessment()
        metrics = assessor.assess_ocr_result(sample_ocr_result, sample_image)

        assert isinstance(metrics, QualityMetrics)
        assert 0 <= metrics.overall_quality <= 1
        assert 0 <= metrics.confidence_score <= 1


class TestConfidenceScoring:
    """Test confidence scoring"""

    def test_calculate_word_confidence(self):
        """Test word confidence calculation"""
        scorer = ConfidenceScoring()
        word = {'text': 'hello', 'confidence': 0.9}

        confidence = scorer.calculate_word_confidence(word)

        assert isinstance(confidence, float)
        assert 0 <= confidence <= 1

    def test_aggregate_confidence(self):
        """Test confidence aggregation"""
        scorer = ConfidenceScoring()
        items = [
            {'text': 'word1', 'confidence': 0.9},
            {'text': 'word2', 'confidence': 0.8},
        ]

        avg = scorer.aggregate_confidence(items, method="average")

        assert isinstance(avg, float)
        assert 0 <= avg <= 1


class TestErrorDetection:
    """Test error detection"""

    def test_detect_errors(self):
        """Test error detection"""
        detector = ErrorDetection()
        text = "Sample text with potential errors"

        errors = detector.detect_errors(text)

        assert isinstance(errors, list)

    def test_detect_spacing_issues(self):
        """Test spacing issue detection"""
        detector = ErrorDetection()
        text = "word1word2"  # Missing space

        errors = detector._detect_spacing_issues(text)

        assert isinstance(errors, list)
