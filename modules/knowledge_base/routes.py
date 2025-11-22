"""
FastAPI Routes for Knowledge Base API

RESTful API endpoints with OpenAPI documentation.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from .analytics import AnalyticsManager
from .articles import ArticleManager
from .categories import CategoryManager
from .chatbot import ChatbotManager
from .export import ExportManager
from .faqs import FAQManager
from .glossary import GlossaryManager
from .import_kb import ImportManager
from .kb_types import (
    AccessLevel,
    Article,
    Category,
    ContentStatus,
    ContentType,
    FAQ,
    GlossaryTerm,
    Language,
    SearchQuery,
    Tutorial,
    Video,
)
from .multilingual import MultilingualManager
from .ratings import RatingManager
from .recommendations import RecommendationEngine
from .search import SearchEngine
from .templates import TemplateManager
from .tutorials import TutorialManager
from .versioning import VersionManager
from .videos import VideoManager

# Create router
router = APIRouter(prefix="/api/kb", tags=["Knowledge Base"])


# Dependency to get DB session (implement based on your setup)
def get_db():
    """Get database session."""
    # Implement your database session management
    pass


# Article Endpoints
@router.post("/articles", response_model=Article, status_code=status.HTTP_201_CREATED)
async def create_article(
    title: str,
    content: str,
    author_id: UUID,
    db: Session = Depends(get_db),
):
    """Create a new article."""
    article_mgr = ArticleManager(db)
    return await article_mgr.create_article(title=title, content=content, author_id=author_id)


@router.get("/articles/{article_id}", response_model=Article)
async def get_article(
    article_id: UUID,
    db: Session = Depends(get_db),
):
    """Get an article by ID."""
    article_mgr = ArticleManager(db)
    article = await article_mgr.get_article(article_id=article_id)

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    return article


@router.put("/articles/{article_id}", response_model=Article)
async def update_article(
    article_id: UUID,
    updated_by: UUID,
    db: Session = Depends(get_db),
    **updates,
):
    """Update an article."""
    article_mgr = ArticleManager(db)
    return await article_mgr.update_article(article_id, updated_by, **updates)


@router.post("/articles/{article_id}/publish", response_model=Article)
async def publish_article(
    article_id: UUID,
    db: Session = Depends(get_db),
):
    """Publish an article."""
    article_mgr = ArticleManager(db)
    return await article_mgr.publish_article(article_id)


@router.get("/articles", response_model=dict)
async def list_articles(
    status: Optional[ContentStatus] = None,
    category_id: Optional[UUID] = None,
    limit: int = Query(20, le=100),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """List articles with filtering."""
    article_mgr = ArticleManager(db)
    return await article_mgr.list_articles(
        status=status,
        category_id=category_id,
        limit=limit,
        offset=offset,
    )


# Search Endpoints
@router.post("/search")
async def search(
    query: str,
    content_types: Optional[List[ContentType]] = None,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """Search knowledge base."""
    search_engine = SearchEngine(db)
    return await search_engine.search(
        query=query,
        content_types=content_types,
        limit=limit,
    )


@router.get("/search/autocomplete")
async def autocomplete(
    query: str,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """Get autocomplete suggestions."""
    search_engine = SearchEngine(db)
    return await search_engine.autocomplete(query, limit)


@router.post("/search/question")
async def question_answering(
    question: str,
    db: Session = Depends(get_db),
):
    """Answer questions using KB."""
    search_engine = SearchEngine(db)
    return await search_engine.question_answering(question)


# Category Endpoints
@router.post("/categories", response_model=Category)
async def create_category(
    name: str,
    slug: Optional[str] = None,
    description: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Create a category."""
    category_mgr = CategoryManager(db)
    return await category_mgr.create_category(name, slug, description)


@router.get("/categories")
async def list_categories(
    db: Session = Depends(get_db),
):
    """List all categories."""
    category_mgr = CategoryManager(db)
    return await category_mgr.list_categories()


