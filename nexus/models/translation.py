"""
Translation Models

Defines all translation-related database models.
"""

import enum
from typing import Optional
from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    Float,
    Boolean,
    Enum,
    ForeignKey,
    JSON,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from nexus.models.base import BaseModel, SoftDeleteMixin


class TranslationStatus(str, enum.Enum):
    """Translation processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REVIEWING = "reviewing"
    APPROVED = "approved"


class TranslationEngine(str, enum.Enum):
    """Available translation engines."""

    GOOGLE = "google"
    DEEPL = "deepl"
    AZURE = "azure"
    AWS = "aws"
    OPENAI = "openai"
    CLAUDE = "claude"
    CUSTOM = "custom"


class Translation(BaseModel, SoftDeleteMixin):
    """
    Main translation model.

    Attributes:
        user_id: ID of user who requested translation
        source_text: Original text to translate
        target_text: Translated text
        source_language: Source language code (e.g., 'en')
        target_language: Target language code (e.g., 'es')
        engine: Translation engine used
        status: Processing status
        quality_score: Quality assessment score (0-1)
        confidence_score: Translation confidence (0-1)
        context: Additional context for translation
        metadata: JSON field for additional data
        cached: Whether result was from cache
        processing_time_ms: Processing time in milliseconds
        token_count: Number of tokens processed
        cost: Cost of translation
    """

    __tablename__ = "translations"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    source_text = Column(Text, nullable=False)
    target_text = Column(Text, nullable=True)
    source_language = Column(String(10), nullable=False, index=True)
    target_language = Column(String(10), nullable=False, index=True)
    engine = Column(Enum(TranslationEngine), nullable=False, index=True)
    status = Column(
        Enum(TranslationStatus),
        default=TranslationStatus.PENDING,
        nullable=False,
        index=True,
    )
    quality_score = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    context = Column(Text, nullable=True)
    metadata = Column(JSON, default=dict, nullable=False)
    cached = Column(Boolean, default=False, nullable=False)
    processing_time_ms = Column(Integer, nullable=True)
    token_count = Column(Integer, nullable=True)
    cost = Column(Float, nullable=True)

    # Relationships
    user = relationship("User", back_populates="translations")
    history = relationship(
        "TranslationHistory",
        back_populates="translation",
        cascade="all, delete-orphan",
    )
    quality_assessments = relationship(
        "TranslationQuality",
        back_populates="translation",
        cascade="all, delete-orphan",
    )

    # Indexes for performance
    __table_args__ = (
        Index(
            "idx_translation_lookup",
            "source_language",
            "target_language",
            "status",
        ),
        Index(
            "idx_user_translations",
            "user_id",
            "created_at",
        ),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<Translation(id={self.id}, "
            f"{self.source_language}->{self.target_language}, "
            f"status={self.status})>"
        )


class TranslationHistory(BaseModel):
    """
    Translation history for version control.

    Tracks all changes made to a translation.
    """

    __tablename__ = "translation_histories"

    translation_id = Column(
        Integer, ForeignKey("translations.id"), nullable=False, index=True
    )
    version = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    change_reason = Column(String(255), nullable=True)
    metadata = Column(JSON, default=dict)

    # Relationships
    translation = relationship("Translation", back_populates="history")

    __table_args__ = (
        UniqueConstraint("translation_id", "version", name="uq_translation_version"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<TranslationHistory(id={self.id}, "
            f"translation_id={self.translation_id}, "
            f"version={self.version})>"
        )


class Language(BaseModel):
    """
    Supported language definitions.

    Attributes:
        code: ISO 639-1 language code (e.g., 'en')
        name: Language name (e.g., 'English')
        native_name: Native language name (e.g., 'English')
        is_active: Whether language is currently supported
        is_rtl: Whether language is right-to-left
        supported_engines: List of engines supporting this language
    """

    __tablename__ = "languages"

    code = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    native_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_rtl = Column(Boolean, default=False, nullable=False)
    supported_engines = Column(JSON, default=list, nullable=False)

    def __repr__(self) -> str:
        """String representation."""
        return f"<Language(code={self.code}, name={self.name})>"


class Glossary(BaseModel, SoftDeleteMixin):
    """
    Translation glossary for consistent terminology.

    Attributes:
        name: Glossary name
        description: Glossary description
        user_id: Owner user ID
        is_public: Whether glossary is public
        source_language: Source language code
        target_language: Target language code
        domain: Domain/industry (e.g., 'medical', 'legal')
    """

    __tablename__ = "glossaries"

    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    is_public = Column(Boolean, default=False, nullable=False)
    source_language = Column(String(10), nullable=False)
    target_language = Column(String(10), nullable=False)
    domain = Column(String(100), nullable=True, index=True)

    # Relationships
    user = relationship("User", back_populates="glossaries")
    terms = relationship(
        "GlossaryTerm",
        back_populates="glossary",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Glossary(id={self.id}, name={self.name})>"


class GlossaryTerm(BaseModel):
    """
    Individual glossary term entry.

    Attributes:
        glossary_id: Parent glossary ID
        source_term: Term in source language
        target_term: Term in target language
        context: Usage context
        case_sensitive: Whether term matching is case-sensitive
        is_approved: Whether term is approved for use
    """

    __tablename__ = "glossary_terms"

    glossary_id = Column(
        Integer, ForeignKey("glossaries.id"), nullable=False, index=True
    )
    source_term = Column(String(255), nullable=False, index=True)
    target_term = Column(String(255), nullable=False)
    context = Column(Text, nullable=True)
    case_sensitive = Column(Boolean, default=False, nullable=False)
    is_approved = Column(Boolean, default=True, nullable=False)

    # Relationships
    glossary = relationship("Glossary", back_populates="terms")

    __table_args__ = (
        Index("idx_glossary_term_lookup", "glossary_id", "source_term"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<GlossaryTerm(id={self.id}, {self.source_term}->{self.target_term})>"


class TranslationMemory(BaseModel):
    """
    Translation memory for reusing previous translations.

    Attributes:
        source_text: Source text
        target_text: Target text
        source_language: Source language code
        target_language: Target language code
        context_hash: Hash of context for matching
        usage_count: Number of times reused
        quality_score: Average quality score
        domain: Domain/category
    """

    __tablename__ = "translation_memories"

    source_text = Column(Text, nullable=False, index=True)
    target_text = Column(Text, nullable=False)
    source_language = Column(String(10), nullable=False, index=True)
    target_language = Column(String(10), nullable=False, index=True)
    context_hash = Column(String(64), nullable=True, index=True)
    usage_count = Column(Integer, default=1, nullable=False)
    quality_score = Column(Float, nullable=True)
    domain = Column(String(100), nullable=True, index=True)

    __table_args__ = (
        Index(
            "idx_tm_lookup",
            "source_language",
            "target_language",
            "context_hash",
        ),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<TranslationMemory(id={self.id}, "
            f"{self.source_language}->{self.target_language})>"
        )


class TranslationQuality(BaseModel):
    """
    Quality assessment results for translations.

    Attributes:
        translation_id: Associated translation ID
        fluency_score: Fluency score (0-1)
        adequacy_score: Adequacy score (0-1)
        overall_score: Overall quality score (0-1)
        back_translation: Back-translated text for validation
        back_translation_similarity: Similarity score with original
        errors: List of detected errors
        suggestions: Improvement suggestions
        assessed_by: User who performed assessment
    """

    __tablename__ = "translation_qualities"

    translation_id = Column(
        Integer, ForeignKey("translations.id"), nullable=False, index=True
    )
    fluency_score = Column(Float, nullable=True)
    adequacy_score = Column(Float, nullable=True)
    overall_score = Column(Float, nullable=True)
    back_translation = Column(Text, nullable=True)
    back_translation_similarity = Column(Float, nullable=True)
    errors = Column(JSON, default=list, nullable=False)
    suggestions = Column(JSON, default=list, nullable=False)
    assessed_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    translation = relationship("Translation", back_populates="quality_assessments")

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<TranslationQuality(id={self.id}, "
            f"translation_id={self.translation_id}, "
            f"score={self.overall_score})>"
        )
