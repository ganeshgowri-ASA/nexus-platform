"""
Versioning System Module

Article versioning, change tracking, and update notifications.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import desc
from sqlalchemy.orm import Session

from .models import Article, ArticleVersion

logger = logging.getLogger(__name__)


class VersionManager:
    """Manager for content versioning and change tracking."""

    def __init__(self, db_session: Session):
        self.db = db_session

    async def create_version(
        self,
        article_id: UUID,
        changed_by: UUID,
        change_summary: Optional[str] = None,
    ) -> ArticleVersion:
        """Create a new version of an article."""
        try:
            article = self.db.query(Article).filter(Article.id == article_id).first()
            if not article:
                raise ValueError(f"Article {article_id} not found")

            version = ArticleVersion(
                article_id=article.id,
                version=article.version,
                title=article.title,
                content=article.content,
                changed_by=changed_by,
                change_summary=change_summary,
            )

            self.db.add(version)
            self.db.commit()
            self.db.refresh(version)

            return version

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating version: {str(e)}")
            raise

    async def get_version_history(
        self,
        article_id: UUID,
        limit: int = 10,
    ) -> List[ArticleVersion]:
        """Get version history for an article."""
        try:
            versions = (
                self.db.query(ArticleVersion)
                .filter(ArticleVersion.article_id == article_id)
                .order_by(desc(ArticleVersion.version))
                .limit(limit)
                .all()
            )

            return versions

        except Exception as e:
            logger.error(f"Error getting version history: {str(e)}")
            return []

    async def revert_to_version(
        self,
        article_id: UUID,
        version_number: int,
        reverted_by: UUID,
    ) -> Article:
        """Revert article to a previous version."""
        try:
            version = (
                self.db.query(ArticleVersion)
                .filter(
                    ArticleVersion.article_id == article_id,
                    ArticleVersion.version == version_number,
                )
                .first()
            )

            if not version:
                raise ValueError(f"Version {version_number} not found")

            article = self.db.query(Article).filter(Article.id == article_id).first()
            if not article:
                raise ValueError(f"Article {article_id} not found")

            # Create version of current state
            await self.create_version(
                article_id,
                reverted_by,
                f"Reverted to version {version_number}",
            )

            # Revert content
            article.title = version.title
            article.content = version.content
            article.version += 1
            article.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(article)

            return article

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error reverting to version: {str(e)}")
            raise
