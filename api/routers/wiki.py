"""
NEXUS Wiki System - FastAPI Router

RESTful API endpoints for wiki operations including:
- Full CRUD operations for pages
- Search and filtering
- Category and tag management
- Version history
- Comments and discussions
- Analytics
- File attachments
- Permissions

Author: NEXUS Platform Team
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import (
    APIRouter, Depends, HTTPException, status, UploadFile,
    File, Query, Path as PathParam, Body
)
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from pydantic import BaseModel, Field
import logging

from database import get_db
from modules.wiki.models import (
    WikiPage, WikiCategory, WikiTag, WikiComment,
    WikiHistory, WikiAttachment, WikiPermission,
    WikiTemplate, WikiAnalytics
)
from modules.wiki.wiki_types import (
    PageStatus, ContentFormat, PermissionLevel,
    PageCreateRequest, PageUpdateRequest, PageSearchRequest,
    WikiPage as WikiPageSchema, WikiCategory as WikiCategorySchema,
    WikiTag as WikiTagSchema, WikiComment as WikiCommentSchema,
    WikiHistory as WikiHistorySchema, AnalyticsData
)
from modules.wiki.pages import PageManager
from modules.wiki.editor import EditorService
from modules.wiki.versioning import VersioningService
from modules.wiki.search import SearchService
from modules.wiki.categories import CategoryService
from modules.wiki.comments import CommentService
from modules.wiki.analytics import AnalyticsService
from modules.wiki.attachments import AttachmentService
from modules.wiki.permissions import PermissionService

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/wiki",
    tags=["wiki"],
    responses={404: {"description": "Not found"}},
)


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
    success: bool = True


class PageListResponse(BaseModel):
    """Response model for page lists with pagination."""
    pages: List[WikiPageSchema]
    total: int
    page: int
    page_size: int
    total_pages: int


class SearchResponse(BaseModel):
    """Response model for search results."""
    results: List[WikiPageSchema]
    total: int
    query: str
    took_ms: float


class CommentCreateRequest(BaseModel):
    """Request model for creating a comment."""
    content: str = Field(..., min_length=1)
    parent_comment_id: Optional[int] = None
    mentions: Optional[List[int]] = None


class PermissionRequest(BaseModel):
    """Request model for setting permissions."""
    user_id: Optional[int] = None
    role: Optional[str] = None
    permission_level: PermissionLevel


class BulkDeleteRequest(BaseModel):
    """Request model for bulk delete operations."""
    page_ids: List[int] = Field(..., min_items=1)


# ============================================================================
# AUTHENTICATION & AUTHORIZATION
# ============================================================================

def get_current_user_id() -> int:
    """
    Get current authenticated user ID.
    TODO: Implement proper JWT authentication.
    """
    # Placeholder - implement proper JWT auth
    return 1


def check_page_permission(
    page_id: int,
    user_id: int,
    required_level: PermissionLevel,
    db: Session
) -> bool:
    """Check if user has required permission for a page."""
    ps = PermissionService(db)
    return ps.check_permission(page_id, user_id, required_level)


# ============================================================================
# PAGE ENDPOINTS
# ============================================================================

@router.get("/pages", response_model=PageListResponse)
def list_pages(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[PageStatus] = Query(None, description="Filter by status"),
    category_id: Optional[int] = Query(None, description="Filter by category"),
    namespace: Optional[str] = Query(None, description="Filter by namespace"),
    search: Optional[str] = Query(None, description="Search query"),
    sort_by: str = Query("updated_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    db: Session = Depends(get_db)
) -> PageListResponse:
    """
    List all wiki pages with pagination and filtering.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        status: Filter by page status
        category_id: Filter by category
        namespace: Filter by namespace
        search: Search in title and content
        sort_by: Field to sort by
        sort_order: Sort order (asc/desc)
        db: Database session

    Returns:
        Paginated list of pages
    """
    try:
        query = db.query(WikiPage).filter(WikiPage.is_deleted == False)

        # Apply filters
        if status:
            query = query.filter(WikiPage.status == status)
        if category_id:
            query = query.filter(WikiPage.category_id == category_id)
        if namespace:
            query = query.filter(WikiPage.namespace == namespace)
        if search:
            query = query.filter(
                or_(
                    WikiPage.title.ilike(f"%{search}%"),
                    WikiPage.content.ilike(f"%{search}%")
                )
            )

        # Get total count
        total = query.count()

        # Apply sorting
        sort_column = getattr(WikiPage, sort_by, WikiPage.updated_at)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)

        # Apply pagination
        offset = (page - 1) * page_size
        pages = query.offset(offset).limit(page_size).all()

        # Convert to schema
        page_schemas = [WikiPageSchema.model_validate(p) for p in pages]

        return PageListResponse(
            pages=page_schemas,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )

    except Exception as e:
        logger.error(f"Error listing pages: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list pages"
        )


@router.post("/pages", response_model=WikiPageSchema, status_code=status.HTTP_201_CREATED)
def create_page(
    request: PageCreateRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
) -> WikiPageSchema:
    """
    Create a new wiki page.

    Args:
        request: Page creation request
        db: Database session
        user_id: Current user ID

    Returns:
        Created page

    Raises:
        HTTPException: If page creation fails
    """
    try:
        pm = PageManager(db)
        page = pm.create_page(request, user_id)
        db.commit()

        return WikiPageSchema.model_validate(page)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating page: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create page"
        )


@router.get("/pages/{page_id}", response_model=WikiPageSchema)
def get_page(
    page_id: int = PathParam(..., description="Page ID"),
    increment_views: bool = Query(True, description="Increment view count"),
    db: Session = Depends(get_db)
) -> WikiPageSchema:
    """
    Get a specific wiki page by ID.

    Args:
        page_id: Page ID
        increment_views: Whether to increment view count
        db: Database session

    Returns:
        Page details

    Raises:
        HTTPException: If page not found
    """
    page = db.query(WikiPage).filter(
        WikiPage.id == page_id,
        WikiPage.is_deleted == False
    ).first()

    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found"
        )

    # Increment view count
    if increment_views:
        page.view_count += 1
        page.last_viewed_at = datetime.utcnow()
        db.commit()

    return WikiPageSchema.model_validate(page)


@router.put("/pages/{page_id}", response_model=WikiPageSchema)
def update_page(
    page_id: int = PathParam(..., description="Page ID"),
    request: PageUpdateRequest = Body(...),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
) -> WikiPageSchema:
    """
    Update an existing wiki page.

    Args:
        page_id: Page ID
        request: Page update request
        db: Database session
        user_id: Current user ID

    Returns:
        Updated page

    Raises:
        HTTPException: If page not found or update fails
    """
    try:
        pm = PageManager(db)
        page = pm.update_page(page_id, request, user_id)
        db.commit()

        return WikiPageSchema.model_validate(page)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating page: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update page"
        )


@router.delete("/pages/{page_id}", response_model=MessageResponse)
def delete_page(
    page_id: int = PathParam(..., description="Page ID"),
    permanent: bool = Query(False, description="Permanently delete (cannot be undone)"),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
) -> MessageResponse:
    """
    Delete a wiki page (soft or hard delete).

    Args:
        page_id: Page ID
        permanent: If True, permanently delete; if False, soft delete
        db: Database session
        user_id: Current user ID

    Returns:
        Success message

    Raises:
        HTTPException: If page not found or deletion fails
    """
    try:
        pm = PageManager(db)

        if permanent:
            pm.delete_page_permanent(page_id, user_id)
            message = "Page permanently deleted"
        else:
            pm.delete_page(page_id, user_id)
            message = "Page deleted (can be restored)"

        db.commit()

        return MessageResponse(message=message)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting page: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete page"
        )


@router.post("/pages/bulk-delete", response_model=MessageResponse)
def bulk_delete_pages(
    request: BulkDeleteRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
) -> MessageResponse:
    """
    Bulk delete multiple pages.

    Args:
        request: Bulk delete request with page IDs
        db: Database session
        user_id: Current user ID

    Returns:
        Success message with count
    """
    try:
        pm = PageManager(db)
        count = 0

        for page_id in request.page_ids:
            try:
                pm.delete_page(page_id, user_id)
                count += 1
            except Exception as e:
                logger.warning(f"Failed to delete page {page_id}: {e}")

        db.commit()

        return MessageResponse(
            message=f"Successfully deleted {count} out of {len(request.page_ids)} pages"
        )

    except Exception as e:
        logger.error(f"Error in bulk delete: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform bulk delete"
        )


# ============================================================================
# SEARCH ENDPOINTS
# ============================================================================

@router.get("/search", response_model=SearchResponse)
def search_pages(
    query: str = Query(..., min_length=1, description="Search query"),
    category_id: Optional[int] = Query(None, description="Filter by category"),
    tags: Optional[str] = Query(None, description="Comma-separated tag names"),
    status: Optional[PageStatus] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Result offset"),
    db: Session = Depends(get_db)
) -> SearchResponse:
    """
    Search wiki pages with advanced filtering.

    Args:
        query: Search query string
        category_id: Filter by category ID
        tags: Comma-separated tag names
        status: Filter by page status
        limit: Maximum number of results
        offset: Result offset for pagination
        db: Database session

    Returns:
        Search results with metadata
    """
    try:
        start_time = datetime.utcnow()

        # Build search request
        tag_list = tags.split(",") if tags else None

        search_request = PageSearchRequest(
            query=query,
            category_id=category_id,
            tags=tag_list,
            status=status,
            limit=limit,
            offset=offset
        )

        # Perform search
        ss = SearchService(db)
        results = ss.search_pages(search_request)

        # Calculate time taken
        end_time = datetime.utcnow()
        took_ms = (end_time - start_time).total_seconds() * 1000

        return SearchResponse(
            results=results,
            total=len(results),
            query=query,
            took_ms=took_ms
        )

    except Exception as e:
        logger.error(f"Error searching pages: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed"
        )


# ============================================================================
# CATEGORY ENDPOINTS
# ============================================================================

@router.get("/categories", response_model=List[WikiCategorySchema])
def list_categories(
    parent_id: Optional[int] = Query(None, description="Filter by parent category"),
    db: Session = Depends(get_db)
) -> List[WikiCategorySchema]:
    """
    List all categories, optionally filtered by parent.

    Args:
        parent_id: Parent category ID (None for root categories)
        db: Database session

    Returns:
        List of categories
    """
    try:
        query = db.query(WikiCategory).filter(WikiCategory.is_active == True)

        if parent_id is not None:
            query = query.filter(WikiCategory.parent_id == parent_id)
        else:
            query = query.filter(WikiCategory.parent_id == None)

        categories = query.order_by(WikiCategory.order).all()
        return [WikiCategorySchema.model_validate(c) for c in categories]

    except Exception as e:
        logger.error(f"Error listing categories: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list categories"
        )


@router.post("/categories", response_model=WikiCategorySchema, status_code=status.HTTP_201_CREATED)
def create_category(
    name: str = Body(...),
    description: Optional[str] = Body(None),
    parent_id: Optional[int] = Body(None),
    icon: Optional[str] = Body(None),
    color: Optional[str] = Body(None),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
) -> WikiCategorySchema:
    """
    Create a new category.

    Args:
        name: Category name
        description: Category description
        parent_id: Parent category ID
        icon: Category icon
        color: Category color (hex)
        db: Database session
        user_id: Current user ID

    Returns:
        Created category
    """
    try:
        cs = CategoryService(db)
        category = cs.create_category(
            name=name,
            description=description,
            parent_id=parent_id,
            icon=icon,
            color=color,
            created_by=user_id
        )
        db.commit()

        return WikiCategorySchema.model_validate(category)

    except Exception as e:
        logger.error(f"Error creating category: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create category"
        )


@router.get("/categories/{category_id}/pages", response_model=List[WikiPageSchema])
def get_category_pages(
    category_id: int = PathParam(..., description="Category ID"),
    recursive: bool = Query(False, description="Include subcategories"),
    db: Session = Depends(get_db)
) -> List[WikiPageSchema]:
    """
    Get all pages in a category.

    Args:
        category_id: Category ID
        recursive: If True, include pages from subcategories
        db: Database session

    Returns:
        List of pages in category
    """
    try:
        cs = CategoryService(db)
        pages = cs.get_category_pages(category_id, recursive=recursive)
        return [WikiPageSchema.model_validate(p) for p in pages]

    except Exception as e:
        logger.error(f"Error getting category pages: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get category pages"
        )


# ============================================================================
# TAG ENDPOINTS
# ============================================================================

@router.get("/tags", response_model=List[WikiTagSchema])
def list_tags(
    limit: int = Query(100, ge=1, le=500, description="Max tags to return"),
    sort_by: str = Query("usage_count", description="Sort field"),
    db: Session = Depends(get_db)
) -> List[WikiTagSchema]:
    """
    List all tags, sorted by usage count.

    Args:
        limit: Maximum number of tags to return
        sort_by: Field to sort by
        db: Database session

    Returns:
        List of tags
    """
    try:
        sort_column = getattr(WikiTag, sort_by, WikiTag.usage_count)
        tags = db.query(WikiTag).order_by(desc(sort_column)).limit(limit).all()
        return [WikiTagSchema.model_validate(t) for t in tags]

    except Exception as e:
        logger.error(f"Error listing tags: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list tags"
        )


@router.get("/tags/{tag_name}/pages", response_model=List[WikiPageSchema])
def get_tag_pages(
    tag_name: str = PathParam(..., description="Tag name"),
    db: Session = Depends(get_db)
) -> List[WikiPageSchema]:
    """
    Get all pages with a specific tag.

    Args:
        tag_name: Tag name
        db: Database session

    Returns:
        List of pages with tag
    """
    try:
        tag = db.query(WikiTag).filter(WikiTag.name == tag_name.lower()).first()
        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tag not found"
            )

        pages = [p for p in tag.pages if not p.is_deleted]
        return [WikiPageSchema.model_validate(p) for p in pages]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tag pages: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get tag pages"
        )


# ============================================================================
# VERSION HISTORY ENDPOINTS
# ============================================================================

@router.get("/pages/{page_id}/history", response_model=List[WikiHistorySchema])
def get_page_history(
    page_id: int = PathParam(..., description="Page ID"),
    limit: int = Query(50, ge=1, le=200, description="Max history entries"),
    db: Session = Depends(get_db)
) -> List[WikiHistorySchema]:
    """
    Get version history for a page.

    Args:
        page_id: Page ID
        limit: Maximum number of history entries
        db: Database session

    Returns:
        List of history entries
    """
    try:
        history = db.query(WikiHistory).filter(
            WikiHistory.page_id == page_id
        ).order_by(desc(WikiHistory.version)).limit(limit).all()

        return [WikiHistorySchema.model_validate(h) for h in history]

    except Exception as e:
        logger.error(f"Error getting page history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get page history"
        )


@router.get("/pages/{page_id}/history/{version}", response_model=WikiHistorySchema)
def get_page_version(
    page_id: int = PathParam(..., description="Page ID"),
    version: int = PathParam(..., ge=1, description="Version number"),
    db: Session = Depends(get_db)
) -> WikiHistorySchema:
    """
    Get a specific version of a page.

    Args:
        page_id: Page ID
        version: Version number
        db: Database session

    Returns:
        Specific version details
    """
    history = db.query(WikiHistory).filter(
        WikiHistory.page_id == page_id,
        WikiHistory.version == version
    ).first()

    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found"
        )

    return WikiHistorySchema.model_validate(history)


@router.post("/pages/{page_id}/history/{version}/restore", response_model=WikiPageSchema)
def restore_page_version(
    page_id: int = PathParam(..., description="Page ID"),
    version: int = PathParam(..., ge=1, description="Version number"),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
) -> WikiPageSchema:
    """
    Restore a page to a previous version.

    Args:
        page_id: Page ID
        version: Version number to restore
        db: Database session
        user_id: Current user ID

    Returns:
        Restored page
    """
    try:
        vs = VersioningService(db)
        page = vs.restore_version(page_id, version, user_id)
        db.commit()

        return WikiPageSchema.model_validate(page)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error restoring version: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to restore version"
        )


# ============================================================================
# COMMENT ENDPOINTS
# ============================================================================

@router.get("/pages/{page_id}/comments", response_model=List[WikiCommentSchema])
def get_page_comments(
    page_id: int = PathParam(..., description="Page ID"),
    db: Session = Depends(get_db)
) -> List[WikiCommentSchema]:
    """
    Get all comments for a page.

    Args:
        page_id: Page ID
        db: Database session

    Returns:
        List of comments
    """
    try:
        comments = db.query(WikiComment).filter(
            WikiComment.page_id == page_id,
            WikiComment.is_deleted == False
        ).order_by(WikiComment.created_at.desc()).all()

        return [WikiCommentSchema.model_validate(c) for c in comments]

    except Exception as e:
        logger.error(f"Error getting comments: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get comments"
        )


@router.post("/pages/{page_id}/comments", response_model=WikiCommentSchema, status_code=status.HTTP_201_CREATED)
def add_page_comment(
    page_id: int = PathParam(..., description="Page ID"),
    request: CommentCreateRequest = Body(...),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
) -> WikiCommentSchema:
    """
    Add a comment to a page.

    Args:
        page_id: Page ID
        request: Comment creation request
        db: Database session
        user_id: Current user ID

    Returns:
        Created comment
    """
    try:
        cs = CommentService(db)
        comment = cs.add_comment(
            page_id=page_id,
            author_id=user_id,
            content=request.content,
            parent_comment_id=request.parent_comment_id,
            mentions=request.mentions
        )
        db.commit()

        return WikiCommentSchema.model_validate(comment)

    except Exception as e:
        logger.error(f"Error adding comment: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add comment"
        )


@router.delete("/comments/{comment_id}", response_model=MessageResponse)
def delete_comment(
    comment_id: int = PathParam(..., description="Comment ID"),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
) -> MessageResponse:
    """
    Delete a comment.

    Args:
        comment_id: Comment ID
        db: Database session
        user_id: Current user ID

    Returns:
        Success message
    """
    try:
        comment = db.query(WikiComment).get(comment_id)
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found"
            )

        # Check authorization (user must be comment author or admin)
        if comment.author_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this comment"
            )

        comment.is_deleted = True
        db.commit()

        return MessageResponse(message="Comment deleted")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting comment: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete comment"
        )


# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@router.get("/analytics/overview", response_model=AnalyticsData)
def get_analytics_overview(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db)
) -> AnalyticsData:
    """
    Get analytics overview for the wiki.

    Args:
        days: Number of days to analyze
        db: Database session

    Returns:
        Analytics data
    """
    try:
        as_service = AnalyticsService(db)
        start_date = datetime.utcnow() - timedelta(days=days)
        end_date = datetime.utcnow()

        analytics = as_service.get_overview(start_date, end_date)
        return analytics

    except Exception as e:
        logger.error(f"Error getting analytics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get analytics"
        )


@router.get("/analytics/pages/{page_id}", response_model=AnalyticsData)
def get_page_analytics(
    page_id: int = PathParam(..., description="Page ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days"),
    db: Session = Depends(get_db)
) -> AnalyticsData:
    """
    Get analytics for a specific page.

    Args:
        page_id: Page ID
        days: Number of days to analyze
        db: Database session

    Returns:
        Page analytics data
    """
    try:
        as_service = AnalyticsService(db)
        start_date = datetime.utcnow() - timedelta(days=days)
        end_date = datetime.utcnow()

        analytics = as_service.get_page_analytics(page_id, start_date, end_date)
        return analytics

    except Exception as e:
        logger.error(f"Error getting page analytics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get page analytics"
        )


# ============================================================================
# ATTACHMENT ENDPOINTS
# ============================================================================

@router.post("/pages/{page_id}/attachments", status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    page_id: int = PathParam(..., description="Page ID"),
    file: UploadFile = File(...),
    description: Optional[str] = Body(None),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """
    Upload a file attachment to a page.

    Args:
        page_id: Page ID
        file: File to upload
        description: File description
        db: Database session
        user_id: Current user ID

    Returns:
        Attachment metadata
    """
    try:
        # Verify page exists
        page = db.query(WikiPage).get(page_id)
        if not page or page.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Page not found"
            )

        # Save attachment
        attachment_service = AttachmentService(db)
        file_content = await file.read()

        attachment = attachment_service.save_attachment(
            page_id=page_id,
            filename=file.filename,
            content=file_content,
            content_type=file.content_type,
            description=description,
            uploaded_by=user_id
        )
        db.commit()

        return {
            "id": attachment.id,
            "filename": attachment.filename,
            "size": attachment.file_size,
            "mime_type": attachment.mime_type,
            "url": f"/api/wiki/attachments/{attachment.id}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading attachment: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload attachment"
        )


@router.get("/attachments/{attachment_id}")
async def download_attachment(
    attachment_id: int = PathParam(..., description="Attachment ID"),
    db: Session = Depends(get_db)
) -> FileResponse:
    """
    Download a file attachment.

    Args:
        attachment_id: Attachment ID
        db: Database session

    Returns:
        File response with attachment
    """
    try:
        attachment = db.query(WikiAttachment).get(attachment_id)
        if not attachment or attachment.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attachment not found"
            )

        return FileResponse(
            path=attachment.file_path,
            filename=attachment.original_filename,
            media_type=attachment.mime_type
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading attachment: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download attachment"
        )


@router.delete("/attachments/{attachment_id}", response_model=MessageResponse)
def delete_attachment(
    attachment_id: int = PathParam(..., description="Attachment ID"),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
) -> MessageResponse:
    """
    Delete an attachment.

    Args:
        attachment_id: Attachment ID
        db: Database session
        user_id: Current user ID

    Returns:
        Success message
    """
    try:
        attachment = db.query(WikiAttachment).get(attachment_id)
        if not attachment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attachment not found"
            )

        attachment.is_deleted = True
        db.commit()

        return MessageResponse(message="Attachment deleted")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting attachment: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete attachment"
        )


# ============================================================================
# PERMISSION ENDPOINTS
# ============================================================================

@router.get("/pages/{page_id}/permissions", response_model=List[WikiPermission])
def get_page_permissions(
    page_id: int = PathParam(..., description="Page ID"),
    db: Session = Depends(get_db)
) -> List[WikiPermission]:
    """
    Get permissions for a page.

    Args:
        page_id: Page ID
        db: Database session

    Returns:
        List of permissions
    """
    try:
        permissions = db.query(WikiPermission).filter(
            WikiPermission.page_id == page_id
        ).all()

        return permissions

    except Exception as e:
        logger.error(f"Error getting permissions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get permissions"
        )


@router.post("/pages/{page_id}/permissions", response_model=MessageResponse)
def set_page_permission(
    page_id: int = PathParam(..., description="Page ID"),
    request: PermissionRequest = Body(...),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
) -> MessageResponse:
    """
    Set permission for a page.

    Args:
        page_id: Page ID
        request: Permission request
        db: Database session
        user_id: Current user ID (must be page owner or admin)

    Returns:
        Success message
    """
    try:
        ps = PermissionService(db)
        ps.set_permission(
            page_id=page_id,
            user_id=request.user_id,
            role=request.role,
            permission_level=request.permission_level,
            granted_by=user_id
        )
        db.commit()

        return MessageResponse(message="Permission set successfully")

    except Exception as e:
        logger.error(f"Error setting permission: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set permission"
        )


# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

@router.get("/health")
def health_check() -> Dict[str, str]:
    """
    Health check endpoint.

    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": "wiki-api",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/stats")
def get_wiki_stats(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get wiki statistics.

    Args:
        db: Database session

    Returns:
        Wiki statistics
    """
    try:
        stats = {
            "total_pages": db.query(WikiPage).filter(
                WikiPage.is_deleted == False
            ).count(),
            "published_pages": db.query(WikiPage).filter(
                WikiPage.is_deleted == False,
                WikiPage.status == PageStatus.PUBLISHED
            ).count(),
            "total_categories": db.query(WikiCategory).filter(
                WikiCategory.is_active == True
            ).count(),
            "total_tags": db.query(WikiTag).count(),
            "total_comments": db.query(WikiComment).filter(
                WikiComment.is_deleted == False
            ).count(),
            "total_views": db.query(func.sum(WikiPage.view_count)).filter(
                WikiPage.is_deleted == False
            ).scalar() or 0
        }

        return stats

    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get statistics"
        )
