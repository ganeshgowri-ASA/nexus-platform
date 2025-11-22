"""
Document management API endpoints.

This module provides FastAPI routes for all document management operations.
"""

from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from backend.core.dependencies import get_current_user
from backend.core.exceptions import DocumentNotFoundException, PermissionDeniedException
from backend.core.logging import get_logger
from backend.database import get_db
from modules.documents.document_types import (
    CommentCreate,
    CommentResponse,
    DocumentCreate,
    DocumentDetailResponse,
    DocumentResponse,
    DocumentStatistics,
    FolderCreate,
    FolderResponse,
    MetadataEntry,
    PermissionCreate,
    PermissionResponse,
    SearchQuery,
    SearchResponse,
    ShareLinkCreate,
    ShareLinkResponse,
    TagCreate,
    TagResponse,
    VersionResponse,
    WorkflowCreate,
    WorkflowResponse,
)
from modules.documents.storage import StorageManager
from modules.documents.permissions import PermissionService
from modules.documents.audit import AuditService
from modules.documents.search import DocumentSearchService
from modules.documents.ai_assistant import DocumentAIAssistant

logger = get_logger(__name__)
router = APIRouter()


# Document CRUD Operations


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = None,
    description: Optional[str] = None,
    folder_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> DocumentResponse:
    """
    Upload a new document.

    Args:
        file: File to upload
        title: Document title (defaults to filename)
        description: Document description
        folder_id: Parent folder ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        DocumentResponse: Created document
    """
    try:
        from backend.models.document import Document

        # Initialize storage manager
        storage = StorageManager()

        # Save file to storage
        file_path, file_hash, file_size = await storage.save_file(file)

        # Create document record
        document = Document(
            title=title or file.filename,
            description=description,
            file_name=file.filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=file.content_type,
            file_hash=file_hash,
            owner_id=current_user.id,
            folder_id=folder_id,
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        # Log action
        audit = AuditService(db)
        await audit.log_document_access(
            document.id, current_user.id, "created", {"file_name": file.filename}
        )

        logger.info(
            "document_uploaded",
            document_id=document.id,
            user_id=current_user.id,
            file_name=file.filename,
        )

        return DocumentResponse.model_validate(document)

    except Exception as e:
        logger.error("document_upload_failed", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}",
        )


@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    folder_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> List[DocumentResponse]:
    """
    List documents accessible by the current user.

    Args:
        folder_id: Filter by folder
        status_filter: Filter by status
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        current_user: Current authenticated user

    Returns:
        List[DocumentResponse]: List of documents
    """
    from backend.models.document import Document, DocumentStatus

    query = db.query(Document)

    # Apply filters
    if folder_id is not None:
        query = query.filter(Document.folder_id == folder_id)

    if status_filter:
        query = query.filter(Document.status == status_filter)

    # Filter by ownership or permissions
    query = query.filter(
        (Document.owner_id == current_user.id) | (Document.is_public == True)
    )

    # Apply pagination
    documents = query.offset(skip).limit(limit).all()

    return [DocumentResponse.model_validate(doc) for doc in documents]


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> DocumentDetailResponse:
    """
    Get document details.

    Args:
        document_id: Document ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        DocumentDetailResponse: Document details
    """
    from backend.models.document import Document

    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    # Check permissions
    perm_service = PermissionService(db)
    if not await perm_service.check_document_permission(
        document_id, current_user.id, "view"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied",
        )

    # Log access
    audit = AuditService(db)
    await audit.log_document_access(document_id, current_user.id, "viewed")

    # Increment view count
    document.view_count += 1
    db.commit()

    return DocumentDetailResponse.model_validate(document)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    permanent: bool = Query(False),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> None:
    """
    Delete a document.

    Args:
        document_id: Document ID
        permanent: Permanently delete (vs soft delete)
        db: Database session
        current_user: Current authenticated user
    """
    from backend.models.document import Document, DocumentStatus

    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    # Check permissions (only owner or admin can delete)
    if document.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only document owner can delete",
        )

    # Log action
    audit = AuditService(db)
    await audit.log_document_access(
        document_id, current_user.id, "deleted", {"permanent": permanent}
    )

    if permanent:
        # Delete file from storage
        storage = StorageManager()
        await storage.delete_file(document.file_path)
        db.delete(document)
    else:
        # Soft delete
        document.status = DocumentStatus.DELETED

    db.commit()

    logger.info(
        "document_deleted",
        document_id=document_id,
        user_id=current_user.id,
        permanent=permanent,
    )


# Search


