"""OCR service layer - business logic"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional, Dict, Any
from datetime import datetime
import os

from app.modules.ocr.models import OCRDocument, OCRTable, OCRStatus, OCREngine
from app.modules.ocr.processor import OCRProcessor
from app.modules.ocr.schemas import OCRRequest, OCRResponse, OCRDetailResponse, OCRListResponse
from app.modules.ocr.utils import save_uploaded_file, validate_image_file
from app.core.config import settings
from app.core.logging import get_logger
from app.utils.exceptions import OCRProcessingError, InvalidFileTypeError, FileSizeExceededError

logger = get_logger(__name__)


class OCRService:
    """OCR service for text extraction operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_image(
        self,
        file_content: bytes,
        filename: str,
        file_type: str,
        user_id: Optional[str] = None,
        ocr_request: Optional[OCRRequest] = None
    ) -> OCRDetailResponse:
        """Process image/PDF for OCR extraction"""

        # Validate file size
        if len(file_content) > settings.MAX_UPLOAD_SIZE:
            raise FileSizeExceededError(
                f"File size {len(file_content)} exceeds maximum {settings.MAX_UPLOAD_SIZE}"
            )

        # Validate file type
        allowed_types = ['image/png', 'image/jpeg', 'image/jpg', 'image/tiff', 'application/pdf']
        if file_type not in allowed_types:
            raise InvalidFileTypeError(f"File type {file_type} not supported. Allowed: {allowed_types}")

        # Use default OCR request if not provided
        if ocr_request is None:
            ocr_request = OCRRequest()

        try:
            # Save uploaded file
            file_path = save_uploaded_file(file_content, filename, settings.UPLOAD_DIR)

            # Create database record
            ocr_doc = OCRDocument(
                user_id=user_id,
                file_name=filename,
                file_path=file_path,
                file_type=file_type,
                file_size=len(file_content),
                status=OCRStatus.PROCESSING,
                engine=OCREngine(ocr_request.engine.value)
            )

            self.db.add(ocr_doc)
            await self.db.commit()
            await self.db.refresh(ocr_doc)

            logger.info(f"Created OCR document {ocr_doc.id} for file {filename}")

            # Process OCR
            try:
                processor = OCRProcessor(engine=ocr_request.engine.value)

                if file_type == 'application/pdf':
                    # Process PDF (multi-page)
                    pdf_results = await processor.extract_from_pdf(
                        file_path,
                        detect_language=ocr_request.detect_language,
                        extract_tables=ocr_request.extract_tables,
                        detect_handwriting=ocr_request.detect_handwriting,
                        analyze_layout=ocr_request.analyze_layout
                    )

                    # Combine results from all pages
                    combined_text = "\n\n".join([r["extracted_text"] for r in pdf_results])
                    avg_confidence = sum([r["confidence_score"] for r in pdf_results]) / len(pdf_results)

                    result = {
                        "extracted_text": combined_text,
                        "confidence_score": avg_confidence,
                        "detected_language": pdf_results[0].get("detected_language"),
                        "languages": pdf_results[0].get("languages"),
                        "handwriting_detected": any(r.get("handwriting_detected") for r in pdf_results),
                        "tables_detected": sum(r.get("tables_detected", 0) for r in pdf_results),
                        "table_data": [t for r in pdf_results for t in r.get("table_data", [])],
                        "layout_analysis": pdf_results[0].get("layout_analysis"),
                        "processing_time": sum(r.get("processing_time", 0) for r in pdf_results),
                        "metadata": {"pages": len(pdf_results), "page_results": pdf_results}
                    }
                else:
                    # Process single image
                    result = await processor.extract_text(
                        file_path,
                        detect_language=ocr_request.detect_language,
                        extract_tables=ocr_request.extract_tables,
                        detect_handwriting=ocr_request.detect_handwriting,
                        analyze_layout=ocr_request.analyze_layout
                    )

                # Update database record with results
                ocr_doc.status = OCRStatus.COMPLETED
                ocr_doc.extracted_text = result["extracted_text"]
                ocr_doc.confidence_score = result["confidence_score"]
                ocr_doc.detected_language = result.get("detected_language")
                ocr_doc.languages = result.get("languages")
                ocr_doc.handwriting_detected = result.get("handwriting_detected", False)
                ocr_doc.tables_detected = result.get("tables_detected", 0)
                ocr_doc.table_data = result.get("table_data")
                ocr_doc.layout_analysis = result.get("layout_analysis")
                ocr_doc.processing_time = result.get("processing_time")
                ocr_doc.metadata = result.get("metadata")

                await self.db.commit()
                await self.db.refresh(ocr_doc)

                logger.info(f"OCR processing completed for document {ocr_doc.id}")

                # Save extracted tables if any
                if result.get("table_data"):
                    await self._save_tables(ocr_doc.id, result["table_data"])

                return OCRDetailResponse.model_validate(ocr_doc)

            except Exception as e:
                # Update status to failed
                ocr_doc.status = OCRStatus.FAILED
                ocr_doc.error_message = str(e)
                await self.db.commit()

                logger.error(f"OCR processing failed for document {ocr_doc.id}: {e}", exc_info=True)
                raise OCRProcessingError(f"OCR processing failed: {str(e)}")

        except Exception as e:
            logger.error(f"Failed to process OCR request: {e}", exc_info=True)
            raise

    async def _save_tables(self, document_id: str, tables: List[Dict[str, Any]]) -> None:
        """Save extracted tables to database"""
        try:
            for table in tables:
                ocr_table = OCRTable(
                    document_id=document_id,
                    table_index=table.get("table_index", 0),
                    rows=table.get("rows", 0),
                    columns=table.get("columns", 0),
                    data=table.get("data", []),
                    confidence_score=table.get("confidence_score"),
                    metadata=table
                )
                self.db.add(ocr_table)

            await self.db.commit()
            logger.info(f"Saved {len(tables)} tables for document {document_id}")

        except Exception as e:
            logger.error(f"Failed to save tables: {e}", exc_info=True)

    async def get_document(self, document_id: str, user_id: Optional[str] = None) -> OCRDetailResponse:
        """Get OCR document by ID"""
        query = select(OCRDocument).where(OCRDocument.id == document_id)

        if user_id:
            query = query.where(OCRDocument.user_id == user_id)

        result = await self.db.execute(query)
        document = result.scalar_one_or_none()

        if not document:
            raise OCRProcessingError("Document not found")

        return OCRDetailResponse.model_validate(document)

    async def list_documents(
        self,
        user_id: Optional[str] = None,
        status: Optional[OCRStatus] = None,
        page: int = 1,
        page_size: int = 10
    ) -> OCRListResponse:
        """List OCR documents with pagination"""
        query = select(OCRDocument)

        if user_id:
            query = query.where(OCRDocument.user_id == user_id)

        if status:
            query = query.where(OCRDocument.status == status)

        # Get total count
        count_result = await self.db.execute(
            select(OCRDocument).where(
                and_(
                    OCRDocument.user_id == user_id if user_id else True,
                    OCRDocument.status == status if status else True
                )
            )
        )
        total = len(count_result.all())

        # Apply pagination
        query = query.offset((page - 1) * page_size).limit(page_size)
        query = query.order_by(OCRDocument.created_at.desc())

        result = await self.db.execute(query)
        documents = result.scalars().all()

        return OCRListResponse(
            total=total,
            items=[OCRResponse.model_validate(doc) for doc in documents],
            page=page,
            page_size=page_size
        )

    async def delete_document(self, document_id: str, user_id: Optional[str] = None) -> bool:
        """Delete OCR document"""
        query = select(OCRDocument).where(OCRDocument.id == document_id)

        if user_id:
            query = query.where(OCRDocument.user_id == user_id)

        result = await self.db.execute(query)
        document = result.scalar_one_or_none()

        if not document:
            raise OCRProcessingError("Document not found")

        # Delete file from disk
        try:
            if os.path.exists(document.file_path):
                os.remove(document.file_path)
        except Exception as e:
            logger.warning(f"Failed to delete file {document.file_path}: {e}")

        # Delete from database
        await self.db.delete(document)
        await self.db.commit()

        logger.info(f"Deleted OCR document {document_id}")
        return True

    async def get_document_tables(self, document_id: str) -> List[Dict[str, Any]]:
        """Get all tables extracted from a document"""
        query = select(OCRTable).where(OCRTable.document_id == document_id)
        result = await self.db.execute(query)
        tables = result.scalars().all()

        return [table.dict() for table in tables]
