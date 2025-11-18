"""
Document workflow engine for Document Management System.

This module provides comprehensive workflow management including:
- Review workflows with configurable steps
- Approval chains with multiple approvers
- Routing logic with conditional transitions
- Task assignment with deadlines
- Workflow state management with persistence
- Workflow templates and versioning
"""

import json
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable

from sqlalchemy import and_, or_, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from backend.core.exceptions import (
    AuthorizationException,
    InvalidWorkflowStateException,
    ResourceNotFoundException,
    ValidationException,
    WorkflowApprovalException,
    WorkflowException,
    WorkflowNotFoundException,
)
from backend.core.logging import get_logger
from backend.models.document import (
    Document,
    DocumentStatus,
    DocumentWorkflow,
    WorkflowStep,
    WorkflowStatus,
)
from backend.models.user import User

logger = get_logger(__name__)


class WorkflowStepType(str, Enum):
    """Workflow step types."""

    APPROVAL = "approval"
    REVIEW = "review"
    ACKNOWLEDGMENT = "acknowledgment"
    TASK = "task"
    DECISION = "decision"
    NOTIFICATION = "notification"


class WorkflowTransitionCondition(str, Enum):
    """Workflow transition conditions."""

    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    TIMEOUT = "timeout"
    CUSTOM = "custom"


