"""Translation module database models"""
from sqlalchemy import Column, String, Text, Float, Integer, Boolean, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
import enum
from app.db.base import BaseModel


class TranslationStatus(str, enum.Enum):
    """Translation processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TranslationService(str, enum.Enum):
    """Available translation services"""
    GOOGLE = "google"
    DEEPL = "deepl"
    ANTHROPIC = "anthropic"


class TranslationType(str, enum.Enum):
    """Type of translation"""
    TEXT = "text"
    DOCUMENT = "document"
    BATCH = "batch"
    REALTIME = "realtime"


class Translation(BaseModel):
    """Translation model"""
    __tablename__ = "translations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=True, index=True)

    # Source Content
    source_text = Column(Text, nullable=False)
    source_language = Column(String(10), nullable=False, index=True)
    detected_language = Column(String(10), nullable=True)

    # Target Content
    translated_text = Column(Text, nullable=True)
    target_language = Column(String(10), nullable=False, index=True)

    # Translation Processing
    status = Column(SQLEnum(TranslationStatus), default=TranslationStatus.PENDING, nullable=False, index=True)
    service = Column(SQLEnum(TranslationService), default=TranslationService.GOOGLE, nullable=False)
    translation_type = Column(SQLEnum(TranslationType), default=TranslationType.TEXT, nullable=False)

    # Quality Metrics
    quality_score = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)

    # Glossary & Context
    glossary_id = Column(String(36), nullable=True, index=True)
    context = Column(Text, nullable=True)

    # Processing Metadata
    character_count = Column(Integer, nullable=False)
    processing_time = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    metadata = Column(JSONB, nullable=True)

    def __repr__(self):
        return f"<Translation(id={self.id}, {self.source_language}->{self.target_language}, status={self.status})>"


class TranslationGlossary(BaseModel):
    """Custom glossary for translation consistency"""
    __tablename__ = "translation_glossaries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    source_language = Column(String(10), nullable=False)
    target_language = Column(String(10), nullable=False)

    # Glossary entries: {term: translation, ...}
    entries = Column(JSONB, nullable=False, default={})
    entry_count = Column(Integer, default=0)

    is_active = Column(Boolean, default=True)
    metadata = Column(JSONB, nullable=True)

    def __repr__(self):
        return f"<TranslationGlossary(id={self.id}, name={self.name}, entries={self.entry_count})>"


class DocumentTranslation(BaseModel):
    """Document translation model"""
    __tablename__ = "document_translations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=True, index=True)

    # Source Document
    source_file_name = Column(String(500), nullable=False)
    source_file_path = Column(String(1000), nullable=False)
    source_file_type = Column(String(50), nullable=False)
    source_language = Column(String(10), nullable=False)

    # Target Document
    target_file_path = Column(String(1000), nullable=True)
    target_language = Column(String(10), nullable=False)

    # Processing
    status = Column(SQLEnum(TranslationStatus), default=TranslationStatus.PENDING, nullable=False, index=True)
    service = Column(SQLEnum(TranslationService), default=TranslationService.GOOGLE, nullable=False)

    # Statistics
    page_count = Column(Integer, nullable=True)
    segment_count = Column(Integer, nullable=True)
    character_count = Column(Integer, nullable=False)
    processing_time = Column(Float, nullable=True)

    # Quality & Glossary
    quality_score = Column(Float, nullable=True)
    glossary_id = Column(String(36), nullable=True)

    error_message = Column(Text, nullable=True)
    metadata = Column(JSONB, nullable=True)

    def __repr__(self):
        return f"<DocumentTranslation(id={self.id}, file={self.source_file_name}, status={self.status})>"


class BatchTranslation(BaseModel):
    """Batch translation job"""
    __tablename__ = "batch_translations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=True, index=True)
    name = Column(String(255), nullable=False)

    source_language = Column(String(10), nullable=False)
    target_language = Column(String(10), nullable=False)

    # Batch Processing
    status = Column(SQLEnum(TranslationStatus), default=TranslationStatus.PENDING, nullable=False, index=True)
    service = Column(SQLEnum(TranslationService), default=TranslationService.GOOGLE, nullable=False)

    total_items = Column(Integer, default=0)
    completed_items = Column(Integer, default=0)
    failed_items = Column(Integer, default=0)

    # Statistics
    total_characters = Column(Integer, default=0)
    processing_time = Column(Float, nullable=True)

    glossary_id = Column(String(36), nullable=True)
    error_message = Column(Text, nullable=True)
    metadata = Column(JSONB, nullable=True)

    def __repr__(self):
        return f"<BatchTranslation(id={self.id}, name={self.name}, {self.completed_items}/{self.total_items})>"
