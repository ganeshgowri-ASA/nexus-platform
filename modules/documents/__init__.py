"""
Document Management System (DMS) Module for NEXUS Platform.

This module provides comprehensive document management capabilities including:
- File storage with multi-backend support (local, S3, Azure, GCS)
- Version control with diff tracking and rollback
- Advanced search with full-text and semantic capabilities
- Real-time collaboration features
- Granular permissions and access control
- Document workflows and approvals
- AI-powered classification and content intelligence
- OCR and format conversion
- Compliance and retention management
- Audit logging and forensics
"""

__version__ = "0.1.0"
__author__ = "NEXUS Team"

# Export main classes and functions
from modules.documents.document_types import (
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
    FolderCreate,
    FolderResponse,
    VersionResponse,
    MetadataEntry,
    TagResponse,
    PermissionResponse,
)

# Export services
from modules.documents.versioning import (
    VersionControlService,
    VersionBranchingService,
    VersioningException,
)
from modules.documents.permissions import (
    PermissionService,
    ShareLinkService,
    PermissionDeniedException,
)
from modules.documents.audit import (
    AuditService,
    AuditAction,
    AuditException,
)
from modules.documents.ai_assistant import (
    DocumentAIAssistant,
    BatchAIProcessor,
    AIAssistantException,
)
from modules.documents.metadata import (
    MetadataService,
    MetadataSchemaService,
    MetadataException,
)
from modules.documents.integration import (
    EmailIntegrationService,
    ScannerIntegrationService,
    CloudStorageSyncService,
    DesktopSyncService,
    WebhookService,
    MobileSyncService,
    IntegrationType,
)
from modules.documents.bulk_operations import (
    BulkOperationService,
    BulkOperationType,
    BulkOperationStatus,
)
from modules.documents.reports import (
    ReportService,
    ReportType,
    ReportFormat,
    ReportPeriod,
)
from modules.documents.export import (
    ExportService,
    ExportFormat,
    MetadataFormat,
    ExportScope,
)

__all__ = [
    # Types
    "DocumentCreate",
    "DocumentUpdate",
    "DocumentResponse",
    "FolderCreate",
    "FolderResponse",
    "VersionResponse",
    "MetadataEntry",
    "TagResponse",
    "PermissionResponse",
    # Versioning
    "VersionControlService",
    "VersionBranchingService",
    "VersioningException",
    # Permissions
    "PermissionService",
    "ShareLinkService",
    "PermissionDeniedException",
    # Audit
    "AuditService",
    "AuditAction",
    "AuditException",
    # AI Assistant
    "DocumentAIAssistant",
    "BatchAIProcessor",
    "AIAssistantException",
    # Metadata
    "MetadataService",
    "MetadataSchemaService",
    "MetadataException",
    # Integration
    "EmailIntegrationService",
    "ScannerIntegrationService",
    "CloudStorageSyncService",
    "DesktopSyncService",
    "WebhookService",
    "MobileSyncService",
    "IntegrationType",
    # Bulk Operations
    "BulkOperationService",
    "BulkOperationType",
    "BulkOperationStatus",
    # Reports
    "ReportService",
    "ReportType",
    "ReportFormat",
    "ReportPeriod",
    # Export
    "ExportService",
    "ExportFormat",
    "MetadataFormat",
    "ExportScope",
]
