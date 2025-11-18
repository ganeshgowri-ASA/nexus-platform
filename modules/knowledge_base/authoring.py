"""
Collaborative Authoring Module

Team collaboration, review workflows, and editorial calendar.
"""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from .models import ReviewWorkflow

logger = logging.getLogger(__name__)


class AuthoringManager:
    """Manager for collaborative authoring and workflows."""

    def __init__(self, db_session: Session):
        self.db = db_session

    async def submit_for_review(
        self,
        content_id: UUID,
        content_type: str,
    ) -> ReviewWorkflow:
        """Submit content for review."""
        try:
            workflow = ReviewWorkflow(
                content_id=content_id,
                content_type=content_type,
                status="pending",
            )

            self.db.add(workflow)
            self.db.commit()
            self.db.refresh(workflow)

            return workflow

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error submitting for review: {str(e)}")
            raise

    async def review_content(
        self,
        workflow_id: UUID,
        reviewer_id: UUID,
        approved: bool,
        comments: Optional[List[str]] = None,
        required_changes: Optional[List[str]] = None,
    ) -> ReviewWorkflow:
        """Review submitted content."""
        try:
            workflow = (
                self.db.query(ReviewWorkflow)
                .filter(ReviewWorkflow.id == workflow_id)
                .first()
            )

            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")

            workflow.reviewer_id = reviewer_id
            workflow.status = "approved" if approved else "rejected"
            workflow.comments = comments or []
            workflow.required_changes = required_changes or []
            workflow.reviewed_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(workflow)

            return workflow

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error reviewing content: {str(e)}")
            raise