class WorkflowPriority(str, Enum):
    """Workflow priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class WorkflowStepDefinition:
    """
    Workflow step definition.

    Attributes:
        step_number: Step order number
        step_name: Step name
        step_type: Type of step
        assignee_id: Assigned user ID (or role)
        deadline_hours: Hours until deadline
        is_required: Whether step is mandatory
        allow_delegation: Allow assignee to delegate
        notify_assignee: Send notification to assignee
    """

    def __init__(
        self,
        step_number: int,
        step_name: str,
        step_type: WorkflowStepType,
        assignee_id: Optional[int] = None,
        deadline_hours: Optional[int] = None,
        is_required: bool = True,
        allow_delegation: bool = False,
        notify_assignee: bool = True,
    ) -> None:
        """Initialize step definition."""
        self.step_number = step_number
        self.step_name = step_name
        self.step_type = step_type
        self.assignee_id = assignee_id
        self.deadline_hours = deadline_hours
        self.is_required = is_required
        self.allow_delegation = allow_delegation
        self.notify_assignee = notify_assignee

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "step_number": self.step_number,
            "step_name": self.step_name,
            "step_type": self.step_type.value,
            "assignee_id": self.assignee_id,
            "deadline_hours": self.deadline_hours,
            "is_required": self.is_required,
            "allow_delegation": self.allow_delegation,
            "notify_assignee": self.notify_assignee,
        }


class WorkflowTemplate:
    """
    Reusable workflow template.

    Attributes:
        id: Template ID
        name: Template name
        description: Template description
        steps: List of step definitions
        is_active: Whether template is active
        created_by_id: Creator user ID
    """

    def __init__(
        self,
        name: str,
        description: str,
        steps: List[WorkflowStepDefinition],
        created_by_id: int,
        template_id: Optional[int] = None,
    ) -> None:
        """Initialize workflow template."""
        self.id = template_id
        self.name = name
        self.description = description
        self.steps = steps
        self.is_active = True
        self.created_by_id = created_by_id
        self.created_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "steps": [step.to_dict() for step in self.steps],
            "is_active": self.is_active,
            "created_by_id": self.created_by_id,
            "created_at": self.created_at.isoformat(),
        }


class WorkflowInstance:
    """
    Active workflow instance.

    Attributes:
        id: Workflow instance ID
        document_id: Document ID
        template: Workflow template
        status: Current workflow status
        current_step: Current step number
        initiated_by_id: User who started workflow
        priority: Workflow priority
        metadata: Additional workflow data
        started_at: Workflow start time
        completed_at: Workflow completion time
    """

    def __init__(
        self,
        document_id: int,
        template: WorkflowTemplate,
        initiated_by_id: int,
        priority: WorkflowPriority = WorkflowPriority.MEDIUM,
        workflow_id: Optional[int] = None,
    ) -> None:
        """Initialize workflow instance."""
        self.id = workflow_id
        self.document_id = document_id
        self.template = template
        self.status = WorkflowStatus.PENDING
        self.current_step = 1
        self.initiated_by_id = initiated_by_id
        self.priority = priority
        self.metadata: Dict[str, Any] = {}
        self.started_at = datetime.utcnow()
        self.completed_at: Optional[datetime] = None
        self.step_instances: List[WorkflowStepInstance] = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "template": self.template.to_dict(),
            "status": self.status.value,
            "current_step": self.current_step,
            "total_steps": len(self.template.steps),
            "initiated_by_id": self.initiated_by_id,
            "priority": self.priority.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "steps": [step.to_dict() for step in self.step_instances],
        }


class WorkflowStepInstance:
    """
    Workflow step instance.

    Attributes:
        workflow_id: Parent workflow ID
        definition: Step definition
        status: Step status
        assigned_to_id: Currently assigned user
        comments: Step comments
        decision: Approval decision
        completed_at: Completion timestamp
        deadline: Step deadline
    """

    def __init__(
        self,
        workflow_id: int,
        definition: WorkflowStepDefinition,
    ) -> None:
        """Initialize step instance."""
        self.workflow_id = workflow_id
        self.definition = definition
        self.status = WorkflowStatus.PENDING
        self.assigned_to_id = definition.assignee_id
        self.comments: Optional[str] = None
        self.decision: Optional[str] = None
        self.completed_at: Optional[datetime] = None
        self.started_at: Optional[datetime] = None
        self.deadline: Optional[datetime] = None

        # Calculate deadline if specified
        if definition.deadline_hours:
            self.deadline = datetime.utcnow() + timedelta(hours=definition.deadline_hours)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "step_number": self.definition.step_number,
            "step_name": self.definition.step_name,
            "step_type": self.definition.step_type.value,
            "status": self.status.value,
            "assigned_to_id": self.assigned_to_id,
            "comments": self.comments,
            "decision": self.decision,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "is_overdue": self.is_overdue(),
        }

    def is_overdue(self) -> bool:
        """Check if step is overdue."""
        if not self.deadline or self.status in [WorkflowStatus.APPROVED, WorkflowStatus.REJECTED]:
            return False
        return datetime.utcnow() > self.deadline


class WorkflowEngine:
    """
    Document workflow engine.

    Provides comprehensive workflow management including creation,
    execution, approval chains, routing, and state management.
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize workflow engine.

        Args:
            db: Database session
        """
        self.db = db
        self.logger = get_logger(self.__class__.__name__)
        self._templates: Dict[int, WorkflowTemplate] = {}
        self._workflows: Dict[int, WorkflowInstance] = {}

    # Template Management

    async def create_template(
        self,
        name: str,
        description: str,
        steps: List[WorkflowStepDefinition],
        created_by_id: int,
    ) -> WorkflowTemplate:
        """
        Create workflow template.

        Args:
            name: Template name
            description: Template description
            steps: List of step definitions
            created_by_id: Creator user ID

        Returns:
            Created template

        Raises:
            ValidationException: If validation fails
        """
        try:
            self.logger.info("creating_workflow_template", name=name)

            # Validate template
            self._validate_template(name, steps)

            # Create template
            template = WorkflowTemplate(
                name=name,
                description=description,
                steps=steps,
                created_by_id=created_by_id,
            )

            # TODO: Store in database
            template.id = len(self._templates) + 1
            self._templates[template.id] = template

            self.logger.info("template_created", template_id=template.id)

            return template

        except ValidationException:
            raise
        except Exception as e:
            self.logger.exception("create_template_failed", error=str(e))
            raise WorkflowException(f"Failed to create template: {str(e)}")

    async def get_template(self, template_id: int) -> WorkflowTemplate:
        """
        Get workflow template by ID.

        Args:
            template_id: Template ID

        Returns:
            Workflow template

        Raises:
            ResourceNotFoundException: If template not found
        """
        if template_id not in self._templates:
            # TODO: Fetch from database
            raise ResourceNotFoundException("Workflow template", template_id)

        return self._templates[template_id]

    async def list_templates(
        self,
        active_only: bool = True,
    ) -> List[WorkflowTemplate]:
        """
        List all workflow templates.

        Args:
            active_only: Only return active templates

        Returns:
            List of templates
        """
        templates = list(self._templates.values())

        if active_only:
            templates = [t for t in templates if t.is_active]

        return templates

    # Workflow Management

    async def start_workflow(
        self,
        document_id: int,
        template_id: int,
        initiated_by_id: int,
        priority: WorkflowPriority = WorkflowPriority.MEDIUM,
    ) -> WorkflowInstance:
        """
        Start a new workflow for a document.

        Args:
            document_id: Document ID
            template_id: Workflow template ID
            initiated_by_id: User starting workflow
            priority: Workflow priority

        Returns:
            Workflow instance

        Raises:
            ResourceNotFoundException: If document or template not found
            WorkflowException: If workflow start fails
        """
        try:
            self.logger.info(
                "starting_workflow",
                document_id=document_id,
                template_id=template_id,
            )

            # Verify document exists
            document = await self._get_document(document_id)

            # Get template
            template = await self.get_template(template_id)

            # Check for existing active workflow
            existing = await self._get_active_workflow(document_id)
            if existing:
                raise WorkflowException(
                    f"Document already has active workflow: {existing.id}"
                )

            # Create workflow instance
            workflow = WorkflowInstance(
                document_id=document_id,
                template=template,
                initiated_by_id=initiated_by_id,
                priority=priority,
            )

            # TODO: Store in database
            workflow.id = len(self._workflows) + 1
            self._workflows[workflow.id] = workflow

            # Create step instances
            for step_def in template.steps:
                step_instance = WorkflowStepInstance(
                    workflow_id=workflow.id,
                    definition=step_def,
                )
                workflow.step_instances.append(step_instance)

            # Start first step
            await self._start_step(workflow, 1)

            # Update document status
            await self._update_document_status(document_id, DocumentStatus.IN_REVIEW)

            self.logger.info("workflow_started", workflow_id=workflow.id)

            return workflow

        except (ResourceNotFoundException, WorkflowException):
            raise
        except Exception as e:
            self.logger.exception("start_workflow_failed", error=str(e))
            raise WorkflowException(f"Failed to start workflow: {str(e)}")

    async def get_workflow(self, workflow_id: int) -> WorkflowInstance:
        """
        Get workflow instance by ID.

        Args:
            workflow_id: Workflow ID

        Returns:
            Workflow instance

        Raises:
            WorkflowNotFoundException: If workflow not found
        """
        if workflow_id not in self._workflows:
            # TODO: Fetch from database
            raise WorkflowNotFoundException(workflow_id)

        return self._workflows[workflow_id]

    async def approve_step(
        self,
        workflow_id: int,
        step_number: int,
        user_id: int,
        comments: Optional[str] = None,
    ) -> WorkflowInstance:
        """
        Approve a workflow step.

        Args:
            workflow_id: Workflow ID
            step_number: Step number
            user_id: User approving
            comments: Optional comments

        Returns:
            Updated workflow

        Raises:
            WorkflowNotFoundException: If workflow not found
            AuthorizationException: If user not authorized
            InvalidWorkflowStateException: If step can't be approved
        """
        try:
            self.logger.info(
                "approving_step",
                workflow_id=workflow_id,
                step_number=step_number,
                user_id=user_id,
            )

            # Get workflow
            workflow = await self.get_workflow(workflow_id)

            # Validate state
            self._validate_workflow_state(workflow, step_number, user_id)

            # Get step instance
            step = workflow.step_instances[step_number - 1]

            # Approve step
            step.status = WorkflowStatus.APPROVED
            step.decision = "approved"
            step.comments = comments
            step.completed_at = datetime.utcnow()

            # TODO: Update in database

            # Advance to next step or complete workflow
            if step_number < len(workflow.template.steps):
                await self._advance_workflow(workflow)
            else:
                await self._complete_workflow(workflow, WorkflowStatus.APPROVED)

            self.logger.info("step_approved", workflow_id=workflow_id, step_number=step_number)

            return workflow

        except (WorkflowNotFoundException, AuthorizationException, InvalidWorkflowStateException):
            raise
        except Exception as e:
            self.logger.exception("approve_step_failed", error=str(e))
            raise WorkflowApprovalException(f"Step approval failed: {str(e)}")

    async def reject_step(
        self,
        workflow_id: int,
        step_number: int,
        user_id: int,
        reason: str,
    ) -> WorkflowInstance:
        """
        Reject a workflow step.

        Args:
            workflow_id: Workflow ID
            step_number: Step number
            user_id: User rejecting
            reason: Rejection reason

        Returns:
            Updated workflow

        Raises:
            WorkflowNotFoundException: If workflow not found
            AuthorizationException: If user not authorized
        """
        try:
            self.logger.info(
                "rejecting_step",
                workflow_id=workflow_id,
                step_number=step_number,
                user_id=user_id,
            )

            # Get workflow
            workflow = await self.get_workflow(workflow_id)

            # Validate state
            self._validate_workflow_state(workflow, step_number, user_id)

            # Get step instance
            step = workflow.step_instances[step_number - 1]

            # Reject step
            step.status = WorkflowStatus.REJECTED
            step.decision = "rejected"
            step.comments = reason
            step.completed_at = datetime.utcnow()

            # TODO: Update in database

            # Complete workflow as rejected
            await self._complete_workflow(workflow, WorkflowStatus.REJECTED)

            self.logger.info("step_rejected", workflow_id=workflow_id, step_number=step_number)

            return workflow

        except (WorkflowNotFoundException, AuthorizationException):
            raise
        except Exception as e:
            self.logger.exception("reject_step_failed", error=str(e))
            raise WorkflowApprovalException(f"Step rejection failed: {str(e)}")

    async def reassign_step(
        self,
        workflow_id: int,
        step_number: int,
        current_user_id: int,
        new_assignee_id: int,
    ) -> WorkflowInstance:
        """
        Reassign a workflow step to another user.

        Args:
            workflow_id: Workflow ID
            step_number: Step number
            current_user_id: Current assignee
            new_assignee_id: New assignee

        Returns:
            Updated workflow

        Raises:
            AuthorizationException: If reassignment not allowed
        """
        try:
            self.logger.info(
                "reassigning_step",
                workflow_id=workflow_id,
                step_number=step_number,
                new_assignee=new_assignee_id,
            )

            # Get workflow
            workflow = await self.get_workflow(workflow_id)

            # Get step
            step = workflow.step_instances[step_number - 1]

            # Check if current user can delegate
            if not step.definition.allow_delegation:
                raise AuthorizationException("Step delegation not allowed")

            if step.assigned_to_id != current_user_id:
                raise AuthorizationException("Only current assignee can reassign")

            # Reassign
            step.assigned_to_id = new_assignee_id

            # TODO: Update in database and notify new assignee

            self.logger.info("step_reassigned", workflow_id=workflow_id, step_number=step_number)

            return workflow

        except AuthorizationException:
            raise
        except Exception as e:
            self.logger.exception("reassign_step_failed", error=str(e))
            raise WorkflowException(f"Step reassignment failed: {str(e)}")

    async def cancel_workflow(
        self,
        workflow_id: int,
        user_id: int,
        reason: Optional[str] = None,
    ) -> WorkflowInstance:
        """
        Cancel an active workflow.

        Args:
            workflow_id: Workflow ID
            user_id: User canceling workflow
            reason: Cancellation reason

        Returns:
            Cancelled workflow

        Raises:
            WorkflowNotFoundException: If workflow not found
            AuthorizationException: If user not authorized
        """
        try:
            self.logger.info("canceling_workflow", workflow_id=workflow_id, user_id=user_id)

            # Get workflow
            workflow = await self.get_workflow(workflow_id)

            # Verify authorization (initiator or document owner)
            document = await self._get_document(workflow.document_id)
            if workflow.initiated_by_id != user_id and document.owner_id != user_id:
                raise AuthorizationException("Not authorized to cancel workflow")

            # Cancel workflow
            await self._complete_workflow(workflow, WorkflowStatus.CANCELLED)

            # Store cancellation reason
            workflow.metadata["cancellation_reason"] = reason
            workflow.metadata["cancelled_by"] = user_id

            self.logger.info("workflow_cancelled", workflow_id=workflow_id)

            return workflow

        except (WorkflowNotFoundException, AuthorizationException):
            raise
        except Exception as e:
            self.logger.exception("cancel_workflow_failed", error=str(e))
            raise WorkflowException(f"Workflow cancellation failed: {str(e)}")

    async def get_user_tasks(
        self,
        user_id: int,
        status_filter: Optional[WorkflowStatus] = None,
        overdue_only: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Get workflow tasks assigned to user.

        Args:
            user_id: User ID
            status_filter: Filter by status
            overdue_only: Only return overdue tasks

        Returns:
            List of task dictionaries
        """
        try:
            tasks = []

            for workflow in self._workflows.values():
                if workflow.status not in [WorkflowStatus.PENDING, WorkflowStatus.IN_PROGRESS]:
                    continue

                for step in workflow.step_instances:
                    if step.assigned_to_id != user_id:
                        continue

                    if status_filter and step.status != status_filter:
                        continue

                    if overdue_only and not step.is_overdue():
                        continue

                    tasks.append({
                        "workflow_id": workflow.id,
                        "document_id": workflow.document_id,
                        "step": step.to_dict(),
                        "priority": workflow.priority.value,
                    })

            return tasks

        except Exception as e:
            self.logger.exception("get_user_tasks_failed", error=str(e))
            return []

    # Private Helper Methods

    def _validate_template(self, name: str, steps: List[WorkflowStepDefinition]) -> None:
        """Validate workflow template."""
        if not name or len(name) < 3:
            raise ValidationException("Template name must be at least 3 characters")

        if not steps or len(steps) < 1:
            raise ValidationException("Template must have at least one step")

        # Validate step numbers are sequential
        for i, step in enumerate(steps, 1):
            if step.step_number != i:
                raise ValidationException(f"Step numbers must be sequential starting from 1")

    def _validate_workflow_state(
        self,
        workflow: WorkflowInstance,
        step_number: int,
        user_id: int,
    ) -> None:
        """Validate workflow state for action."""
        if workflow.status not in [WorkflowStatus.PENDING, WorkflowStatus.IN_PROGRESS]:
            raise InvalidWorkflowStateException(
                f"Workflow is {workflow.status.value}, cannot process step"
            )

        if workflow.current_step != step_number:
            raise InvalidWorkflowStateException(
                f"Current step is {workflow.current_step}, not {step_number}"
            )

        step = workflow.step_instances[step_number - 1]
        if step.assigned_to_id != user_id:
            raise AuthorizationException("Not assigned to this step")

        if step.status != WorkflowStatus.PENDING:
            raise InvalidWorkflowStateException(
                f"Step already {step.status.value}"
            )

    async def _start_step(self, workflow: WorkflowInstance, step_number: int) -> None:
        """Start a workflow step."""
        step = workflow.step_instances[step_number - 1]
        step.status = WorkflowStatus.PENDING
        step.started_at = datetime.utcnow()

        workflow.current_step = step_number
        workflow.status = WorkflowStatus.IN_PROGRESS

        # TODO: Send notification to assignee
        self.logger.debug("step_started", workflow_id=workflow.id, step_number=step_number)

    async def _advance_workflow(self, workflow: WorkflowInstance) -> None:
        """Advance workflow to next step."""
        next_step = workflow.current_step + 1
        await self._start_step(workflow, next_step)
        self.logger.debug("workflow_advanced", workflow_id=workflow.id, step=next_step)

    async def _complete_workflow(
        self,
        workflow: WorkflowInstance,
        final_status: WorkflowStatus,
    ) -> None:
        """Complete workflow with final status."""
        workflow.status = final_status
        workflow.completed_at = datetime.utcnow()

        # Update document status
        if final_status == WorkflowStatus.APPROVED:
            await self._update_document_status(workflow.document_id, DocumentStatus.APPROVED)
        elif final_status == WorkflowStatus.REJECTED:
            await self._update_document_status(workflow.document_id, DocumentStatus.REJECTED)
        else:
            await self._update_document_status(workflow.document_id, DocumentStatus.ACTIVE)

        self.logger.info(
            "workflow_completed",
            workflow_id=workflow.id,
            status=final_status.value,
        )

    async def _get_document(self, document_id: int) -> Document:
        """Get document by ID."""
        stmt = select(Document).where(Document.id == document_id)
        result = await self.db.execute(stmt)
        document = result.scalar_one_or_none()

        if not document:
            raise ResourceNotFoundException("Document", document_id)

        return document

    async def _update_document_status(
        self,
        document_id: int,
        status: DocumentStatus,
    ) -> None:
        """Update document status."""
        # TODO: Update in database
        self.logger.debug("document_status_updated", document_id=document_id, status=status.value)

    async def _get_active_workflow(self, document_id: int) -> Optional[WorkflowInstance]:
        """Get active workflow for document."""
        for workflow in self._workflows.values():
            if (
                workflow.document_id == document_id
                and workflow.status in [WorkflowStatus.PENDING, WorkflowStatus.IN_PROGRESS]
            ):
                return workflow
        return None
