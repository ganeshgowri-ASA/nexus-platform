"""OCR module API endpoints"""
from fastapi import APIRouter, UploadFile, File, Depends, Query, HTTPException, status, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import json

from app.db.session import get_db
from app.modules.ocr.service import OCRService
from app.modules.ocr.schemas import (
    OCRRequest,
    OCRResponse,
    OCRDetailResponse,
    OCRListResponse,
    OCREngineEnum,
    OCRStatusEnum
)
from app.modules.ocr.models import OCRStatus
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/extract", response_model=OCRDetailResponse, status_code=status.HTTP_201_CREATED)
async def extract_text(
    file: UploadFile = File(..., description="Image or PDF file to process"),
    engine: Optional[OCREngineEnum] = Form(OCREngineEnum.TESSERACT, description="OCR engine to use"),
    detect_language: bool = Form(True, description="Detect text language"),
    extract_tables: bool = Form(True, description="Extract tables from document"),
    detect_handwriting: bool = Form(True, description="Detect handwriting"),
    analyze_layout: bool = Form(True, description="Analyze document layout"),
    user_id: Optional[str] = Form(None, description="User ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Extract text from an image or PDF file using OCR.

    **Supported file types:**
    - Images: PNG, JPEG, TIFF
    - Documents: PDF

    **Features:**
    - Text extraction with confidence scores
    - Language detection (100+ languages)
    - Table detection and extraction
    - Handwriting recognition
    - Layout analysis
    - Multi-page PDF support

    **OCR Engines:**
    - `tesseract`: Open-source, free, good accuracy
    - `google_vision`: Google Cloud Vision API (requires API key)
    - `aws_textract`: AWS Textract (requires AWS credentials)
    """
    try:
        # Read file content
        file_content = await file.read()

        # Create OCR request
        ocr_request = OCRRequest(
            engine=engine,
            detect_language=detect_language,
            extract_tables=extract_tables,
            detect_handwriting=detect_handwriting,
            analyze_layout=analyze_layout
        )

        # Process OCR
        service = OCRService(db)
        result = await service.process_image(
            file_content=file_content,
            filename=file.filename,
            file_type=file.content_type,
            user_id=user_id,
            ocr_request=ocr_request
        )

        return result

    except Exception as e:
        logger.error(f"OCR extraction error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract text: {str(e)}"
        )


@router.get("/documents/{document_id}", response_model=OCRDetailResponse)
async def get_document(
    document_id: str,
    user_id: Optional[str] = Query(None, description="User ID for authorization"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get OCR document details by ID.

    Returns complete information about the OCR processing result including:
    - Extracted text
    - Confidence scores
    - Detected language
    - Table data
    - Layout analysis
    - Processing metadata
    """
    try:
        service = OCRService(db)
        document = await service.get_document(document_id, user_id)
        return document

    except Exception as e:
        logger.error(f"Failed to get document: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {str(e)}"
        )


@router.get("/documents", response_model=OCRListResponse)
async def list_documents(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    status: Optional[OCRStatusEnum] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db)
):
    """
    List OCR documents with pagination and filtering.

    **Filters:**
    - `user_id`: Show only documents for a specific user
    - `status`: Filter by processing status (pending, processing, completed, failed)

    **Pagination:**
    - `page`: Page number (starting from 1)
    - `page_size`: Number of items per page (max 100)
    """
    try:
        service = OCRService(db)
        ocr_status = OCRStatus(status.value) if status else None
        documents = await service.list_documents(user_id, ocr_status, page, page_size)
        return documents

    except Exception as e:
        logger.error(f"Failed to list documents: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    user_id: Optional[str] = Query(None, description="User ID for authorization"),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an OCR document and its associated file.

    This will:
    - Remove the document record from the database
    - Delete the uploaded file from storage
    - Remove all associated table data
    """
    try:
        service = OCRService(db)
        await service.delete_document(document_id, user_id)
        return None

    except Exception as e:
        logger.error(f"Failed to delete document: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {str(e)}"
        )


@router.get("/documents/{document_id}/tables")
async def get_document_tables(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all tables extracted from a document.

    Returns detailed information about each table including:
    - Table dimensions (rows, columns)
    - Cell data in 2D array format
    - Position in document
    - Confidence scores
    """
    try:
        service = OCRService(db)
        tables = await service.get_document_tables(document_id)
        return {"document_id": document_id, "tables": tables, "count": len(tables)}

    except Exception as e:
        logger.error(f"Failed to get tables: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Failed to get tables: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint for OCR module"""
    return {
        "status": "healthy",
        "module": "ocr",
        "version": "0.1.0"
    }