@router.post("/search", response_model=SearchResponse)
async def search_documents(
    query: SearchQuery,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> SearchResponse:
    """
    Search documents.

    Args:
        query: Search query
        db: Database session
        current_user: Current authenticated user

    Returns:
        SearchResponse: Search results
    """
    search_service = DocumentSearchService(db)
    results = await search_service.search(query, current_user.id)
    return results


# Permissions


@router.post("/{document_id}/permissions", response_model=PermissionResponse)
async def grant_permission(
    document_id: int,
    permission: PermissionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> PermissionResponse:
    """Grant document permission."""
    perm_service = PermissionService(db)

    # Check if user has admin access
    if not await perm_service.check_document_permission(
        document_id, current_user.id, "admin"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required to grant permissions",
        )

    perm = await perm_service.grant_document_permission(
        document_id=document_id,
        user_id=permission.user_id,
        access_level=permission.access_level,
        granted_by_id=current_user.id,
        expires_at=permission.expires_at,
    )

    return PermissionResponse.model_validate(perm)


@router.get("/{document_id}/permissions", response_model=List[PermissionResponse])
async def list_permissions(
    document_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> List[PermissionResponse]:
    """List document permissions."""
    perm_service = PermissionService(db)
    permissions = await perm_service.list_document_permissions(document_id)
    return [PermissionResponse.model_validate(p) for p in permissions]


# Share Links


@router.post("/{document_id}/share", response_model=ShareLinkResponse)
async def create_share_link(
    document_id: int,
    share_link: ShareLinkCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> ShareLinkResponse:
    """Create a shareable link for a document."""
    from modules.documents.permissions import ShareLinkService

    share_service = ShareLinkService(db)
    link = await share_service.create_share_link(
        document_id=document_id,
        created_by_id=current_user.id,
        share_type=share_link.share_type,
        access_level=share_link.access_level,
        password=share_link.password,
        expires_at=share_link.expires_at,
        max_downloads=share_link.max_downloads,
    )

    return ShareLinkResponse.model_validate(link)


# Comments


@router.post("/{document_id}/comments", response_model=CommentResponse)
async def create_comment(
    document_id: int,
    comment: CommentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> CommentResponse:
    """Add a comment to a document."""
    from modules.documents.collaboration import CollaborationService

    collab_service = CollaborationService(db)
    new_comment = await collab_service.add_comment(
        document_id=document_id,
        user_id=current_user.id,
        content=comment.content,
        parent_id=comment.parent_id,
    )

    return CommentResponse.model_validate(new_comment)


@router.get("/{document_id}/comments", response_model=List[CommentResponse])
async def list_comments(
    document_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> List[CommentResponse]:
    """List document comments."""
    from modules.documents.collaboration import CollaborationService

    collab_service = CollaborationService(db)
    comments = await collab_service.get_document_comments(document_id)
    return [CommentResponse.model_validate(c) for c in comments]


# Workflows


@router.post("/{document_id}/workflows", response_model=WorkflowResponse)
async def create_workflow(
    document_id: int,
    workflow: WorkflowCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> WorkflowResponse:
    """Create a workflow for document approval."""
    from modules.documents.workflow import WorkflowEngine

    workflow_engine = WorkflowEngine(db)
    new_workflow = await workflow_engine.create_workflow(
        document_id=document_id,
        workflow_name=workflow.workflow_name,
        steps=workflow.steps,
        initiated_by_id=current_user.id,
    )

    return WorkflowResponse.model_validate(new_workflow)


# Versions


@router.get("/{document_id}/versions", response_model=List[VersionResponse])
async def list_versions(
    document_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> List[VersionResponse]:
    """List document versions."""
    from modules.documents.versioning import VersionControlService

    version_service = VersionControlService(db)
    versions = await version_service.list_versions(document_id)
    return [VersionResponse.model_validate(v) for v in versions]


# AI Operations


@router.post("/{document_id}/ai/summarize")
async def summarize_document(
    document_id: int,
    max_length: int = Query(200, ge=50, le=1000),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> dict:
    """Generate AI summary of document."""
    from backend.models.document import Document

    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Get document content
    storage = StorageManager()
    content = await storage.get_file(document.file_path)

    # Generate summary
    ai_assistant = DocumentAIAssistant()
    summary = await ai_assistant.summarize_document(
        content.decode("utf-8", errors="ignore"), max_length=max_length
    )

    return summary


@router.post("/{document_id}/ai/classify")
async def classify_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> dict:
    """AI-powered document classification."""
    from backend.models.document import Document

    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Get document content
    storage = StorageManager()
    content = await storage.get_file(document.file_path)

    # Classify
    ai_assistant = DocumentAIAssistant()
    classification = await ai_assistant.classify_document(
        content.decode("utf-8", errors="ignore"), document.file_name
    )

    return classification


# Statistics


@router.get("/stats/overview", response_model=DocumentStatistics)
async def get_statistics(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> DocumentStatistics:
    """Get document statistics."""
    from backend.models.document import Document
    from sqlalchemy import func

    # Get statistics
    total_docs = db.query(func.count(Document.id)).scalar()
    total_size = db.query(func.sum(Document.file_size)).scalar() or 0
    total_views = db.query(func.sum(Document.view_count)).scalar() or 0
    total_downloads = db.query(func.sum(Document.download_count)).scalar() or 0

    return DocumentStatistics(
        total_documents=total_docs,
        total_size=total_size,
        total_views=total_views,
        total_downloads=total_downloads,
        documents_by_status={},
        documents_by_type={},
        recent_activity_count=0,
    )
