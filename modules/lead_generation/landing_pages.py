"""
Landing page management for lead generation.

This module provides landing page templates, A/B testing,
mobile responsive design, and conversion tracking.
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from .lead_types import LandingPage, LandingPageCreate
from .models import LandingPage as LandingPageModel
from shared.utils import generate_uuid, generate_slug, sanitize_input
from shared.exceptions import ValidationError, NotFoundError, DatabaseError
from config.logging_config import get_logger

logger = get_logger(__name__)


class LandingPageManager:
    """Landing page management service."""

    def __init__(self, db: Session):
        """
        Initialize landing page manager.

        Args:
            db: Database session.
        """
        self.db = db

    async def create_landing_page(
        self,
        page_data: LandingPageCreate,
        base_url: str = "https://nexus.com",
    ) -> LandingPage:
        """
        Create a new landing page.

        Args:
            page_data: Landing page creation data.
            base_url: Base URL for the landing page.

        Returns:
            Created landing page object.

        Raises:
            ValidationError: If page data is invalid.
            DatabaseError: If database operation fails.
        """
        try:
            # Generate slug if not provided
            slug = page_data.slug or generate_slug(page_data.name)

            # Validate slug uniqueness
            existing = self.db.query(LandingPageModel).filter(
                LandingPageModel.slug == slug
            ).first()
            if existing:
                raise ValidationError(f"Landing page with slug '{slug}' already exists")

            # Generate full URL
            url = f"{base_url}/landing/{slug}"

            # Create landing page
            page = LandingPageModel(
                id=generate_uuid(),
                name=page_data.name,
                title=sanitize_input(page_data.title),
                slug=slug,
                template=page_data.template,
                content=page_data.content,
                form_id=page_data.form_id,
                is_active=page_data.is_active,
                url=url,
            )

            self.db.add(page)
            self.db.commit()
            self.db.refresh(page)

            logger.info(f"Landing page created: {page.name} (ID: {page.id})")

            return LandingPage.model_validate(page)

        except IntegrityError:
            self.db.rollback()
            raise ValidationError(f"Landing page with name or slug already exists")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating landing page: {e}")
            raise DatabaseError(f"Failed to create landing page: {str(e)}")

    async def get_landing_page(self, page_id: str) -> LandingPage:
        """
        Get landing page by ID.

        Args:
            page_id: Page ID.

        Returns:
            Landing page object.

        Raises:
            NotFoundError: If page not found.
        """
        page = self.db.query(LandingPageModel).filter(
            LandingPageModel.id == page_id
        ).first()
        if not page:
            raise NotFoundError(f"Landing page not found: {page_id}")

        return LandingPage.model_validate(page)

    async def get_landing_page_by_slug(self, slug: str) -> LandingPage:
        """
        Get landing page by slug.

        Args:
            slug: Page slug.

        Returns:
            Landing page object.

        Raises:
            NotFoundError: If page not found.
        """
        page = self.db.query(LandingPageModel).filter(
            LandingPageModel.slug == slug
        ).first()
        if not page:
            raise NotFoundError(f"Landing page not found: {slug}")

        return LandingPage.model_validate(page)

    async def list_landing_pages(
        self,
        skip: int = 0,
        limit: int = 20,
        active_only: bool = False,
    ) -> List[LandingPage]:
        """
        List all landing pages.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            active_only: Only return active pages.

        Returns:
            List of landing page objects.
        """
        query = self.db.query(LandingPageModel)

        if active_only:
            query = query.filter(LandingPageModel.is_active == True)

        pages = query.offset(skip).limit(limit).all()

        return [LandingPage.model_validate(page) for page in pages]

    async def update_landing_page(self, page_id: str, updates: dict) -> LandingPage:
        """
        Update landing page.

        Args:
            page_id: Page ID.
            updates: Update data.

        Returns:
            Updated landing page object.

        Raises:
            NotFoundError: If page not found.
        """
        page = self.db.query(LandingPageModel).filter(
            LandingPageModel.id == page_id
        ).first()
        if not page:
            raise NotFoundError(f"Landing page not found: {page_id}")

        # Update fields
        for key, value in updates.items():
            if hasattr(page, key):
                setattr(page, key, value)

        self.db.commit()
        self.db.refresh(page)

        logger.info(f"Landing page updated: {page.name} (ID: {page.id})")

        return LandingPage.model_validate(page)

    async def track_page_view(self, page_id: str) -> None:
        """
        Track page view.

        Args:
            page_id: Page ID.
        """
        page = self.db.query(LandingPageModel).filter(
            LandingPageModel.id == page_id
        ).first()
        if page:
            page.views += 1
            self._update_conversion_rate(page)
            self.db.commit()

    async def track_submission(self, page_id: str) -> None:
        """
        Track form submission.

        Args:
            page_id: Page ID.
        """
        page = self.db.query(LandingPageModel).filter(
            LandingPageModel.id == page_id
        ).first()
        if page:
            page.submissions += 1
            self._update_conversion_rate(page)
            self.db.commit()

    def _update_conversion_rate(self, page: LandingPageModel) -> None:
        """
        Update conversion rate for page.

        Args:
            page: Landing page model.
        """
        if page.views > 0:
            page.conversion_rate = (page.submissions / page.views) * 100


class LandingPageTemplates:
    """Pre-built landing page templates."""

    @staticmethod
    def get_template(template_name: str) -> dict:
        """
        Get landing page template by name.

        Args:
            template_name: Template name.

        Returns:
            Template configuration.
        """
        templates = {
            "hero_form": {
                "name": "Hero with Form",
                "sections": [
                    {
                        "type": "hero",
                        "headline": "Transform Your Business Today",
                        "subheadline": "Join thousands of companies already succeeding",
                        "background_image": "/images/hero-bg.jpg",
                    },
                    {
                        "type": "form",
                        "position": "right",
                    },
                ],
            },
            "video_sales": {
                "name": "Video Sales Page",
                "sections": [
                    {
                        "type": "video",
                        "video_url": "https://youtube.com/watch?v=example",
                        "thumbnail": "/images/video-thumb.jpg",
                    },
                    {
                        "type": "benefits",
                        "items": [
                            "Benefit 1",
                            "Benefit 2",
                            "Benefit 3",
                        ],
                    },
                    {
                        "type": "form",
                        "position": "center",
                    },
                ],
            },
            "webinar": {
                "name": "Webinar Registration",
                "sections": [
                    {
                        "type": "hero",
                        "headline": "Free Webinar: [Topic]",
                        "subheadline": "Date & Time",
                    },
                    {
                        "type": "speakers",
                        "speakers": [],
                    },
                    {
                        "type": "form",
                        "position": "center",
                    },
                ],
            },
        }

        return templates.get(template_name, templates["hero_form"])


class ABTestingManager:
    """A/B testing manager for landing pages."""

    def __init__(self, db: Session):
        """
        Initialize A/B testing manager.

        Args:
            db: Database session.
        """
        self.db = db

    async def create_variant(
        self,
        original_page_id: str,
        variant_data: dict,
    ) -> LandingPage:
        """
        Create A/B test variant.

        Args:
            original_page_id: Original page ID.
            variant_data: Variant configuration.

        Returns:
            Created variant page.
        """
        original = self.db.query(LandingPageModel).filter(
            LandingPageModel.id == original_page_id
        ).first()
        if not original:
            raise NotFoundError(f"Original page not found: {original_page_id}")

        # Create variant
        variant = LandingPageModel(
            id=generate_uuid(),
            name=f"{original.name} - Variant",
            title=variant_data.get("title", original.title),
            slug=f"{original.slug}-variant-{generate_uuid()[:8]}",
            template=original.template,
            content=variant_data.get("content", original.content),
            form_id=original.form_id,
            is_active=True,
        )

        self.db.add(variant)
        self.db.commit()
        self.db.refresh(variant)

        logger.info(f"A/B test variant created for page: {original.name}")

        return LandingPage.model_validate(variant)

    async def get_winner(
        self,
        page_id_a: str,
        page_id_b: str,
    ) -> tuple[str, float]:
        """
        Determine A/B test winner.

        Args:
            page_id_a: Page A ID.
            page_id_b: Page B ID.

        Returns:
            Tuple of (winner_id, confidence_level).
        """
        page_a = self.db.query(LandingPageModel).filter(
            LandingPageModel.id == page_id_a
        ).first()
        page_b = self.db.query(LandingPageModel).filter(
            LandingPageModel.id == page_id_b
        ).first()

        if not page_a or not page_b:
            raise NotFoundError("One or both pages not found")

        # Simple winner determination based on conversion rate
        if page_a.conversion_rate > page_b.conversion_rate:
            winner_id = page_id_a
            confidence = min(
                ((page_a.conversion_rate - page_b.conversion_rate) / page_b.conversion_rate) * 100,
                99.0
            ) if page_b.conversion_rate > 0 else 50.0
        else:
            winner_id = page_id_b
            confidence = min(
                ((page_b.conversion_rate - page_a.conversion_rate) / page_a.conversion_rate) * 100,
                99.0
            ) if page_a.conversion_rate > 0 else 50.0

        return winner_id, confidence
