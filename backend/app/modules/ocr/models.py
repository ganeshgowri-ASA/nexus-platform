"""OCR module database models"""
from sqlalchemy import Column, String, Text, Float, Integer, Boolean, JSON, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
import enum
from app.db.base import BaseModel


class OCRStatus(str, enum.Enum):
    """OCR processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class OCREngine(str, enum.Enum):
    """Available OCR engines"""
    TESSERACT = "tesseract"
    GOOGLE_VISION = "google_vision"
    AWS_TEXTRACT = "aws_textract"


class OCRDocument(BaseModel):
    """OCR document model"""
    __tablename__ = "ocr_documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=True, index=True)
    file_name = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_type = Column(String(50), nullable=False)  # image/png, application/pdf, etc.
    file_size = Column(Integer, nullable=False)  # Size in bytes

    # OCR Processing
    status = Column(SQLEnum(OCRStatus), default=OCRStatus.PENDING, nullable=False, index=True)
    engine = Column(SQLEnum(OCREngine), default=OCREngine.TESSERACT, nullable=False)
    extracted_text = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)

    # Language Detection
    detected_language = Column(String(10), nullable=True)
    languages = Column(JSONB, nullable=True)  # List of detected languages with confidence

    # Advanced Features
    layout_analysis = Column(JSONB, nullable=True)  # Layout structure information
    handwriting_detected = Column(Boolean, default=False)
    tables_detected = Column(Integer, default=0)
    table_data = Column(JSONB, nullable=True)  # Extracted table data

    # Processing Metadata
    processing_time = Column(Float, nullable=True)  # Time in seconds
    error_message = Column(Text, nullable=True)
    metadata = Column(JSONB, nullable=True)  # Additional metadata

    def __repr__(self):
        return f"<OCRDocument(id={self.id}, file_name={self.file_name}, status={self.status})>"


class OCRTable(BaseModel):
    """Extracted table data from OCR"""
    __tablename__ = "ocr_tables"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), nullable=False, index=True)
    table_index = Column(Integer, nullable=False)  # Position in document
    rows = Column(Integer, nullable=False)
    columns = Column(Integer, nullable=False)
    data = Column(JSONB, nullable=False)  # Table data as 2D array
    confidence_score = Column(Float, nullable=True)
    metadata = Column(JSONB, nullable=True)

    def __repr__(self):
        return f"<OCRTable(id={self.id}, document_id={self.document_id}, rows={self.rows}, cols={self.columns})>"
