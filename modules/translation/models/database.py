"""
Database models for translation module
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    JSON,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

from ..config import config

# Create database engine
engine = create_engine(config.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Translation(Base):
    """Translation records"""

    __tablename__ = "translations"

    id = Column(Integer, primary_key=True, index=True)
    source_text = Column(Text, nullable=False)
    translated_text = Column(Text, nullable=False)
    source_language = Column(String(10), nullable=False, index=True)
    target_language = Column(String(10), nullable=False, index=True)
    provider = Column(String(50), nullable=False)
    quality_score = Column(Float, nullable=True)
    character_count = Column(Integer, nullable=False)

    # Glossary reference
    glossary_id = Column(Integer, ForeignKey("glossaries.id"), nullable=True)
    glossary = relationship("Glossary", back_populates="translations")

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    user_id = Column(String(255), nullable=True, index=True)
    metadata = Column(JSON, nullable=True)

    # Performance indexes
    __table_args__ = (
        Index('idx_translation_lookup', 'source_language', 'target_language', 'provider'),
        Index('idx_created_at', 'created_at'),
    )


class Glossary(Base):
    """Glossary definitions"""

    __tablename__ = "glossaries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    source_language = Column(String(10), nullable=False)
    target_language = Column(String(10), nullable=False)

    # Relationships
    terms = relationship("GlossaryTerm", back_populates="glossary", cascade="all, delete-orphan")
    translations = relationship("Translation", back_populates="glossary")

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = Column(String(255), nullable=True, index=True)
    is_active = Column(Boolean, default=True)


class GlossaryTerm(Base):
    """Terms in a glossary"""

    __tablename__ = "glossary_terms"

    id = Column(Integer, primary_key=True, index=True)
    glossary_id = Column(Integer, ForeignKey("glossaries.id"), nullable=False)
    source_term = Column(String(500), nullable=False, index=True)
    target_term = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    case_sensitive = Column(Boolean, default=False)

    # Relationship
    glossary = relationship("Glossary", back_populates="terms")

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Performance indexes
    __table_args__ = (
        Index('idx_glossary_term_lookup', 'glossary_id', 'source_term'),
    )


class TranslationJob(Base):
    """Batch translation jobs"""

    __tablename__ = "translation_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(100), unique=True, nullable=False, index=True)
    status = Column(String(50), nullable=False, default="pending", index=True)

    # Job configuration
    source_language = Column(String(10), nullable=False)
    target_language = Column(String(10), nullable=False)
    provider = Column(String(50), nullable=False)
    glossary_id = Column(Integer, ForeignKey("glossaries.id"), nullable=True)

    # Progress tracking
    total_items = Column(Integer, default=0)
    completed_items = Column(Integer, default=0)
    failed_items = Column(Integer, default=0)
    progress_percentage = Column(Float, default=0.0)

    # Results
    result_file_path = Column(String(500), nullable=True)
    error_message = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    user_id = Column(String(255), nullable=True, index=True)
    metadata = Column(JSON, nullable=True)

    # Performance indexes
    __table_args__ = (
        Index('idx_job_status', 'status', 'created_at'),
    )


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)


def drop_db():
    """Drop all database tables"""
    Base.metadata.drop_all(bind=engine)
