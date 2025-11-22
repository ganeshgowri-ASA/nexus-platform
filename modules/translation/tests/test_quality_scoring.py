"""
Unit tests for quality scoring service
"""

import pytest
from modules.translation.services.quality_scoring import QualityScoringService


class TestQualityScoringService:
    """Tests for QualityScoringService"""

    def setup_method(self):
        """Setup test fixtures"""
        self.service = QualityScoringService()

    @pytest.mark.asyncio
    async def test_calculate_quality_score(self):
        """Test quality score calculation"""
        result = await self.service.calculate_quality_score(
            source_text="Hello, world!",
            translated_text="Hola, mundo!",
            source_language="en",
            target_language="es"
        )

        assert 'score' in result
        assert 'rating' in result
        assert 'factors' in result
        assert 'suggestions' in result
        assert 0.0 <= result['score'] <= 1.0
        assert result['rating'] in ['excellent', 'good', 'acceptable', 'poor']

    def test_length_ratio_calculation(self):
        """Test length ratio calculation"""
        score = self.service._calculate_length_ratio("Hello", "Hola")
        assert 0.0 <= score <= 1.0

    def test_number_preservation(self):
        """Test number preservation scoring"""
        score = self.service._calculate_number_preservation(
            "There are 5 cats",
            "Hay 5 gatos"
        )
        assert score == 1.0  # Numbers are preserved

    def test_punctuation_preservation(self):
        """Test punctuation preservation"""
        score = self.service._calculate_punctuation_preservation(
            "Hello, world!",
            "Hola, mundo!"
        )
        assert score > 0.8  # Punctuation is well preserved

    @pytest.mark.asyncio
    async def test_compare_translations(self):
        """Test translation comparison"""
        translations = [
            {'text': 'Hola mundo', 'provider': 'google'},
            {'text': 'Hola mundo', 'provider': 'deepl'}
        ]

        result = self.service.compare_translations(translations)

        assert 'similarities' in result
        assert 'average_similarity' in result
        assert 'consensus' in result
