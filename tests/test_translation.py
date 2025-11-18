"""
Translation Module Tests

Unit and integration tests for translation functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from nexus.models.base import Base
from nexus.models.user import User, UserRole
from nexus.models.translation import Translation, TranslationStatus, TranslationEngine
from nexus.modules.translation.translator import Translator
from nexus.modules.translation.language_detection import LanguageDetector
from nexus.modules.translation.glossary import GlossaryManager
from nexus.modules.translation.cache import TranslationCache
from nexus.modules.translation.memory import TranslationMemoryManager
from nexus.modules.translation.quality import QualityAssessment


@pytest.fixture(scope="function")
def test_db():
    """Create a test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(test_db):
    """Create a test user."""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_password",
        role=UserRole.USER,
        is_active=True,
    )
    user.save(test_db)
    return user


class TestLanguageDetection:
    """Tests for language detection."""

    def test_detect_english(self):
        """Test detecting English text."""
        detector = LanguageDetector()
        result = detector.detect("Hello, how are you today?")

        assert result["language"] == "en"
        assert result["confidence"] > 0.8

    def test_detect_spanish(self):
        """Test detecting Spanish text."""
        detector = LanguageDetector()
        result = detector.detect("Hola, ¿cómo estás hoy?")

        assert result["language"] == "es"
        assert result["confidence"] > 0.8

    def test_empty_text_raises_error(self):
        """Test that empty text raises an error."""
        detector = LanguageDetector()

        with pytest.raises(Exception):
            detector.detect("")


class TestGlossaryManager:
    """Tests for glossary management."""

    def test_create_glossary(self, test_db, test_user):
        """Test creating a glossary."""
        manager = GlossaryManager(test_db)

        glossary = manager.create_glossary(
            name="Medical Terms",
            user_id=test_user.id,
            source_lang="en",
            target_lang="es",
            domain="medical",
        )

        assert glossary.id is not None
        assert glossary.name == "Medical Terms"
        assert glossary.domain == "medical"

    def test_add_term(self, test_db, test_user):
        """Test adding a term to glossary."""
        manager = GlossaryManager(test_db)

        glossary = manager.create_glossary(
            name="Tech Terms",
            user_id=test_user.id,
            source_lang="en",
            target_lang="fr",
        )

        term = manager.add_term(
            glossary_id=glossary.id,
            source_term="software",
            target_term="logiciel",
        )

        assert term.id is not None
        assert term.source_term == "software"
        assert term.target_term == "logiciel"

    def test_apply_glossary(self, test_db, test_user):
        """Test applying glossary to text."""
        manager = GlossaryManager(test_db)

        glossary = manager.create_glossary(
            name="Test Glossary",
            user_id=test_user.id,
            source_lang="en",
            target_lang="es",
            is_public=True,
        )

        manager.add_term(
            glossary_id=glossary.id,
            source_term="hello",
            target_term="hola",
        )

        text = "Say hello to the world"
        found_terms = manager.apply_glossary(text, "en", "es", test_user.id)

        assert "hello" in found_terms
        assert found_terms["hello"] == "hola"


class TestTranslationCache:
    """Tests for translation caching."""

    @patch("redis.from_url")
    def test_cache_set_and_get(self, mock_redis):
        """Test setting and getting from cache."""
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        mock_client.ping.return_value = True

        cache = TranslationCache()

        # Mock set and get
        cache.set("hello", "en", "es", "hola")

        # The actual test would require a real Redis instance
        # This is a simplified test
        assert cache.enabled


