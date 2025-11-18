"""
Ratings and Feedback Module

User ratings, feedback collection, and helpful/not helpful voting.
"""

import logging
from typing import Dict, Optional
from uuid import UUID

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from .kb_types import ContentType
from .models import Article, Rating

logger = logging.getLogger(__name__)


class RatingManager:
    """Manager for content ratings and feedback."""

    def __init__(self, db_session: Session):
        self.db = db_session

    async def add_rating(
        self,
        content_id: UUID,
        content_type: ContentType,
        user_id: UUID,
        rating: int,
        is_helpful: Optional[bool] = None,
        comment: Optional[str] = None,
        tags: Optional[list] = None,
    ) -> Rating:
        """Add or update a rating."""
        try:
            # Check for existing rating
            existing = (
                self.db.query(Rating)
                .filter(
                    Rating.content_id == content_id,
                    Rating.user_id == user_id,
                )
                .first()
            )

            if existing:
                existing.rating = rating
                existing.is_helpful = is_helpful
                existing.comment = comment
                existing.feedback_tags = tags or []
                rating_obj = existing
            else:
                rating_obj = Rating(
                    content_id=content_id,
                    content_type=content_type.value,
                    user_id=user_id,
                    rating=rating,
                    is_helpful=is_helpful,
                    comment=comment,
                    feedback_tags=tags or [],
                )
                self.db.add(rating_obj)

            self.db.commit()
            self.db.refresh(rating_obj)

            # Update content average rating
            await self._update_content_rating(content_id, content_type)

            logger.info(f"Added rating for {content_type.value} {content_id}")
            return rating_obj

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding rating: {str(e)}")
            raise

    async def mark_helpful(
        self,
        content_id: UUID,
        content_type: ContentType,
        user_id: UUID,
        is_helpful: bool,
    ) -> None:
        """Mark content as helpful or not helpful."""
        try:
            await self.add_rating(
                content_id=content_id,
                content_type=content_type,
                user_id=user_id,
                rating=5 if is_helpful else 1,
                is_helpful=is_helpful,
            )

            # Update helpful counts
            if content_type == ContentType.ARTICLE:
                article = self.db.query(Article).filter(Article.id == content_id).first()
                if article:
                    if is_helpful:
                        article.helpful_count += 1
                    else:
                        article.not_helpful_count += 1
                    self.db.commit()

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error marking helpful: {str(e)}")
            raise

    async def get_content_ratings(
        self,
        content_id: UUID,
        limit: int = 50,
    ) -> Dict:
        """Get all ratings for content."""
        try:
            ratings = (
                self.db.query(Rating)
                .filter(Rating.content_id == content_id)
                .limit(limit)
                .all()
            )

            # Calculate statistics
            if ratings:
                avg_rating = sum(r.rating for r in ratings) / len(ratings)
                helpful_count = sum(1 for r in ratings if r.is_helpful)
                not_helpful_count = sum(1 for r in ratings if r.is_helpful is False)
            else:
                avg_rating = 0
                helpful_count = 0
                not_helpful_count = 0

            return {
                "ratings": ratings,
                "count": len(ratings),
                "average": avg_rating,
                "helpful_count": helpful_count,
                "not_helpful_count": not_helpful_count,
            }

        except Exception as e:
            logger.error(f"Error getting ratings: {str(e)}")
            raise

    async def _update_content_rating(
        self,
        content_id: UUID,
        content_type: ContentType,
    ) -> None:
        """Update the average rating for content."""
        try:
            avg_rating = (
                self.db.query(func.avg(Rating.rating))
                .filter(Rating.content_id == content_id)
                .scalar()
            ) or 0.0

            # Update based on content type
            if content_type == ContentType.ARTICLE:
                article = self.db.query(Article).filter(Article.id == content_id).first()
                if article:
                    article.average_rating = float(avg_rating)

            self.db.commit()

        except Exception as e:
            logger.error(f"Error updating content rating: {str(e)}")
