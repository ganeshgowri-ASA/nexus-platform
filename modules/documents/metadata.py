"""
Metadata management system for documents.

This module provides comprehensive metadata handling including:
- Automatic metadata extraction from files
- Custom metadata fields
- Metadata search and filtering
- Bulk metadata operations
- Schema validation
- Metadata indexing
"""

import io
import mimetypes
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from PIL import Image
from PyPDF2 import PdfReader
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.core.config import get_settings
from backend.core.exceptions import (
    DocumentNotFoundException,
    NEXUSException,
    ValidationException,
)
from backend.core.logging import get_logger
from backend.models.document import Document, DocumentMetadata

logger = get_logger(__name__)
settings = get_settings()


class MetadataException(NEXUSException):
    """Exception raised for metadata-related errors."""

    def __init__(self, message: str = "Metadata operation failed", **kwargs: Any) -> None:
        super().__init__(message, status_code=500, **kwargs)


class MetadataValidationException(ValidationException):
    """Exception raised for metadata validation errors."""

    pass


class MetadataService:
    """
    Service for managing document metadata.

    Provides comprehensive metadata management including extraction,
    validation, search, and bulk operations.
    """

    # Standard metadata fields
    SYSTEM_METADATA_FIELDS = {
        "file_name",
        "file_size",
        "mime_type",
        "created_at",
        "modified_at",
        "author",
        "title",
        "description",
        "language",
        "page_count",
        "word_count",
        "character_count",
        "image_width",
        "image_height",
        "image_format",
        "pdf_version",
        "creation_date",
        "modification_date",
    }

    # Metadata value types
    VALUE_TYPES = {
        "string",
        "number",
        "integer",
        "boolean",
        "date",
        "datetime",
        "json",
        "list",
    }

    def __init__(self, db_session: AsyncSession) -> None:
        """
        Initialize metadata service.

        Args:
            db_session: Database session
        """
        self.db = db_session

    async def add_metadata(
        self,
        document_id: int,
        key: str,
        value: Any,
        value_type: str = "string",
        is_system: bool = False,
    ) -> DocumentMetadata:
        """
        Add metadata to a document.

        Args:
            document_id: Document ID
            key: Metadata key
            value: Metadata value
            value_type: Type of value
            is_system: Whether this is system metadata

        Returns:
            DocumentMetadata: Created metadata entry

        Raises:
            DocumentNotFoundException: If document not found
            MetadataValidationException: If metadata is invalid
        """
        logger.info(
            "Adding metadata",
            document_id=document_id,
            key=key,
            value_type=value_type,
        )

        # Verify document exists
        result = await self.db.execute(select(Document).where(Document.id == document_id))
        if not result.scalar_one_or_none():
            raise DocumentNotFoundException(document_id)

        # Validate value type
        if value_type not in self.VALUE_TYPES:
            raise MetadataValidationException(
                f"Invalid value type: {value_type}",
                errors={"value_type": f"Must be one of: {', '.join(self.VALUE_TYPES)}"},
            )

        # Convert value to string for storage
        value_str = self._serialize_value(value, value_type)

        # Check if metadata already exists
        result = await self.db.execute(
            select(DocumentMetadata).where(
                and_(
                    DocumentMetadata.document_id == document_id,
                    DocumentMetadata.key == key,
                )
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing metadata
            existing.value = value_str
            existing.value_type = value_type
            existing.is_system = is_system
            existing.updated_at = datetime.utcnow()
            metadata = existing
        else:
            # Create new metadata
            metadata = DocumentMetadata(
                document_id=document_id,
                key=key,
                value=value_str,
                value_type=value_type,
                is_system=is_system,
            )
            self.db.add(metadata)

        await self.db.commit()
        await self.db.refresh(metadata)

        logger.info("Metadata added", metadata_id=metadata.id, key=key)

        return metadata

    async def get_metadata(
        self,
        document_id: int,
        key: str,
    ) -> Optional[Any]:
        """
        Get a specific metadata value.

        Args:
            document_id: Document ID
            key: Metadata key

        Returns:
            Metadata value (deserialized) or None if not found

        Raises:
            DocumentNotFoundException: If document not found
        """
        result = await self.db.execute(
            select(DocumentMetadata).where(
                and_(
                    DocumentMetadata.document_id == document_id,
                    DocumentMetadata.key == key,
                )
            )
        )
        metadata = result.scalar_one_or_none()

        if not metadata:
            return None

        return self._deserialize_value(metadata.value, metadata.value_type)

    async def get_all_metadata(
        self,
        document_id: int,
        include_system: bool = True,
    ) -> Dict[str, Any]:
        """
        Get all metadata for a document.

        Args:
            document_id: Document ID
            include_system: Whether to include system metadata

        Returns:
            Dict mapping metadata keys to values

        Raises:
            DocumentNotFoundException: If document not found
        """
        # Verify document exists
        result = await self.db.execute(select(Document).where(Document.id == document_id))
        if not result.scalar_one_or_none():
            raise DocumentNotFoundException(document_id)

        # Get metadata
        query = select(DocumentMetadata).where(DocumentMetadata.document_id == document_id)

        if not include_system:
            query = query.where(DocumentMetadata.is_system == False)

        result = await self.db.execute(query)
        metadata_entries = result.scalars().all()

        # Convert to dict
        metadata_dict = {}
        for entry in metadata_entries:
            metadata_dict[entry.key] = {
                "value": self._deserialize_value(entry.value, entry.value_type),
                "type": entry.value_type,
                "is_system": entry.is_system,
                "created_at": entry.created_at.isoformat() if entry.created_at else None,
                "updated_at": entry.updated_at.isoformat() if entry.updated_at else None,
            }

        logger.info(
            "Retrieved all metadata",
            document_id=document_id,
            count=len(metadata_dict),
        )

        return metadata_dict

    async def update_metadata(
        self,
        document_id: int,
        key: str,
        value: Any,
        value_type: Optional[str] = None,
    ) -> DocumentMetadata:
        """
        Update existing metadata.

        Args:
            document_id: Document ID
            key: Metadata key
            value: New value
            value_type: New value type (optional)

        Returns:
            DocumentMetadata: Updated metadata entry

        Raises:
            DocumentNotFoundException: If document not found
            MetadataException: If metadata key doesn't exist
        """
        logger.info("Updating metadata", document_id=document_id, key=key)

        result = await self.db.execute(
            select(DocumentMetadata).where(
                and_(
                    DocumentMetadata.document_id == document_id,
                    DocumentMetadata.key == key,
                )
            )
        )
        metadata = result.scalar_one_or_none()

        if not metadata:
            raise MetadataException(
                f"Metadata key '{key}' not found for document {document_id}"
            )

        # Update value type if provided
        if value_type:
            if value_type not in self.VALUE_TYPES:
                raise MetadataValidationException(
                    f"Invalid value type: {value_type}",
                    errors={"value_type": f"Must be one of: {', '.join(self.VALUE_TYPES)}"},
                )
            metadata.value_type = value_type
        else:
            value_type = metadata.value_type

        # Update value
        metadata.value = self._serialize_value(value, value_type)
        metadata.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(metadata)

        logger.info("Metadata updated", metadata_id=metadata.id, key=key)

        return metadata

    async def delete_metadata(
        self,
        document_id: int,
        key: str,
    ) -> None:
        """
        Delete metadata entry.

        Args:
            document_id: Document ID
            key: Metadata key

        Raises:
            DocumentNotFoundException: If document not found
            MetadataException: If metadata key doesn't exist
        """
        logger.info("Deleting metadata", document_id=document_id, key=key)

        result = await self.db.execute(
            select(DocumentMetadata).where(
                and_(
                    DocumentMetadata.document_id == document_id,
                    DocumentMetadata.key == key,
                )
            )
        )
        metadata = result.scalar_one_or_none()

        if not metadata:
            raise MetadataException(
                f"Metadata key '{key}' not found for document {document_id}"
            )

        await self.db.delete(metadata)
        await self.db.commit()

        logger.info("Metadata deleted", key=key)

    async def bulk_add_metadata(
        self,
        document_id: int,
        metadata_dict: Dict[str, Any],
        value_types: Optional[Dict[str, str]] = None,
    ) -> List[DocumentMetadata]:
        """
        Add multiple metadata entries at once.

        Args:
            document_id: Document ID
            metadata_dict: Dict mapping keys to values
            value_types: Optional dict mapping keys to value types

        Returns:
            List[DocumentMetadata]: Created metadata entries

        Raises:
            DocumentNotFoundException: If document not found
        """
        logger.info(
            "Bulk adding metadata",
            document_id=document_id,
            count=len(metadata_dict),
        )

        value_types = value_types or {}
        metadata_entries = []

        for key, value in metadata_dict.items():
            value_type = value_types.get(key, self._infer_value_type(value))
            metadata = await self.add_metadata(
                document_id=document_id,
                key=key,
                value=value,
                value_type=value_type,
            )
            metadata_entries.append(metadata)

        logger.info("Bulk metadata added", count=len(metadata_entries))

        return metadata_entries

    async def search_by_metadata(
        self,
        filters: Dict[str, Any],
        operator: str = "AND",
        limit: int = 100,
        offset: int = 0,
    ) -> List[Document]:
        """
        Search documents by metadata.

        Args:
            filters: Dict mapping metadata keys to filter values
            operator: Boolean operator for multiple filters ('AND' or 'OR')
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List[Document]: Matching documents

        Raises:
            ValidationException: If operator is invalid
        """
        logger.info(
            "Searching by metadata",
            filters=filters,
            operator=operator,
            limit=limit,
        )

        if operator not in ["AND", "OR"]:
            raise ValidationException(
                "Invalid operator",
                errors={"operator": "Must be 'AND' or 'OR'"},
            )

        # Build subqueries for each filter
        conditions = []
        for key, value in filters.items():
            value_str = str(value)
            condition = and_(
                DocumentMetadata.key == key,
                DocumentMetadata.value.contains(value_str),
            )
            conditions.append(condition)

        # Combine conditions
        if operator == "AND":
            # For AND, we need all metadata entries to match
            # This is more complex - we need to join multiple times
            # Simplified: get all matching documents and filter in Python
            query = select(DocumentMetadata).where(or_(*conditions))
        else:
            # For OR, any match is sufficient
            query = select(DocumentMetadata).where(or_(*conditions))

        query = query.options(selectinload(DocumentMetadata.document))

        result = await self.db.execute(query)
        metadata_entries = result.scalars().all()

        # Get unique documents
        documents = {}
        for entry in metadata_entries:
            if entry.document:
                documents[entry.document.id] = entry.document

        # For AND operator, filter documents that have all required metadata
        if operator == "AND":
            filtered_docs = []
            for doc in documents.values():
                # Check if document has all required metadata
                doc_metadata = await self.get_all_metadata(doc.id, include_system=False)
                if all(key in doc_metadata for key in filters.keys()):
                    # Check if values match
                    if all(
                        str(filters[key]) in str(doc_metadata[key]["value"])
                        for key in filters.keys()
                    ):
                        filtered_docs.append(doc)
            documents_list = filtered_docs
        else:
            documents_list = list(documents.values())

        # Apply pagination
        documents_list = documents_list[offset : offset + limit]

        logger.info("Metadata search completed", count=len(documents_list))

        return documents_list

    async def extract_file_metadata(
        self,
        file_path: str,
        file_content: Optional[bytes] = None,
    ) -> Dict[str, Any]:
        """
        Extract metadata from a file.

        Args:
            file_path: Path to file
            file_content: File content bytes (optional, will read from path if not provided)

        Returns:
            Dict containing extracted metadata

        Raises:
            MetadataException: If extraction fails
        """
        logger.info("Extracting file metadata", file_path=file_path)

        path = Path(file_path)
        metadata = {}

        try:
            # Basic file metadata
            if path.exists():
                stats = path.stat()
                metadata["file_size"] = stats.st_size
                metadata["modified_at"] = datetime.fromtimestamp(stats.st_mtime).isoformat()

            # Get content if not provided
            if file_content is None and path.exists():
                file_content = path.read_bytes()

            # MIME type
            mime_type, _ = mimetypes.guess_type(str(path))
            metadata["mime_type"] = mime_type or "application/octet-stream"

            # Extract based on file type
            if mime_type:
                if mime_type.startswith("image/"):
                    image_metadata = self._extract_image_metadata(file_content)
                    metadata.update(image_metadata)
                elif mime_type == "application/pdf":
                    pdf_metadata = self._extract_pdf_metadata(file_content)
                    metadata.update(pdf_metadata)
                elif mime_type.startswith("text/"):
                    text_metadata = self._extract_text_metadata(file_content)
                    metadata.update(text_metadata)

            logger.info(
                "File metadata extracted",
                file_path=file_path,
                fields_count=len(metadata),
            )

            return metadata

        except Exception as e:
            logger.exception("Failed to extract metadata", error=str(e))
            raise MetadataException(f"Failed to extract metadata: {str(e)}")

    def _extract_image_metadata(self, content: bytes) -> Dict[str, Any]:
        """
        Extract metadata from image files.

        Args:
            content: Image file content

        Returns:
            Dict containing image metadata
        """
        metadata = {}

        try:
            image = Image.open(io.BytesIO(content))
            metadata["image_width"] = image.width
            metadata["image_height"] = image.height
            metadata["image_format"] = image.format
            metadata["image_mode"] = image.mode

            # Extract EXIF data if available
            if hasattr(image, "_getexif") and image._getexif():
                exif = image._getexif()
                if exif:
                    # Common EXIF tags
                    if 306 in exif:  # DateTime
                        metadata["creation_date"] = str(exif[306])
                    if 271 in exif:  # Make
                        metadata["camera_make"] = str(exif[271])
                    if 272 in exif:  # Model
                        metadata["camera_model"] = str(exif[272])

        except Exception as e:
            logger.warning("Failed to extract image metadata", error=str(e))

        return metadata

    def _extract_pdf_metadata(self, content: bytes) -> Dict[str, Any]:
        """
        Extract metadata from PDF files.

        Args:
            content: PDF file content

        Returns:
            Dict containing PDF metadata
        """
        metadata = {}

        try:
            pdf = PdfReader(io.BytesIO(content))
            metadata["page_count"] = len(pdf.pages)

            # Extract PDF info
            if pdf.metadata:
                if pdf.metadata.author:
                    metadata["author"] = pdf.metadata.author
                if pdf.metadata.title:
                    metadata["title"] = pdf.metadata.title
                if pdf.metadata.subject:
                    metadata["subject"] = pdf.metadata.subject
                if pdf.metadata.creator:
                    metadata["creator"] = pdf.metadata.creator
                if pdf.metadata.producer:
                    metadata["producer"] = pdf.metadata.producer
                if pdf.metadata.creation_date:
                    metadata["creation_date"] = str(pdf.metadata.creation_date)
                if pdf.metadata.modification_date:
                    metadata["modification_date"] = str(pdf.metadata.modification_date)

        except Exception as e:
            logger.warning("Failed to extract PDF metadata", error=str(e))

        return metadata

    def _extract_text_metadata(self, content: bytes) -> Dict[str, Any]:
        """
        Extract metadata from text files.

        Args:
            content: Text file content

        Returns:
            Dict containing text metadata
        """
        metadata = {}

        try:
            text = content.decode("utf-8")
            metadata["character_count"] = len(text)
            metadata["word_count"] = len(text.split())
            metadata["line_count"] = len(text.splitlines())

            # Detect language (simplified - would use langdetect in production)
            metadata["language"] = "unknown"

        except Exception as e:
            logger.warning("Failed to extract text metadata", error=str(e))

        return metadata

    def _serialize_value(self, value: Any, value_type: str) -> str:
        """
        Serialize a value for storage.

        Args:
            value: Value to serialize
            value_type: Type of value

        Returns:
            str: Serialized value
        """
        import json

        if value_type in ["string", "number", "integer", "boolean"]:
            return str(value)
        elif value_type in ["date", "datetime"]:
            if isinstance(value, datetime):
                return value.isoformat()
            return str(value)
        elif value_type in ["json", "list"]:
            return json.dumps(value)
        else:
            return str(value)

    def _deserialize_value(self, value_str: Optional[str], value_type: str) -> Any:
        """
        Deserialize a stored value.

        Args:
            value_str: Serialized value
            value_type: Type of value

        Returns:
            Deserialized value
        """
        import json

        if value_str is None:
            return None

        try:
            if value_type == "string":
                return value_str
            elif value_type == "number":
                return float(value_str)
            elif value_type == "integer":
                return int(value_str)
            elif value_type == "boolean":
                return value_str.lower() in ["true", "1", "yes"]
            elif value_type in ["date", "datetime"]:
                return datetime.fromisoformat(value_str)
            elif value_type in ["json", "list"]:
                return json.loads(value_str)
            else:
                return value_str
        except Exception as e:
            logger.warning(
                "Failed to deserialize value",
                value_type=value_type,
                error=str(e),
            )
            return value_str

    def _infer_value_type(self, value: Any) -> str:
        """
        Infer the value type from a Python value.

        Args:
            value: Value to infer type from

        Returns:
            str: Inferred value type
        """
        if isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "number"
        elif isinstance(value, datetime):
            return "datetime"
        elif isinstance(value, (list, tuple)):
            return "list"
        elif isinstance(value, dict):
            return "json"
        else:
            return "string"


class MetadataSchemaService:
    """
    Service for managing metadata schemas and validation.

    Provides schema definition and validation for structured metadata.
    """

    def __init__(self, db_session: AsyncSession, metadata_service: MetadataService) -> None:
        """
        Initialize metadata schema service.

        Args:
            db_session: Database session
            metadata_service: Metadata service instance
        """
        self.db = db_session
        self.metadata_service = metadata_service

    async def validate_metadata(
        self,
        metadata: Dict[str, Any],
        schema: Dict[str, Any],
    ) -> Tuple[bool, List[str]]:
        """
        Validate metadata against a schema.

        Args:
            metadata: Metadata to validate
            schema: Schema definition

        Returns:
            Tuple of (is_valid, list of errors)
        """
        errors = []

        # Check required fields
        required_fields = schema.get("required", [])
        for field in required_fields:
            if field not in metadata:
                errors.append(f"Required field '{field}' is missing")

        # Check field types
        field_types = schema.get("properties", {})
        for field, value in metadata.items():
            if field in field_types:
                expected_type = field_types[field].get("type")
                if expected_type:
                    actual_type = self.metadata_service._infer_value_type(value)
                    if actual_type != expected_type:
                        errors.append(
                            f"Field '{field}' has type '{actual_type}', expected '{expected_type}'"
                        )

        is_valid = len(errors) == 0

        logger.info(
            "Metadata validation completed",
            is_valid=is_valid,
            error_count=len(errors),
        )

        return is_valid, errors

    def create_schema(
        self,
        name: str,
        properties: Dict[str, Dict[str, Any]],
        required: Optional[List[str]] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a metadata schema definition.

        Args:
            name: Schema name
            properties: Field definitions
            required: List of required fields
            description: Schema description

        Returns:
            Dict: Schema definition
        """
        schema = {
            "name": name,
            "description": description or "",
            "properties": properties,
            "required": required or [],
            "created_at": datetime.utcnow().isoformat(),
        }

        logger.info("Metadata schema created", name=name)

        return schema
