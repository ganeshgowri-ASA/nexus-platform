"""
Unit tests for translation service
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from modules.translation.services.translation_service import TranslationService


class TestTranslationService:
    """Tests for TranslationService"""

    def setup_method(self):
        """Setup test fixtures"""
        self.service = TranslationService()

    @pytest.mark.asyncio
    async def test_translate_with_google(self):
        """Test translation with Google provider"""
        # Mock the provider
        with patch.object(
            self.service,
            'get_provider',
            return_value=Mock(translate=AsyncMock(return_value="Hola mundo"))
        ):
            result = await self.service.translate(
                text="Hello world",
                source_language="en",
                target_language="es",
                provider="google",
                enable_quality_scoring=False
            )

            assert result['translated_text'] == "Hola mundo"
            assert result['source_text'] == "Hello world"
            assert result['source_language'] == "en"
            assert result['target_language'] == "es"

    @pytest.mark.asyncio
    async def test_translate_with_invalid_provider(self):
        """Test translation with invalid provider"""
        with pytest.raises(ValueError):
            await self.service.translate(
                text="Hello world",
                source_language="en",
                target_language="es",
                provider="invalid_provider"
            )

    @pytest.mark.asyncio
    async def test_detect_language(self):
        """Test language detection"""
        mock_result = {
            'language': 'en',
            'language_name': 'English',
            'confidence': 0.99
        }

        with patch.object(
            self.service,
            'get_provider',
            return_value=Mock(detect_language=AsyncMock(return_value=mock_result))
        ):
            result = await self.service.detect_language("Hello world")

            assert result['language'] == 'en'
            assert result['language_name'] == 'English'
            assert result['confidence'] == 0.99

    @pytest.mark.asyncio
    async def test_batch_translation(self):
        """Test batch translation"""
        texts = ["Hello", "Goodbye", "Thank you"]
        expected = ["Hola", "Adiós", "Gracias"]

        with patch.object(
            self.service,
            'get_provider',
            return_value=Mock(translate_batch=AsyncMock(return_value=expected))
        ):
            result = await self.service.translate_batch(
                texts=texts,
                source_language="en",
                target_language="es",
                provider="google"
            )

            assert len(result) == 3
            assert result == expected
