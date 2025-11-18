"""
Tutorial Management Module

Interactive tutorials with step-by-step guides and progress tracking.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from .kb_types import ContentStatus, DifficultyLevel, Language, TutorialStep
from .models import Tutorial, TutorialProgress

logger = logging.getLogger(__name__)


class TutorialManager:
    """Manager for interactive tutorials with progress tracking."""

    def __init__(self, db_session: Session):
        self.db = db_session

    async def create_tutorial(
        self,
        title: str,
        description: str,
        author_id: UUID,
        difficulty: DifficultyLevel = DifficultyLevel.BEGINNER,
        steps: Optional[List[Dict]] = None,
        prerequisites: Optional[List[str]] = None,
        learning_objectives: Optional[List[str]] = None,
        **kwargs,
    ) -> Tutorial:
        """Create a new tutorial."""
        try:
            slug = self._generate_slug(title)

            tutorial = Tutorial(
                title=title,
                slug=slug,
                description=description,
                author_id=author_id,
                difficulty=difficulty.value,
                steps=steps or [],
                prerequisites=prerequisites or [],
                learning_objectives=learning_objectives or [],
                **kwargs,
            )

            # Calculate estimated duration
            if steps:
                tutorial.estimated_duration = sum(
                    step.get("estimated_time", 5) for step in steps
                )

            self.db.add(tutorial)
            self.db.commit()
            self.db.refresh(tutorial)

            logger.info(f"Created tutorial: {tutorial.id} - {tutorial.title}")
            return tutorial

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating tutorial: {str(e)}")
            raise

    async def update_tutorial(self, tutorial_id: UUID, **updates) -> Tutorial:
        """Update a tutorial."""
        try:
            tutorial = self.db.query(Tutorial).filter(Tutorial.id == tutorial_id).first()
            if not tutorial:
                raise ValueError(f"Tutorial {tutorial_id} not found")

            for key, value in updates.items():
                if hasattr(tutorial, key):
                    setattr(tutorial, key, value)

            self.db.commit()
            self.db.refresh(tutorial)
            return tutorial

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating tutorial: {str(e)}")
            raise

    async def track_progress(
        self,
        tutorial_id: UUID,
        user_id: UUID,
        current_step: int,
        completed_steps: List[int],
    ) -> TutorialProgress:
        """Track user's tutorial progress."""
        try:
            progress = (
                self.db.query(TutorialProgress)
                .filter(
                    TutorialProgress.tutorial_id == tutorial_id,
                    TutorialProgress.user_id == user_id,
                )
                .first()
            )

            if not progress:
                progress = TutorialProgress(
                    tutorial_id=tutorial_id,
                    user_id=user_id,
                    current_step=current_step,
                    completed_steps=completed_steps,
                )
                self.db.add(progress)
            else:
                progress.current_step = current_step
                progress.completed_steps = completed_steps
                progress.last_accessed_at = datetime.utcnow()

            # Calculate completion percentage
            tutorial = self.db.query(Tutorial).filter(Tutorial.id == tutorial_id).first()
            if tutorial and tutorial.steps:
                total_steps = len(tutorial.steps)
                progress.completion_percentage = (len(completed_steps) / total_steps) * 100

                if progress.completion_percentage >= 100 and not progress.is_completed:
                    progress.is_completed = True
                    progress.completed_at = datetime.utcnow()

                    # Update tutorial completion count
                    tutorial.completion_count += 1

            self.db.commit()
            self.db.refresh(progress)

            return progress

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error tracking progress: {str(e)}")
            raise

    async def get_user_progress(
        self,
        user_id: UUID,
        tutorial_id: Optional[UUID] = None,
    ) -> List[TutorialProgress]:
        """Get user's tutorial progress."""
        try:
            query = self.db.query(TutorialProgress).filter(
                TutorialProgress.user_id == user_id
            )

            if tutorial_id:
                query = query.filter(TutorialProgress.tutorial_id == tutorial_id)

            return query.all()

        except Exception as e:
            logger.error(f"Error getting user progress: {str(e)}")
            raise

    def _generate_slug(self, title: str) -> str:
        """Generate URL slug from title."""
        import re

        slug = title.lower().strip()
        slug = re.sub(r"[^\w\s-]", "", slug)
        slug = re.sub(r"[-\s]+", "-", slug)

        base_slug = slug
        counter = 1
        while self.db.query(Tutorial).filter(Tutorial.slug == slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1

        return slug