@router.get("/categories/tree")
async def get_category_tree(
    db: Session = Depends(get_db),
):
    """Get hierarchical category tree."""
    category_mgr = CategoryManager(db)
    return await category_mgr.get_category_tree()


# FAQ Endpoints
@router.post("/faqs", response_model=FAQ)
async def create_faq(
    question: str,
    answer: str,
    db: Session = Depends(get_db),
):
    """Create a FAQ."""
    faq_mgr = FAQManager(db)
    return await faq_mgr.create_faq(question, answer)


@router.get("/faqs")
async def list_faqs(
    category_id: Optional[UUID] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """List FAQs."""
    faq_mgr = FAQManager(db)
    return await faq_mgr.list_faqs(category_id=category_id, limit=limit)


# Tutorial Endpoints
@router.post("/tutorials", response_model=Tutorial)
async def create_tutorial(
    title: str,
    description: str,
    author_id: UUID,
    db: Session = Depends(get_db),
):
    """Create a tutorial."""
    tutorial_mgr = TutorialManager(db)
    return await tutorial_mgr.create_tutorial(title, description, author_id)


@router.post("/tutorials/{tutorial_id}/progress")
async def track_tutorial_progress(
    tutorial_id: UUID,
    user_id: UUID,
    current_step: int,
    completed_steps: List[int],
    db: Session = Depends(get_db),
):
    """Track tutorial progress."""
    tutorial_mgr = TutorialManager(db)
    return await tutorial_mgr.track_progress(
        tutorial_id,
        user_id,
        current_step,
        completed_steps,
    )


# Video Endpoints
@router.post("/videos", response_model=Video)
async def create_video(
    title: str,
    description: str,
    video_url: str,
    author_id: UUID,
    duration: int,
    db: Session = Depends(get_db),
):
    """Create a video."""
    video_mgr = VideoManager(db)
    return await video_mgr.create_video(
        title,
        description,
        video_url,
        author_id,
        duration,
    )


@router.post("/videos/{video_id}/watch")
async def track_watch_time(
    video_id: UUID,
    watch_duration: int,
    user_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
):
    """Track video watch time."""
    video_mgr = VideoManager(db)
    await video_mgr.track_watch_time(video_id, watch_duration, user_id)
    return {"status": "success"}


# Glossary Endpoints
@router.post("/glossary", response_model=GlossaryTerm)
async def create_glossary_term(
    term: str,
    definition: str,
    db: Session = Depends(get_db),
):
    """Create a glossary term."""
    glossary_mgr = GlossaryManager(db)
    return await glossary_mgr.create_term(term, definition)


@router.get("/glossary/search")
async def search_glossary(
    query: str,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """Search glossary terms."""
    glossary_mgr = GlossaryManager(db)
    return await glossary_mgr.search_terms(query, limit=limit)


# Rating Endpoints
@router.post("/ratings")
async def add_rating(
    content_id: UUID,
    content_type: ContentType,
    user_id: UUID,
    rating: int,
    is_helpful: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """Add a rating."""
    rating_mgr = RatingManager(db)
    return await rating_mgr.add_rating(
        content_id,
        content_type,
        user_id,
        rating,
        is_helpful,
    )


@router.post("/ratings/helpful")
async def mark_helpful(
    content_id: UUID,
    content_type: ContentType,
    user_id: UUID,
    is_helpful: bool,
    db: Session = Depends(get_db),
):
    """Mark content as helpful."""
    rating_mgr = RatingManager(db)
    await rating_mgr.mark_helpful(content_id, content_type, user_id, is_helpful)
    return {"status": "success"}


# Recommendation Endpoints
@router.get("/recommendations")
async def get_recommendations(
    user_id: Optional[UUID] = None,
    current_article_id: Optional[UUID] = None,
    limit: int = 5,
    db: Session = Depends(get_db),
):
    """Get content recommendations."""
    rec_engine = RecommendationEngine(db)
    return await rec_engine.get_recommendations(
        user_id,
        current_article_id,
        limit,
    )


# Analytics Endpoints
@router.get("/analytics/content/{content_id}")
async def get_content_analytics(
    content_id: UUID,
    days: int = 30,
    db: Session = Depends(get_db),
):
    """Get analytics for content."""
    analytics_mgr = AnalyticsManager(db)
    return await analytics_mgr.get_content_stats(content_id, days)


@router.get("/analytics/popular")
async def get_popular_content(
    days: int = 7,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """Get popular content."""
    analytics_mgr = AnalyticsManager(db)
    return await analytics_mgr.get_popular_content(days, limit)


# Chatbot Endpoints
@router.post("/chat/sessions")
async def create_chat_session(
    user_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
):
    """Create a chat session."""
    chatbot_mgr = ChatbotManager(db)
    return await chatbot_mgr.create_session(user_id)


@router.post("/chat/sessions/{session_id}/messages")
async def send_chat_message(
    session_id: UUID,
    message: str,
    db: Session = Depends(get_db),
):
    """Send a chat message."""
    chatbot_mgr = ChatbotManager(db)
    return await chatbot_mgr.send_message(session_id, message)


# Export Endpoints
@router.get("/export/article/{article_id}/pdf")
async def export_article_pdf(
    article_id: UUID,
    db: Session = Depends(get_db),
):
    """Export article to PDF."""
    export_mgr = ExportManager(db)
    pdf_content = await export_mgr.export_to_pdf(article_id)

    return StreamingResponse(
        iter([pdf_content]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=article_{article_id}.pdf"},
    )


@router.get("/export/article/{article_id}/docx")
async def export_article_docx(
    article_id: UUID,
    db: Session = Depends(get_db),
):
    """Export article to DOCX."""
    export_mgr = ExportManager(db)
    docx_content = await export_mgr.export_to_docx(article_id)

    return StreamingResponse(
        iter([docx_content]),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename=article_{article_id}.docx"},
    )


# Import Endpoints
@router.post("/import/markdown")
async def import_markdown(
    markdown_files: List[dict],
    author_id: UUID,
    db: Session = Depends(get_db),
):
    """Import articles from Markdown."""
    import_mgr = ImportManager(db)
    return await import_mgr.import_from_markdown(markdown_files, author_id)


# Template Endpoints
@router.get("/templates")
async def list_templates(
    content_type: Optional[ContentType] = None,
    db: Session = Depends(get_db),
):
    """List content templates."""
    template_mgr = TemplateManager(db)
    return await template_mgr.list_templates(content_type)


@router.post("/templates/{template_id}/apply")
async def apply_template(
    template_id: UUID,
    replacements: Optional[dict] = None,
    db: Session = Depends(get_db),
):
    """Apply a template."""
    template_mgr = TemplateManager(db)
    return await template_mgr.apply_template(template_id, replacements)


# Version Endpoints
@router.get("/articles/{article_id}/versions")
async def get_version_history(
    article_id: UUID,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """Get article version history."""
    version_mgr = VersionManager(db)
    return await version_mgr.get_version_history(article_id, limit)


@router.post("/articles/{article_id}/revert")
async def revert_to_version(
    article_id: UUID,
    version_number: int,
    reverted_by: UUID,
    db: Session = Depends(get_db),
):
    """Revert article to previous version."""
    version_mgr = VersionManager(db)
    return await version_mgr.revert_to_version(
        article_id,
        version_number,
        reverted_by,
    )


# Translation Endpoints
@router.post("/articles/{article_id}/translate")
async def translate_article(
    article_id: UUID,
    target_language: Language,
    db: Session = Depends(get_db),
):
    """Translate article to another language."""
    multilingual_mgr = MultilingualManager(db)
    return await multilingual_mgr.translate_article(article_id, target_language)


# Health check
@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "knowledge_base"}
