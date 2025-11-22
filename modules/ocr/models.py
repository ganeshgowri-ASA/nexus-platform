"""
Database Models

SQLAlchemy models for OCR job tracking, documents, pages, and results.
"""

import logging
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime,
    Boolean, JSON, ForeignKey, Enum as SQLEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

logger = logging.getLogger(__name__)

Base = declarative_base()


class JobStatus(enum.Enum):
    """OCR job status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OCRJob(Base):
    """OCR job tracking"""

    __tablename__ = "ocr_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(100), unique=True, index=True, nullable=False)
    user_id = Column(Integer, index=True)  # NEXUS user ID
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING)

    # File information
    file_name = Column(String(255))
    file_path = Column(String(500))
    file_size = Column(Integer)
    file_type = Column(String(50))

    # Processing parameters
    engine_type = Column(String(50), default="tesseract")
    language = Column(String(50), default="eng")
    options = Column(JSON)

    # Results
    page_count = Column(Integer, default=0)
    total_confidence = Column(Float, default=0.0)
    processing_time = Column(Float)  # in seconds
    error_message = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    documents = relationship("Document", back_populates="job", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<OCRJob(job_id='{self.job_id}', status='{self.status}')>"


class Document(Base):
    """Processed document"""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("ocr_jobs.id"), nullable=False)

    # Document information
    document_id = Column(String(100), unique=True, index=True)
    file_name = Column(String(255))
    file_type = Column(String(50))

    # Content
    text_content = Column(Text)
    confidence = Column(Float)
    language = Column(String(50))

    # Metadata
    metadata = Column(JSON)

    # Quality metrics
    image_quality = Column(Float)
    text_clarity = Column(Float)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    job = relationship("OCRJob", back_populates="documents")
    pages = relationship("Page", back_populates="document", cascade="all, delete-orphan")
    text_blocks = relationship("TextBlock", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Document(document_id='{self.document_id}')>"


class Page(Base):
    """Document page"""

    __tablename__ = "pages"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)

    # Page information
    page_number = Column(Integer, nullable=False)
    page_id = Column(String(100), unique=True, index=True)

    # Content
    text_content = Column(Text)
    confidence = Column(Float)

    # Image information
    image_width = Column(Integer)
    image_height = Column(Integer)
    image_dpi = Column(Integer)

    # Quality
    image_quality_score = Column(Float)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="pages")

    def __repr__(self):
        return f"<Page(page_id='{self.page_id}', page_number={self.page_number})>"


class TextBlock(Base):
    """Text block with position and metadata"""

    __tablename__ = "text_blocks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    page_number = Column(Integer)

    # Text content
    text = Column(Text)
    confidence = Column(Float)

    # Position (bounding box)
    bbox_x = Column(Integer)
    bbox_y = Column(Integer)
    bbox_width = Column(Integer)
    bbox_height = Column(Integer)

    # Type
    block_type = Column(String(50))  # text, heading, list, etc.

    # Formatting
    font_size = Column(Float)
    is_bold = Column(Boolean, default=False)
    is_italic = Column(Boolean, default=False)

    # Order
    reading_order = Column(Integer)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="text_blocks")

    def __repr__(self):
        return f"<TextBlock(text='{self.text[:50]}...')>"


class Confidence(Base):
    """Confidence scores and quality metrics"""

    __tablename__ = "confidence_scores"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("ocr_jobs.id"))
    document_id = Column(Integer, ForeignKey("documents.id"))

    # Confidence metrics
    overall_confidence = Column(Float)
    word_level_avg = Column(Float)
    line_level_avg = Column(Float)
    block_level_avg = Column(Float)

    # Quality metrics
    image_quality = Column(Float)
    text_clarity = Column(Float)
    layout_complexity = Column(Float)

    # Issues detected
    low_confidence_words = Column(Integer, default=0)
    potential_errors = Column(Integer, default=0)
    issues = Column(JSON)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Confidence(overall={self.overall_confidence:.2f})>"


# Database utility functions
def create_tables(engine):
    """Create all tables"""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")


def drop_tables(engine):
    """Drop all tables"""
    Base.metadata.drop_all(bind=engine)
    logger.info("Database tables dropped")
