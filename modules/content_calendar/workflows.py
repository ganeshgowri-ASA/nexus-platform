"""
Workflow management module for approval workflows and assignments.

This module provides:
- Approval workflow creation and management
- Task assignments
- Status tracking
- Notifications
- Deadline management
"""
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from loguru import logger

from database import ContentItem, Assignment, Approval, User, ContentStatus, WorkflowStatus
from .calendar_types import (
    Workflow,
    WorkflowStep,
    ApprovalStatus,
    Notification,
    NotificationType,
)


class WorkflowManager:
    """Workflow manager for approval processes and assignments."""

    def __init__(self, db: Session):
        """
        Initialize workflow manager.

        Args:
            db: Database session
        """
        self.db = db
        self.notifications: list[Notification] = []
        logger.info("WorkflowManager initialized")

    def create_workflow(
        self,
        content_id: int,
        workflow_name: str,
        steps: list[dict],
        description: Optional[str] = None,
    ) -> Workflow:
        """
        Create approval workflow for content.

        Args:
            content_id: Content ID
            workflow_name: Workflow name
            steps: List of workflow steps
            description: Workflow description

        Returns:
            Created workflow
        """
        try:
            # Verify content exists
            content_item = (
                self.db.query(ContentItem)
                .filter(ContentItem.id == content_id)
                .first()
            )

            if not content_item:
                raise ValueError(f"Content {content_id} not found")

            # Create workflow steps
            workflow_steps = []
            for idx, step_data in enumerate(steps):
                # Create assignment
                assignment = Assignment(
                    content_item_id=content_id,
                    assignee_id=step_data["assignee_id"],
                    role=step_data.get("role", "reviewer"),
                    status=WorkflowStatus.PENDING,
                    due_date=step_data.get("deadline"),
                    notes=step_data.get("description"),
                )

                self.db.add(assignment)
                self.db.commit()
                self.db.refresh(assignment)

                workflow_step = WorkflowStep(
                    id=assignment.id,
                    name=step_data["name"],
                    description=step_data.get("description"),
                    order=idx,
                    assignee_id=step_data["assignee_id"],
                    role=step_data.get("role"),
                    status=ApprovalStatus.PENDING_REVIEW,
                    deadline=step_data.get("deadline"),
                )

                workflow_steps.append(workflow_step)

                # Send notification to assignee
                self._send_notification(
                    user_id=step_data["assignee_id"],
                    notification_type=NotificationType.ASSIGNMENT,
                    title="New Task Assignment",
                    message=f"You have been assigned: {step_data['name']}",
                    link=f"/content/{content_id}",
                )

            # Update content status
            content_item.status = ContentStatus.IN_REVIEW

            self.db.commit()

            workflow = Workflow(
                name=workflow_name,
                description=description,
                content_id=content_id,
                steps=workflow_steps,
                current_step=0,
                status=ApprovalStatus.PENDING_REVIEW,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            logger.info(f"Created workflow for content {content_id} with {len(workflow_steps)} steps")
            return workflow

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating workflow: {e}")
            raise

    def get_workflow(self, content_id: int) -> Optional[Workflow]:
        """
        Get workflow for content.

        Args:
            content_id: Content ID

        Returns:
            Workflow or None if not found
        """
        try:
            assignments = (
                self.db.query(Assignment)
                .filter(Assignment.content_item_id == content_id)
                .order_by(Assignment.created_at)
                .all()
            )

            if not assignments:
                return None

            # Convert assignments to workflow steps
            workflow_steps = []
            current_step = 0

            for idx, assignment in enumerate(assignments):
                workflow_step = WorkflowStep(
                    id=assignment.id,
                    name=assignment.role or "Review",
                    description=assignment.notes,
                    order=idx,
                    assignee_id=assignment.assignee_id,
                    role=assignment.role,
                    status=self._map_workflow_status(assignment.status),
                    deadline=assignment.due_date,
                    completed_at=assignment.updated_at if assignment.status == WorkflowStatus.COMPLETED else None,
                )
                workflow_steps.append(workflow_step)

                if assignment.status == WorkflowStatus.IN_PROGRESS:
                    current_step = idx

            # Determine overall status
            if all(s.status == ApprovalStatus.APPROVED for s in workflow_steps):
                overall_status = ApprovalStatus.APPROVED
            elif any(s.status == ApprovalStatus.REJECTED for s in workflow_steps):
                overall_status = ApprovalStatus.REJECTED
            else:
                overall_status = ApprovalStatus.IN_REVIEW

            workflow = Workflow(
                name="Content Approval",
                content_id=content_id,
                steps=workflow_steps,
                current_step=current_step,
                status=overall_status,
                created_at=assignments[0].created_at,
                updated_at=assignments[-1].updated_at,
            )

            return workflow

        except Exception as e:
            logger.error(f"Error getting workflow for content {content_id}: {e}")
            raise

    def advance_workflow(
        self,
        content_id: int,
        step_id: int,
        approved: bool,
        feedback: Optional[str] = None,
        reviewer_id: Optional[int] = None,
    ) -> Workflow:
        """
        Advance workflow to next step.

        Args:
            content_id: Content ID
            step_id: Current step ID (assignment ID)
            approved: Whether step is approved
            feedback: Reviewer feedback
            reviewer_id: Reviewer user ID

        Returns:
            Updated workflow
        """
        try:
            assignment = (
                self.db.query(Assignment)
                .filter(Assignment.id == step_id)
                .first()
            )

            if not assignment:
                raise ValueError(f"Assignment {step_id} not found")

            # Update assignment status
            if approved:
                assignment.status = WorkflowStatus.COMPLETED
                approval_status = WorkflowStatus.APPROVED
            else:
                assignment.status = WorkflowStatus.COMPLETED
                approval_status = WorkflowStatus.REJECTED

            assignment.updated_at = datetime.utcnow()

            # Create approval record
            if reviewer_id:
                approval = Approval(
                    content_item_id=content_id,
                    reviewer_id=reviewer_id,
                    status=approval_status,
                    feedback=feedback,
                    approved_at=datetime.utcnow() if approved else None,
                )
                self.db.add(approval)

            self.db.commit()

            # Get updated workflow
            workflow = self.get_workflow(content_id)

            if not workflow:
                raise ValueError(f"Workflow not found for content {content_id}")

            # Check if workflow is complete
            if approved:
                # Check if there are more steps
                next_steps = [
                    s for s in workflow.steps
                    if s.status == ApprovalStatus.PENDING_REVIEW
                ]

                if next_steps:
                    # Notify next assignee
                    next_step = next_steps[0]
                    self._send_notification(
                        user_id=next_step.assignee_id,
                        notification_type=NotificationType.REVIEW_REQUEST,
                        title="Review Required",
                        message=f"Content is ready for your review: {next_step.name}",
                        link=f"/content/{content_id}",
                    )
                else:
                    # All steps approved - update content status
                    content_item = (
                        self.db.query(ContentItem)
                        .filter(ContentItem.id == content_id)
                        .first()
                    )
                    if content_item:
                        content_item.status = ContentStatus.APPROVED
                        self.db.commit()

                    # Notify creator
                    self._send_notification(
                        user_id=content_item.creator_id,
                        notification_type=NotificationType.APPROVAL,
                        title="Content Approved",
                        message="Your content has been approved!",
                        link=f"/content/{content_id}",
                    )
            else:
                # Rejected - notify creator
                content_item = (
                    self.db.query(ContentItem)
                    .filter(ContentItem.id == content_id)
                    .first()
                )
                if content_item:
                    content_item.status = ContentStatus.DRAFT
                    self.db.commit()

                    self._send_notification(
                        user_id=content_item.creator_id,
                        notification_type=NotificationType.REJECTION,
                        title="Changes Requested",
                        message=f"Feedback: {feedback or 'Please review and update'}",
                        link=f"/content/{content_id}",
                    )

            logger.info(f"Advanced workflow for content {content_id}, approved={approved}")
            return workflow

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error advancing workflow: {e}")
            raise

    def assign_task(
        self,
        content_id: int,
        assignee_id: int,
        role: str,
        deadline: Optional[datetime] = None,
        notes: Optional[str] = None,
    ) -> dict:
        """
        Assign task to user.

        Args:
            content_id: Content ID
            assignee_id: User to assign to
            role: Role/task type
            deadline: Task deadline
            notes: Task notes

        Returns:
            Assignment data
        """
        try:
            assignment = Assignment(
                content_item_id=content_id,
                assignee_id=assignee_id,
                role=role,
                status=WorkflowStatus.PENDING,
                due_date=deadline,
                notes=notes,
            )

            self.db.add(assignment)
            self.db.commit()
            self.db.refresh(assignment)

            # Send notification
            self._send_notification(
                user_id=assignee_id,
                notification_type=NotificationType.ASSIGNMENT,
                title="New Assignment",
                message=f"You have been assigned: {role}",
                link=f"/content/{content_id}",
            )

            logger.info(f"Assigned task to user {assignee_id} for content {content_id}")

            return {
                "id": assignment.id,
                "content_id": content_id,
                "assignee_id": assignee_id,
                "role": role,
                "status": assignment.status.value,
                "deadline": deadline,
                "created_at": assignment.created_at,
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error assigning task: {e}")
            raise

    def get_user_assignments(
        self,
        user_id: int,
        status: Optional[WorkflowStatus] = None,
    ) -> list[dict]:
        """
        Get assignments for user.

        Args:
            user_id: User ID
            status: Filter by status

        Returns:
            List of assignments
        """
        try:
            query = self.db.query(Assignment).filter(
                Assignment.assignee_id == user_id
            )

            if status:
                query = query.filter(Assignment.status == status)

            assignments = query.order_by(Assignment.due_date).all()

            return [
                {
                    "id": a.id,
                    "content_id": a.content_item_id,
                    "role": a.role,
                    "status": a.status.value,
                    "due_date": a.due_date,
                    "notes": a.notes,
                    "created_at": a.created_at,
                }
                for a in assignments
            ]

        except Exception as e:
            logger.error(f"Error getting user assignments: {e}")
            raise

    def get_overdue_tasks(self) -> list[dict]:
        """
        Get overdue tasks.

        Returns:
            List of overdue assignments
        """
        try:
            now = datetime.utcnow()

            overdue = (
                self.db.query(Assignment)
                .filter(
                    and_(
                        Assignment.due_date < now,
                        Assignment.status.in_([
                            WorkflowStatus.PENDING,
                            WorkflowStatus.IN_PROGRESS,
                        ]),
                    )
                )
                .order_by(Assignment.due_date)
                .all()
            )

            return [
                {
                    "id": a.id,
                    "content_id": a.content_item_id,
                    "assignee_id": a.assignee_id,
                    "role": a.role,
                    "status": a.status.value,
                    "due_date": a.due_date,
                    "days_overdue": (now - a.due_date).days,
                }
                for a in overdue
            ]

        except Exception as e:
            logger.error(f"Error getting overdue tasks: {e}")
            raise

    def send_deadline_reminders(self, days_before: int = 1) -> int:
        """
        Send reminders for upcoming deadlines.

        Args:
            days_before: Send reminders this many days before deadline

        Returns:
            Number of reminders sent
        """
        try:
            now = datetime.utcnow()
            reminder_date = now + timedelta(days=days_before)

            upcoming = (
                self.db.query(Assignment)
                .filter(
                    and_(
                        Assignment.due_date >= now,
                        Assignment.due_date <= reminder_date,
                        Assignment.status.in_([
                            WorkflowStatus.PENDING,
                            WorkflowStatus.IN_PROGRESS,
                        ]),
                    )
                )
                .all()
            )

            for assignment in upcoming:
                self._send_notification(
                    user_id=assignment.assignee_id,
                    notification_type=NotificationType.DEADLINE,
                    title="Upcoming Deadline",
                    message=f"Task '{assignment.role}' is due soon",
                    link=f"/content/{assignment.content_item_id}",
                )

            logger.info(f"Sent {len(upcoming)} deadline reminders")
            return len(upcoming)

        except Exception as e:
            logger.error(f"Error sending deadline reminders: {e}")
            return 0

    def get_notifications(self, user_id: int, unread_only: bool = False) -> list[Notification]:
        """
        Get notifications for user.

        Args:
            user_id: User ID
            unread_only: Only return unread notifications

        Returns:
            List of notifications
        """
        # Filter user's notifications
        user_notifications = [
            n for n in self.notifications if n.user_id == user_id
        ]

        if unread_only:
            user_notifications = [n for n in user_notifications if not n.is_read]

        return sorted(user_notifications, key=lambda x: x.created_at, reverse=True)

    def mark_notification_read(self, notification_id: int) -> bool:
        """
        Mark notification as read.

        Args:
            notification_id: Notification ID

        Returns:
            True if marked successfully
        """
        for notification in self.notifications:
            if notification.id == notification_id:
                notification.is_read = True
                return True
        return False

    # Helper Methods
    def _send_notification(
        self,
        user_id: int,
        notification_type: NotificationType,
        title: str,
        message: str,
        link: Optional[str] = None,
    ) -> None:
        """Send notification to user."""
        notification = Notification(
            id=len(self.notifications) + 1,
            user_id=user_id,
            type=notification_type,
            title=title,
            message=message,
            link=link,
            is_read=False,
            created_at=datetime.utcnow(),
        )

        self.notifications.append(notification)
        logger.debug(f"Sent notification to user {user_id}: {title}")

    def _map_workflow_status(self, status: WorkflowStatus) -> ApprovalStatus:
        """Map WorkflowStatus to ApprovalStatus."""
        mapping = {
            WorkflowStatus.PENDING: ApprovalStatus.PENDING_REVIEW,
            WorkflowStatus.IN_PROGRESS: ApprovalStatus.IN_REVIEW,
            WorkflowStatus.APPROVED: ApprovalStatus.APPROVED,
            WorkflowStatus.REJECTED: ApprovalStatus.REJECTED,
            WorkflowStatus.COMPLETED: ApprovalStatus.APPROVED,
        }
        return mapping.get(status, ApprovalStatus.PENDING_REVIEW)
