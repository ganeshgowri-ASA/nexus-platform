"""
FAQ Management Module

Comprehensive FAQ system with auto-generation, voting, and organization.
"""

import logging
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from .kb_types import ContentStatus, Language
from .models import FAQ, Category, Tag

logger = logging.getLogger(__name__)


class FAQManager:
    """Manager for FAQ creation, organization, and auto-generation."""

    def __init__(self, db_session: Session):
        self.db = db_session

    async def create_faq(
        self,
        question: str,
        answer: str,
        category_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        language: Language = Language.EN,
        auto_generated: bool = False,
        source_type: Optional[str] = None,
    ) -> FAQ:
        """Create a new FAQ."""
        try:
            faq = FAQ(
                question=question,
                answer=answer,
                category_id=category_id,
                language=language.value,
                auto_generated=auto_generated,
                source_type=source_type,
            )

            if tags:
                from .categories import TagManager
                tag_mgr = TagManager(self.db)
                faq_tags = await tag_mgr.get_or_create_tags(tags)
                faq.tags.extend(faq_tags)

            self.db.add(faq)
            self.db.commit()
            self.db.refresh(faq)

            logger.info(f"Created FAQ: {faq.id}")
            return faq

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating FAQ: {str(e)}")
            raise

    async def update_faq(self, faq_id: UUID, **updates) -> FAQ:
        """Update an existing FAQ."""
        try:
            faq = self.db.query(FAQ).filter(FAQ.id == faq_id).first()
            if not faq:
                raise ValueError(f"FAQ {faq_id} not found")

            for key, value in updates.items():
                if hasattr(faq, key):
                    setattr(faq, key, value)

            self.db.commit()
            self.db.refresh(faq)
            return faq

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating FAQ: {str(e)}")
            raise

    async def list_faqs(
        self,
        category_id: Optional[UUID] = None,
        language: Optional[Language] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict:
        """List FAQs with filtering."""
        try:
            query = self.db.query(FAQ).filter(FAQ.status == ContentStatus.PUBLISHED.value)

            if category_id:
                query = query.filter(FAQ.category_id == category_id)

            if language:
                query = query.filter(FAQ.language == language.value)

            total = query.count()
            faqs = query.order_by(FAQ.order, desc(FAQ.helpful_count)).limit(limit).offset(offset).all()

            return {"faqs": faqs, "total": total, "limit": limit, "offset": offset}

        except Exception as e:
            logger.error(f"Error listing FAQs: {str(e)}")
            raise

    async def auto_generate_from_support_tickets(
        self,
        tickets: List[Dict],
        min_frequency: int = 3,
    ) -> List[FAQ]:
        """Auto-generate FAQs from support tickets using NLP."""
        try:
            # Group similar questions (simplified - use clustering in production)
            question_groups = self._cluster_questions([t["question"] for t in tickets])

            generated_faqs = []
            for group in question_groups:
                if len(group) >= min_frequency:
                    # Create FAQ from most common question
                    faq = await self.create_faq(
                        question=group[0]["question"],
                        answer=group[0]["answer"],
                        auto_generated=True,
                        source_type="support_ticket",
                        status=ContentStatus.IN_REVIEW,
                    )
                    generated_faqs.append(faq)

            return generated_faqs

        except Exception as e:
            logger.error(f"Error auto-generating FAQs: {str(e)}")
            raise

    def _cluster_questions(self, questions: List[str]) -> List[List[Dict]]:
        """Cluster similar questions (simplified version)."""
        # In production, use sentence embeddings + clustering
        return [[{"question": q, "answer": "Auto-generated answer"}] for q in questions]
