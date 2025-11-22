"""Tests for Translation module"""
import pytest
from httpx import AsyncClient


class TestTranslationEndpoints:
    """Test Translation API endpoints"""

    @pytest.mark.asyncio
    async def test_translation_health_check(self, client: AsyncClient):
        """Test Translation health check endpoint"""
        response = await client.get("/api/v1/translation/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["module"] == "translation"

    @pytest.mark.asyncio
    async def test_translate_text_success(self, client: AsyncClient, sample_text: str):
        """Test successful text translation"""
        payload = {
            "text": sample_text,
            "source_language": "en",
            "target_language": "es",
            "service": "google"
        }

        response = await client.post("/api/v1/translation/translate", json=payload)
        assert response.status_code == 201
        result = response.json()

        assert "id" in result
        assert "translated_text" in result
        assert "source_language" in result
        assert "target_language" in result
        assert result["target_language"] == "es"

    @pytest.mark.asyncio
    async def test_translate_with_auto_detection(self, client: AsyncClient):
        """Test translation with automatic language detection"""
        payload = {
            "text": "Hola mundo",
            "source_language": "auto",
            "target_language": "en",
            "service": "google"
        }

        response = await client.post("/api/v1/translation/translate", json=payload)
        assert response.status_code == 201
        result = response.json()

        assert "detected_language" in result

    @pytest.mark.asyncio
    async def test_translate_empty_text(self, client: AsyncClient):
        """Test translation with empty text"""
        payload = {
            "text": "",
            "source_language": "en",
            "target_language": "es",
            "service": "google"
        }

        response = await client.post("/api/v1/translation/translate", json=payload)
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_batch_translate(self, client: AsyncClient):
        """Test batch translation"""
        payload = {
            "texts": ["Hello world", "Good morning", "Thank you"],
            "source_language": "en",
            "target_language": "es",
            "service": "google"
        }

        response = await client.post("/api/v1/translation/batch", json=payload)
        assert response.status_code == 201
        result = response.json()

        assert "id" in result
        assert "total_items" in result
        assert result["total_items"] == 3

    @pytest.mark.asyncio
    async def test_list_translations(self, client: AsyncClient):
        """Test listing translations"""
        response = await client.get("/api/v1/translation/translations")
        assert response.status_code == 200
        data = response.json()

        assert "total" in data
        assert "items" in data
        assert "page" in data

    @pytest.mark.asyncio
    async def test_get_supported_languages(self, client: AsyncClient):
        """Test getting supported languages"""
        response = await client.get("/api/v1/translation/languages")
        assert response.status_code == 200
        data = response.json()

        assert "languages" in data
        assert "count" in data
        assert len(data["languages"]) > 0


class TestGlossaryEndpoints:
    """Test Glossary API endpoints"""

    @pytest.mark.asyncio
    async def test_create_glossary(self, client: AsyncClient):
        """Test creating a glossary"""
        payload = {
            "name": "Test Glossary",
            "description": "Test description",
            "source_language": "en",
            "target_language": "es",
            "entries": {
                "hello": "hola",
                "world": "mundo",
                "test": "prueba"
            }
        }

        response = await client.post("/api/v1/translation/glossaries", json=payload)
        assert response.status_code == 201
        result = response.json()

        assert "id" in result
        assert result["name"] == "Test Glossary"
        assert result["entry_count"] == 3

    @pytest.mark.asyncio
    async def test_create_glossary_empty_entries(self, client: AsyncClient):
        """Test creating glossary with empty entries"""
        payload = {
            "name": "Empty Glossary",
            "source_language": "en",
            "target_language": "es",
            "entries": {}
        }

        response = await client.post("/api/v1/translation/glossaries", json=payload)
        assert response.status_code == 400  # Should fail validation

    @pytest.mark.asyncio
    async def test_list_glossaries(self, client: AsyncClient):
        """Test listing glossaries"""
        response = await client.get("/api/v1/translation/glossaries")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestTranslationProcessor:
    """Test Translation processor logic"""

    @pytest.mark.asyncio
    async def test_processor_initialization(self):
        """Test translation processor initialization"""
        from app.modules.translation.processor import TranslationProcessor

        processor = TranslationProcessor(service="google")
        assert processor.service == "google"

    @pytest.mark.asyncio
    async def test_detect_language(self):
        """Test language detection"""
        from app.modules.translation.processor import TranslationProcessor

        processor = TranslationProcessor()
        result = await processor.detect_language("Hello world")

        assert "detected_language" in result
        assert "confidence" in result


class TestTranslationUtils:
    """Test Translation utility functions"""

    def test_validate_language_code(self):
        """Test language code validation"""
        from app.modules.translation.utils import validate_language_code

        assert validate_language_code("en") is True
        assert validate_language_code("es") is True
        assert validate_language_code("auto") is True
        assert validate_language_code("invalid") is False

    def test_split_text_into_chunks(self):
        """Test text splitting"""
        from app.modules.translation.utils import split_text_into_chunks

        text = "A" * 10000
        chunks = split_text_into_chunks(text, max_length=5000)

        assert len(chunks) > 1
        assert all(len(chunk) <= 5000 for chunk in chunks)

    def test_calculate_quality_score(self):
        """Test quality score calculation"""
        from app.modules.translation.utils import calculate_quality_score

        score = calculate_quality_score(
            source_text="Hello world",
            translated_text="Hola mundo",
            confidence=0.9
        )

        assert 0 <= score <= 100

    def test_apply_glossary(self):
        """Test glossary application"""
        from app.modules.translation.utils import apply_glossary

        text = "This is a test message"
        glossary = {"test": "prueba"}

        result_text, replacements = apply_glossary(text, glossary)

        assert "prueba" in result_text
        assert replacements == 1

    def test_get_supported_languages(self):
        """Test getting supported languages"""
        from app.modules.translation.utils import get_supported_languages

        languages = get_supported_languages()

        assert len(languages) > 0
        assert all("code" in lang and "name" in lang for lang in languages)


class TestTranslationModels:
    """Test Translation database models"""

    def test_translation_creation(self):
        """Test Translation model creation"""
        from app.modules.translation.models import (
            Translation,
            TranslationStatus,
            TranslationService,
            TranslationType
        )

        translation = Translation(
            source_text="Hello world",
            source_language="en",
            target_language="es",
            status=TranslationStatus.PENDING,
            service=TranslationService.GOOGLE,
            translation_type=TranslationType.TEXT,
            character_count=11
        )

        assert translation.source_text == "Hello world"
        assert translation.source_language == "en"
        assert translation.target_language == "es"

    def test_glossary_creation(self):
        """Test TranslationGlossary model creation"""
        from app.modules.translation.models import TranslationGlossary

        glossary = TranslationGlossary(
            name="Test Glossary",
            source_language="en",
            target_language="es",
            entries={"hello": "hola", "world": "mundo"},
            entry_count=2
        )

        assert glossary.name == "Test Glossary"
        assert glossary.entry_count == 2
        assert len(glossary.entries) == 2

    def test_batch_translation_creation(self):
        """Test BatchTranslation model creation"""
        from app.modules.translation.models import (
            BatchTranslation,
            TranslationStatus,
            TranslationService
        )

        batch = BatchTranslation(
            name="Test Batch",
            source_language="en",
            target_language="es",
            status=TranslationStatus.PENDING,
            service=TranslationService.GOOGLE,
            total_items=10,
            total_characters=500
        )

        assert batch.total_items == 10
        assert batch.completed_items == 0
        assert batch.failed_items == 0
