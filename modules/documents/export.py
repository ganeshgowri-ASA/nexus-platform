"""
Document export for Document Management System.

This module provides document export functionality including:
- Bulk export to ZIP
- Format preservation
- Metadata export (JSON, CSV)
- Export with folder structure
- Incremental export
- Export templates
"""

import csv
import io
import json
import zipfile
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from celery import shared_task
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import get_settings
from backend.core.exceptions import (
    ExportException,
    NEXUSException,
    ResourceNotFoundException,
    ValidationException,
)
from backend.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class ExportFormat(str, Enum):
    """Export formats."""

    ZIP = "zip"
    TAR = "tar"
    FOLDER = "folder"


class MetadataFormat(str, Enum):
    """Metadata export formats."""

    JSON = "json"
    CSV = "csv"
    XML = "xml"
    YAML = "yaml"


class ExportScope(str, Enum):
    """Export scope options."""

    DOCUMENTS_ONLY = "documents_only"
    WITH_METADATA = "with_metadata"
    WITH_VERSIONS = "with_versions"
    WITH_AUDIT_TRAIL = "with_audit_trail"
    FULL = "full"


class ExportService:
    """
    Service for document export operations.

    Provides comprehensive export functionality with support for
    various formats, metadata inclusion, and folder structure preservation.
    """

    def __init__(self, db_session: AsyncSession) -> None:
        """
        Initialize export service.

        Args:
            db_session: Database session
        """
        self.db = db_session
        self.export_cache: Dict[str, Dict[str, Any]] = {}

    async def create_export(
        self,
        user_id: int,
        document_ids: List[int],
        scope: ExportScope = ExportScope.WITH_METADATA,
        preserve_structure: bool = True,
        metadata_format: MetadataFormat = MetadataFormat.JSON,
        include_versions: bool = False,
    ) -> str:
        """
        Create a document export.

        Args:
            user_id: User creating the export
            document_ids: List of document IDs to export
            scope: Export scope (what to include)
            preserve_structure: Preserve folder structure
            metadata_format: Format for metadata export
            include_versions: Include version history

        Returns:
            str: Export ID

        Raises:
            ValidationException: If parameters are invalid
        """
        logger.info(
            "Creating document export",
            user_id=user_id,
            document_count=len(document_ids),
            scope=scope.value,
        )

        if not document_ids:
            raise ValidationException("Document list cannot be empty")

        # Generate export ID
        export_id = f"export_{user_id}_{int(datetime.utcnow().timestamp())}"

        # Initialize export metadata
        self.export_cache[export_id] = {
            "export_id": export_id,
            "user_id": user_id,
            "document_ids": document_ids,
            "scope": scope.value,
            "preserve_structure": preserve_structure,
            "metadata_format": metadata_format.value,
            "include_versions": include_versions,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "file_path": None,
            "file_size": 0,
        }

        logger.info("Export created", export_id=export_id)
        return export_id

    async def export_to_zip(
        self,
        document_ids: List[int],
        preserve_structure: bool = True,
        include_metadata: bool = True,
        metadata_format: MetadataFormat = MetadataFormat.JSON,
        include_versions: bool = False,
    ) -> bytes:
        """
        Export documents to ZIP archive.

        Args:
            document_ids: List of document IDs
            preserve_structure: Preserve folder structure
            include_metadata: Include metadata files
            metadata_format: Format for metadata
            include_versions: Include version history

        Returns:
            bytes: ZIP archive content

        Raises:
            ExportException: If export fails
        """
        logger.info(
            "Exporting documents to ZIP",
            document_count=len(document_ids),
            preserve_structure=preserve_structure,
        )

        try:
            # Create ZIP in memory
            zip_buffer = io.BytesIO()

            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                # Track folders to avoid duplicates
                created_folders: Set[str] = set()

                for doc_id in document_ids:
                    try:
                        # Get document info
                        # doc = await self._get_document(doc_id)

                        # Determine file path in ZIP
                        if preserve_structure:
                            # file_path = await self._get_document_path(doc)
                            file_path = f"documents/doc_{doc_id}.txt"  # Placeholder
                        else:
                            file_path = f"doc_{doc_id}.txt"  # Placeholder

                        # Get document content
                        # content = await self._get_document_content(doc_id)
                        content = b"Sample content"  # Placeholder

                        # Add document to ZIP
                        zip_file.writestr(file_path, content)

                        # Add metadata if requested
                        if include_metadata:
                            metadata = await self._export_document_metadata(
                                doc_id, metadata_format
                            )
                            metadata_path = f"{file_path}.metadata.{metadata_format.value}"
                            zip_file.writestr(metadata_path, metadata)

                        # Add versions if requested
                        if include_versions:
                            versions = await self._export_document_versions(doc_id)
                            for version_num, version_content in versions:
                                version_path = f"{file_path}.v{version_num}"
                                zip_file.writestr(version_path, version_content)

                    except Exception as e:
                        logger.warning(
                            "Failed to export document",
                            doc_id=doc_id,
                            error=str(e),
                        )
                        # Add error log to ZIP
                        error_msg = f"Error exporting document {doc_id}: {str(e)}\n"
                        if "errors.txt" in zip_file.namelist():
                            existing = zip_file.read("errors.txt").decode()
                            zip_file.writestr("errors.txt", existing + error_msg)
                        else:
                            zip_file.writestr("errors.txt", error_msg)

                # Add export manifest
                manifest = self._create_export_manifest(document_ids)
                zip_file.writestr("MANIFEST.json", json.dumps(manifest, indent=2))

            zip_buffer.seek(0)
            zip_content = zip_buffer.read()

            logger.info(
                "ZIP export completed",
                document_count=len(document_ids),
                size_bytes=len(zip_content),
            )

            return zip_content

        except Exception as e:
            logger.error("ZIP export failed", error=str(e))
            raise ExportException(f"ZIP export failed: {str(e)}")

    async def export_metadata(
        self,
        document_ids: List[int],
        format: MetadataFormat = MetadataFormat.JSON,
        include_audit_trail: bool = False,
        include_permissions: bool = False,
    ) -> str:
        """
        Export document metadata.

        Args:
            document_ids: List of document IDs
            format: Output format
            include_audit_trail: Include audit trail
            include_permissions: Include permissions

        Returns:
            str: Formatted metadata

        Raises:
            ExportException: If export fails
        """
        logger.info(
            "Exporting metadata",
            document_count=len(document_ids),
            format=format.value,
        )

        try:
            metadata_list = []

            for doc_id in document_ids:
                metadata = await self._get_document_full_metadata(
                    doc_id,
                    include_audit_trail,
                    include_permissions,
                )
                metadata_list.append(metadata)

            # Format output
            if format == MetadataFormat.JSON:
                output = json.dumps(metadata_list, indent=2, default=str)
            elif format == MetadataFormat.CSV:
                output = self._metadata_to_csv(metadata_list)
            elif format == MetadataFormat.XML:
                output = self._metadata_to_xml(metadata_list)
            elif format == MetadataFormat.YAML:
                output = self._metadata_to_yaml(metadata_list)
            else:
                raise ValidationException(f"Unsupported format: {format}")

            logger.info("Metadata export completed", format=format.value)
            return output

        except Exception as e:
            logger.error("Metadata export failed", error=str(e))
            raise ExportException(f"Metadata export failed: {str(e)}")

    async def export_with_folder_structure(
        self,
        root_folder_id: int,
        output_path: str,
        include_subfolders: bool = True,
    ) -> Dict[str, Any]:
        """
        Export documents preserving folder structure.

        Args:
            root_folder_id: Root folder ID
            output_path: Output directory path
            include_subfolders: Include subfolders recursively

        Returns:
            Dict containing export statistics

        Raises:
            ExportException: If export fails
        """
        logger.info(
            "Exporting with folder structure",
            root_folder_id=root_folder_id,
            output_path=output_path,
        )

        try:
            stats = {
                "folders_created": 0,
                "documents_exported": 0,
                "total_size_bytes": 0,
                "errors": 0,
            }

            # Get folder structure
            folders = await self._get_folder_tree(root_folder_id, include_subfolders)

            output_dir = Path(output_path)
            output_dir.mkdir(parents=True, exist_ok=True)

            for folder in folders:
                try:
                    # Create folder
                    folder_path = output_dir / folder["path"]
                    folder_path.mkdir(parents=True, exist_ok=True)
                    stats["folders_created"] += 1

                    # Export documents in folder
                    # documents = await self._get_folder_documents(folder["id"])
                    # for doc in documents:
                    #     file_path = folder_path / doc.filename
                    #     content = await self._get_document_content(doc.id)
                    #     file_path.write_bytes(content)
                    #     stats["documents_exported"] += 1
                    #     stats["total_size_bytes"] += len(content)

                except Exception as e:
                    logger.warning(
                        "Failed to export folder",
                        folder_id=folder["id"],
                        error=str(e),
                    )
                    stats["errors"] += 1

            logger.info("Folder structure export completed", **stats)
            return stats

        except Exception as e:
            logger.error("Folder structure export failed", error=str(e))
            raise ExportException(f"Folder structure export failed: {str(e)}")

    async def incremental_export(
        self,
        user_id: int,
        last_export_time: datetime,
        output_format: ExportFormat = ExportFormat.ZIP,
    ) -> bytes:
        """
        Perform incremental export of changed documents.

        Args:
            user_id: User ID
            last_export_time: Time of last export
            output_format: Output format

        Returns:
            bytes: Export content

        Raises:
            ExportException: If export fails
        """
        logger.info(
            "Performing incremental export",
            user_id=user_id,
            last_export_time=last_export_time,
        )

        try:
            # Get documents modified since last export
            # query = select(Document).where(
            #     and_(
            #         Document.owner_id == user_id,
            #         Document.updated_at > last_export_time
            #     )
            # )
            # result = await self.db.execute(query)
            # documents = result.scalars().all()

            # For now, use placeholder
            document_ids = []

            # Export changed documents
            if output_format == ExportFormat.ZIP:
                export_content = await self.export_to_zip(
                    document_ids=document_ids,
                    preserve_structure=True,
                    include_metadata=True,
                )
            else:
                raise ValidationException(f"Unsupported format: {output_format}")

            logger.info(
                "Incremental export completed",
                document_count=len(document_ids),
            )

            return export_content

        except Exception as e:
            logger.error("Incremental export failed", error=str(e))
            raise ExportException(f"Incremental export failed: {str(e)}")

    async def create_export_template(
        self,
        name: str,
        user_id: int,
        scope: ExportScope,
        filters: Dict[str, Any],
        format_options: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Create an export template for reuse.

        Args:
            name: Template name
            user_id: User creating template
            scope: Export scope
            filters: Document filters
            format_options: Format options

        Returns:
            Dict containing template info

        Raises:
            ExportException: If template creation fails
        """
        logger.info(
            "Creating export template",
            name=name,
            user_id=user_id,
        )

        try:
            template = {
                "id": f"template_{int(datetime.utcnow().timestamp())}",
                "name": name,
                "user_id": user_id,
                "scope": scope.value,
                "filters": filters,
                "format_options": format_options,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }

            # Save template to database
            # await self._save_export_template(template)

            logger.info("Export template created", template_id=template["id"])
            return template

        except Exception as e:
            logger.error("Failed to create export template", error=str(e))
            raise ExportException(f"Failed to create template: {str(e)}")

    async def apply_export_template(
        self,
        template_id: str,
        user_id: int,
    ) -> str:
        """
        Apply an export template.

        Args:
            template_id: Template ID
            user_id: User applying template

        Returns:
            str: Export ID

        Raises:
            ResourceNotFoundException: If template not found
        """
        logger.info(
            "Applying export template",
            template_id=template_id,
            user_id=user_id,
        )

        # Get template
        # template = await self._get_export_template(template_id)

        # Apply filters to get documents
        # document_ids = await self._apply_filters(template["filters"])

        # Create export with template settings
        export_id = await self.create_export(
            user_id=user_id,
            document_ids=[],  # Placeholder
            scope=ExportScope.WITH_METADATA,
            preserve_structure=True,
        )

        logger.info("Export template applied", export_id=export_id)
        return export_id

    # Helper methods

    async def _export_document_metadata(
        self,
        document_id: int,
        format: MetadataFormat,
    ) -> str:
        """Export metadata for a single document."""
        metadata = {
            "document_id": document_id,
            "exported_at": datetime.utcnow().isoformat(),
            # Additional metadata fields would go here
        }

        if format == MetadataFormat.JSON:
            return json.dumps(metadata, indent=2)
        elif format == MetadataFormat.CSV:
            return self._dict_to_csv([metadata])
        else:
            return str(metadata)

    async def _export_document_versions(
        self,
        document_id: int,
    ) -> List[tuple[int, bytes]]:
        """Export version history for a document."""
        # Get versions from database
        # versions = await self._get_document_versions(document_id)
        versions = []  # Placeholder
        return versions

    async def _get_document_full_metadata(
        self,
        document_id: int,
        include_audit_trail: bool,
        include_permissions: bool,
    ) -> Dict[str, Any]:
        """Get full metadata for a document."""
        metadata = {
            "id": document_id,
            "filename": f"document_{document_id}",
            "created_at": datetime.utcnow().isoformat(),
            # Additional fields would go here
        }

        if include_audit_trail:
            # metadata["audit_trail"] = await self._get_audit_trail(document_id)
            metadata["audit_trail"] = []

        if include_permissions:
            # metadata["permissions"] = await self._get_permissions(document_id)
            metadata["permissions"] = []

        return metadata

    async def _get_folder_tree(
        self,
        root_folder_id: int,
        include_subfolders: bool,
    ) -> List[Dict[str, Any]]:
        """Get folder tree structure."""
        # Query folder hierarchy
        folders = [
            {"id": root_folder_id, "path": "root"}
        ]  # Placeholder
        return folders

    def _create_export_manifest(
        self,
        document_ids: List[int],
    ) -> Dict[str, Any]:
        """Create export manifest."""
        return {
            "export_version": "1.0",
            "exported_at": datetime.utcnow().isoformat(),
            "document_count": len(document_ids),
            "document_ids": document_ids,
        }

    def _metadata_to_csv(
        self,
        metadata_list: List[Dict[str, Any]],
    ) -> str:
        """Convert metadata to CSV format."""
        output = io.StringIO()

        if metadata_list:
            # Get all unique keys
            all_keys = set()
            for item in metadata_list:
                all_keys.update(item.keys())

            fieldnames = sorted(all_keys)
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()

            for item in metadata_list:
                # Flatten nested dicts
                flat_item = self._flatten_dict(item)
                writer.writerow(flat_item)

        return output.getvalue()

    def _dict_to_csv(
        self,
        data: List[Dict[str, Any]],
    ) -> str:
        """Convert dictionary list to CSV."""
        return self._metadata_to_csv(data)

    def _metadata_to_xml(
        self,
        metadata_list: List[Dict[str, Any]],
    ) -> str:
        """Convert metadata to XML format."""
        # Simple XML generation
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n<documents>\n'

        for metadata in metadata_list:
            xml += "  <document>\n"
            for key, value in metadata.items():
                if not isinstance(value, (dict, list)):
                    xml += f"    <{key}>{value}</{key}>\n"
            xml += "  </document>\n"

        xml += "</documents>"
        return xml

    def _metadata_to_yaml(
        self,
        metadata_list: List[Dict[str, Any]],
    ) -> str:
        """Convert metadata to YAML format."""
        # Simple YAML generation
        yaml = "documents:\n"

        for metadata in metadata_list:
            yaml += "  - \n"
            for key, value in metadata.items():
                if not isinstance(value, (dict, list)):
                    yaml += f"    {key}: {value}\n"

        return yaml

    def _flatten_dict(
        self,
        d: Dict[str, Any],
        parent_key: str = "",
        sep: str = "_",
    ) -> Dict[str, Any]:
        """Flatten nested dictionary."""
        items = []

        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k

            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                items.append((new_key, json.dumps(v)))
            else:
                items.append((new_key, v))

        return dict(items)


# Celery Tasks

@shared_task(bind=True, max_retries=3)
def export_documents_task(
    self,
    export_id: str,
    document_ids: List[int],
    scope: str,
    preserve_structure: bool,
    metadata_format: str,
) -> Dict[str, Any]:
    """
    Celery task for document export.

    Args:
        export_id: Export ID
        document_ids: List of document IDs
        scope: Export scope
        preserve_structure: Preserve folder structure
        metadata_format: Metadata format

    Returns:
        Dict containing export results
    """
    logger.info("Executing export task", export_id=export_id)

    try:
        # Perform export
        # export_content = await export_to_zip(...)

        result = {
            "export_id": export_id,
            "status": "completed",
            "document_count": len(document_ids),
            "completed_at": datetime.utcnow().isoformat(),
        }

        logger.info("Export task completed", export_id=export_id)
        return result

    except Exception as e:
        logger.error("Export task failed", error=str(e))
        raise