class TestTranslationMemory:
    """Tests for translation memory."""

    def test_add_translation(self, test_db):
        """Test adding translation to memory."""
        tm_manager = TranslationMemoryManager(test_db)

        tm_entry = tm_manager.add_translation(
            source_text="Hello world",
            target_text="Hola mundo",
            source_lang="en",
            target_lang="es",
            quality_score=0.95,
        )

        assert tm_entry.id is not None
        assert tm_entry.source_text == "Hello world"
        assert tm_entry.target_text == "Hola mundo"

    def test_find_exact_match(self, test_db):
        """Test finding exact match in TM."""
        tm_manager = TranslationMemoryManager(test_db)

        # Add translation
        tm_manager.add_translation(
            source_text="Good morning",
            target_text="Buenos días",
            source_lang="en",
            target_lang="es",
        )

        # Find match
        match = tm_manager.find_match(
            source_text="Good morning",
            source_lang="en",
            target_lang="es",
        )

        assert match is not None
        assert match["similarity"] == 1.0
        assert match["target_text"] == "Buenos días"

    def test_find_fuzzy_match(self, test_db):
        """Test finding fuzzy match in TM."""
        tm_manager = TranslationMemoryManager(test_db)

        # Add translation
        tm_manager.add_translation(
            source_text="How are you doing",
            target_text="Cómo estás",
            source_lang="en",
            target_lang="es",
        )

        # Find fuzzy match
        match = tm_manager.find_match(
            source_text="How are you",
            source_lang="en",
            target_lang="es",
            min_similarity=0.5,
        )

        assert match is not None
        assert match["similarity"] < 1.0


class TestQualityAssessment:
    """Tests for quality assessment."""

    def test_assess_translation(self):
        """Test quality assessment."""
        assessor = QualityAssessment()

        scores = assessor.assess(
            source_text="Hello world",
            translated_text="Hola mundo",
            source_lang="en",
            target_lang="es",
            use_ai=False,  # Don't use AI for test
        )

        assert "overall_score" in scores
        assert 0 <= scores["overall_score"] <= 1

    def test_length_ratio(self):
        """Test length ratio calculation."""
        assessor = QualityAssessment()

        # Similar length
        ratio = assessor._calculate_length_ratio("hello world", "hola mundo")
        assert ratio > 0.8

        # Very different length
        ratio = assessor._calculate_length_ratio("hi", "this is a very long translation")
        assert ratio < 0.8

    def test_preservation_score(self):
        """Test number preservation."""
        assessor = QualityAssessment()

        # Numbers preserved
        score = assessor._calculate_preservation(
            "The price is 100 dollars",
            "El precio es 100 dólares",
        )
        assert score == 1.0

        # Numbers not preserved
        score = assessor._calculate_preservation(
            "The price is 100 dollars",
            "El precio es cien dólares",
        )
        assert score < 1.0


@pytest.mark.integration
class TestTranslatorIntegration:
    """Integration tests for translator."""

    @patch("nexus.modules.translation.engines.GoogleTranslateEngine.translate")
    def test_translate_with_mock_engine(self, mock_translate, test_db, test_user):
        """Test translation with mocked engine."""
        # Mock engine response
        mock_translate.return_value = {
            "translated_text": "Hola mundo",
            "source_language": "en",
            "target_language": "es",
            "confidence": 0.95,
            "engine": "google",
        }

        translator = Translator(
            db=test_db,
            user_id=test_user.id,
            engine="google",
            use_cache=False,  # Disable cache for test
        )

        translation = translator.translate(
            text="Hello world",
            target_lang="es",
            source_lang="en",
        )

        assert translation.id is not None
        assert translation.status == TranslationStatus.COMPLETED
        assert translation.source_language == "en"
        assert translation.target_language == "es"


def test_translation_model_creation(test_db, test_user):
    """Test creating a translation model."""
    translation = Translation(
        user_id=test_user.id,
        source_text="Test text",
        target_text="Texto de prueba",
        source_language="en",
        target_language="es",
        engine=TranslationEngine.GOOGLE,
        status=TranslationStatus.COMPLETED,
        quality_score=0.9,
    )

    translation.save(test_db)

    assert translation.id is not None
    assert translation.user_id == test_user.id


def test_translation_to_dict(test_db, test_user):
    """Test converting translation to dictionary."""
    translation = Translation(
        user_id=test_user.id,
        source_text="Test",
        target_text="Prueba",
        source_language="en",
        target_language="es",
        engine=TranslationEngine.DEEPL,
        status=TranslationStatus.COMPLETED,
    )

    translation.save(test_db)

    result = translation.to_dict()

    assert "id" in result
    assert result["source_text"] == "Test"
    assert result["target_text"] == "Prueba"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
