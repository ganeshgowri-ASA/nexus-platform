"""
Document schemas for API request/response validation.

This module defines Pydantic schemas for document-related API operations.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from modules.documents.document_types import (
    AccessLevel,
    DocumentStatus,
    ShareType,
    WorkflowStatus,
    BulkOperationType,
    BulkOperationStatus,
)


# Re-export from document_types for convenience
__all__ = [
    "DocumentCreate",
    "DocumentUpdate",
    "DocumentResponse",
    "DocumentDetailResponse",
    "FolderCreate",
    "FolderUpdate",
    "FolderResponse",
    "VersionResponse",
    "MetadataEntry",
    "TagCreate",
    "TagResponse",
    "PermissionCreate",
    "PermissionResponse",
    "ShareLinkCreate",
    "ShareLinkResponse",
    "CommentCreate",
    "CommentUpdate",
    "CommentResponse",
    "WorkflowCreate",
    "WorkflowResponse",
    "SearchQuery",
    "SearchResponse",
    "BulkOperationCreate",
    "BulkOperationResponse",
    "DocumentStatistics",
    "StorageStatistics",
]
