"""
FastAPI dependencies
"""

from typing import Generator
from sqlalchemy.orm import Session

from ..models.database import SessionLocal
from ..services.translation_service import TranslationService
from ..services.language_detection import LanguageDetectionService
from ..services.glossary_service import GlossaryService
from ..services.quality_scoring import QualityScoringService


def get_db() -> Generator[Session, None, None]:
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_translation_service() -> TranslationService:
    """Translation service dependency"""
    return TranslationService()


def get_language_detection_service() -> LanguageDetectionService:
    """Language detection service dependency"""
    return LanguageDetectionService()


def get_glossary_service() -> GlossaryService:
    """Glossary service dependency"""
    return GlossaryService()


def get_quality_service() -> QualityScoringService:
    """Quality scoring service dependency"""
    return QualityScoringService()
