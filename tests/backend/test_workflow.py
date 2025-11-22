"""
Unit tests for workflow engine.

Tests cover:
- Workflow template creation and management
- Workflow instance lifecycle
- Step approval and rejection
- Workflow state transitions
- Task assignment and reassignment
- Workflow cancellation
- User task retrieval
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from modules.documents.workflow import (
    WorkflowEngine,
    WorkflowTemplate,
    WorkflowInstance,
    WorkflowStepDefinition,
    WorkflowStepType,
    WorkflowPriority,
)
from backend.models.document import DocumentStatus, WorkflowStatus
from backend.core.exceptions import (
    ResourceNotFoundException,
    WorkflowException,
    WorkflowNotFoundException,
    AuthorizationException,
    InvalidWorkflowStateException,
    ValidationException,
)


@pytest.mark.unit
class TestWorkflowStepDefinition:
    """Test workflow step definition."""

    def test_step_definition_creation(self):
        """Test creating step definition."""
        step = WorkflowStepDefinition(
            step_number=1,
            step_name="Review",
            step_type=WorkflowStepType.REVIEW,
            assignee_id=123,
            deadline_hours=48,
            is_required=True,
        )

        assert step.step_number == 1
        assert step.step_name == "Review"
        assert step.step_type == WorkflowStepType.REVIEW
        assert step.assignee_id == 123
        assert step.deadline_hours == 48

    def test_step_definition_to_dict(self):
        """Test converting step definition to dictionary."""
        step = WorkflowStepDefinition(
            step_number=1,
            step_name="Approval",
            step_type=WorkflowStepType.APPROVAL,
        )

        step_dict = step.to_dict()

        assert step_dict["step_number"] == 1
        assert step_dict["step_name"] == "Approval"
        assert step_dict["step_type"] == "approval"


@pytest.mark.unit
class TestWorkflowTemplate:
    """Test workflow template."""

    def test_template_creation(self, regular_user):
        """Test creating workflow template."""
        steps = [
            WorkflowStepDefinition(1, "Review", WorkflowStepType.REVIEW),
            WorkflowStepDefinition(2, "Approve", WorkflowStepType.APPROVAL),
        ]

        template = WorkflowTemplate(
            name="Review and Approve",
            description="Standard review workflow",
            steps=steps,
            created_by_id=regular_user.id,
        )

        assert template.name == "Review and Approve"
        assert len(template.steps) == 2
        assert template.is_active is True

    def test_template_to_dict(self, regular_user):
        """Test converting template to dictionary."""
        steps = [WorkflowStepDefinition(1, "Review", WorkflowStepType.REVIEW)]
        template = WorkflowTemplate(
            name="Simple Workflow",
            description="Simple workflow",
            steps=steps,
            created_by_id=regular_user.id,
        )

        template_dict = template.to_dict()

        assert template_dict["name"] == "Simple Workflow"
        assert "steps" in template_dict
        assert len(template_dict["steps"]) == 1


@pytest.mark.unit
class TestWorkflowEngine:
    """Test workflow engine functionality."""

    @pytest.mark.asyncio
    async def test_create_template_success(self, db_session, regular_user):
        """Test creating workflow template."""
        engine = WorkflowEngine(db_session)
        steps = [
            WorkflowStepDefinition(1, "Step 1", WorkflowStepType.REVIEW),
            WorkflowStepDefinition(2, "Step 2", WorkflowStepType.APPROVAL),
        ]

        template = await engine.create_template(
            name="Test Workflow",
            description="Test workflow template",
            steps=steps,
            created_by_id=regular_user.id,
        )

        assert template.name == "Test Workflow"
        assert len(template.steps) == 2
        assert template.id is not None

    @pytest.mark.asyncio
    async def test_create_template_validates_name(self, db_session, regular_user):
        """Test that template creation validates name length."""
        engine = WorkflowEngine(db_session)
        steps = [WorkflowStepDefinition(1, "Step 1", WorkflowStepType.REVIEW)]

        with pytest.raises(ValidationException, match="at least 3 characters"):
            await engine.create_template(
                name="AB",  # Too short
                description="Test",
                steps=steps,
                created_by_id=regular_user.id,
            )

    @pytest.mark.asyncio
    async def test_create_template_requires_steps(self, db_session, regular_user):
        """Test that template requires at least one step."""
        engine = WorkflowEngine(db_session)

        with pytest.raises(ValidationException, match="at least one step"):
            await engine.create_template(
                name="Empty Workflow",
                description="No steps",
                steps=[],
                created_by_id=regular_user.id,
            )

    @pytest.mark.asyncio
    async def test_create_template_validates_step_numbers(
        self, db_session, regular_user
    ):
        """Test that template validates sequential step numbers."""
        engine = WorkflowEngine(db_session)
        steps = [
            WorkflowStepDefinition(1, "Step 1", WorkflowStepType.REVIEW),
            WorkflowStepDefinition(3, "Step 3", WorkflowStepType.APPROVAL),  # Skip 2
        ]

        with pytest.raises(ValidationException, match="sequential"):
            await engine.create_template(
                name="Invalid Steps",
                description="Non-sequential steps",
                steps=steps,
                created_by_id=regular_user.id,
            )

    @pytest.mark.asyncio
    async def test_get_template(self, db_session, regular_user):
        """Test retrieving workflow template."""
        engine = WorkflowEngine(db_session)
        steps = [WorkflowStepDefinition(1, "Review", WorkflowStepType.REVIEW)]

        created = await engine.create_template(
            name="Get Template Test",
            description="Test",
            steps=steps,
            created_by_id=regular_user.id,
        )

        retrieved = await engine.get_template(created.id)

        assert retrieved.id == created.id
        assert retrieved.name == created.name

    @pytest.mark.asyncio
    async def test_get_template_not_found(self, db_session):
        """Test that getting non-existent template raises exception."""
        engine = WorkflowEngine(db_session)

        with pytest.raises(ResourceNotFoundException):
            await engine.get_template(99999)

    @pytest.mark.asyncio
    async def test_list_templates(self, db_session, regular_user):
        """Test listing workflow templates."""
        engine = WorkflowEngine(db_session)
        steps = [WorkflowStepDefinition(1, "Review", WorkflowStepType.REVIEW)]

        # Create templates
        t1 = await engine.create_template(
            name="Template 1", description="Test", steps=steps,
            created_by_id=regular_user.id
        )
        t2 = await engine.create_template(
            name="Template 2", description="Test", steps=steps,
            created_by_id=regular_user.id
        )

        templates = await engine.list_templates()

        assert len(templates) >= 2
        template_ids = [t.id for t in templates]
        assert t1.id in template_ids
        assert t2.id in template_ids

    @pytest.mark.asyncio
    async def test_start_workflow_success(
        self, db_session, test_document, regular_user
    ):
        """Test starting a workflow."""
        engine = WorkflowEngine(db_session)

        # Create template
        steps = [
            WorkflowStepDefinition(
                1, "Review", WorkflowStepType.REVIEW,
                assignee_id=regular_user.id
            ),
        ]
        template = await engine.create_template(
            name="Test Workflow",
            description="Test",
            steps=steps,
            created_by_id=regular_user.id,
        )

        # Start workflow
        workflow = await engine.start_workflow(
            document_id=test_document.id,
            template_id=template.id,
            initiated_by_id=regular_user.id,
            priority=WorkflowPriority.MEDIUM,
        )

        assert workflow.document_id == test_document.id
        assert workflow.status == WorkflowStatus.IN_PROGRESS
        assert workflow.current_step == 1
        assert len(workflow.step_instances) == 1

    @pytest.mark.asyncio
    async def test_start_workflow_nonexistent_document(
        self, db_session, regular_user
    ):
        """Test that starting workflow for non-existent document fails."""
        engine = WorkflowEngine(db_session)
        steps = [WorkflowStepDefinition(1, "Review", WorkflowStepType.REVIEW)]

        template = await engine.create_template(
            name="Test", description="Test", steps=steps,
            created_by_id=regular_user.id
        )

        with pytest.raises(ResourceNotFoundException):
            await engine.start_workflow(
                document_id=99999,
                template_id=template.id,
                initiated_by_id=regular_user.id,
            )

    @pytest.mark.asyncio
    async def test_get_workflow(self, db_session, test_document, regular_user):
        """Test retrieving workflow instance."""
        engine = WorkflowEngine(db_session)

        # Create and start workflow
        steps = [WorkflowStepDefinition(
            1, "Review", WorkflowStepType.REVIEW,
            assignee_id=regular_user.id
        )]
        template = await engine.create_template(
            name="Test", description="Test", steps=steps,
            created_by_id=regular_user.id
        )
        started = await engine.start_workflow(
            document_id=test_document.id,
            template_id=template.id,
            initiated_by_id=regular_user.id,
        )

        # Retrieve workflow
        retrieved = await engine.get_workflow(started.id)

        assert retrieved.id == started.id
        assert retrieved.document_id == test_document.id

    @pytest.mark.asyncio
    async def test_approve_step_success(
        self, db_session, test_document, regular_user
    ):
        """Test approving a workflow step."""
        engine = WorkflowEngine(db_session)

        # Start workflow
        steps = [WorkflowStepDefinition(
            1, "Approval", WorkflowStepType.APPROVAL,
            assignee_id=regular_user.id
        )]
        template = await engine.create_template(
            name="Test", description="Test", steps=steps,
            created_by_id=regular_user.id
        )
        workflow = await engine.start_workflow(
            document_id=test_document.id,
            template_id=template.id,
            initiated_by_id=regular_user.id,
        )

        # Approve step
        updated = await engine.approve_step(
            workflow_id=workflow.id,
            step_number=1,
            user_id=regular_user.id,
            comments="Looks good",
        )

        # Workflow should be completed (only one step)
        assert updated.status == WorkflowStatus.APPROVED
        assert updated.step_instances[0].status == WorkflowStatus.APPROVED
        assert updated.completed_at is not None

    @pytest.mark.asyncio
    async def test_approve_step_advances_workflow(
        self, db_session, test_document, regular_user, other_user
    ):
        """Test that approving step advances to next step."""
        engine = WorkflowEngine(db_session)

        # Create two-step workflow
        steps = [
            WorkflowStepDefinition(
                1, "Step 1", WorkflowStepType.APPROVAL,
                assignee_id=regular_user.id
            ),
            WorkflowStepDefinition(
                2, "Step 2", WorkflowStepType.APPROVAL,
                assignee_id=other_user.id
            ),
        ]
        template = await engine.create_template(
            name="Two Steps", description="Test", steps=steps,
            created_by_id=regular_user.id
        )
        workflow = await engine.start_workflow(
            document_id=test_document.id,
            template_id=template.id,
            initiated_by_id=regular_user.id,
        )

        # Approve first step
        updated = await engine.approve_step(
            workflow_id=workflow.id,
            step_number=1,
            user_id=regular_user.id,
        )

        # Should advance to step 2
        assert updated.current_step == 2
        assert updated.status == WorkflowStatus.IN_PROGRESS
        assert updated.step_instances[0].status == WorkflowStatus.APPROVED
        assert updated.step_instances[1].status == WorkflowStatus.PENDING

    @pytest.mark.asyncio
    async def test_approve_step_not_assigned(
        self, db_session, test_document, regular_user, other_user
    ):
        """Test that non-assigned user cannot approve step."""
        engine = WorkflowEngine(db_session)

        steps = [WorkflowStepDefinition(
            1, "Review", WorkflowStepType.REVIEW,
            assignee_id=regular_user.id
        )]
        template = await engine.create_template(
            name="Test", description="Test", steps=steps,
            created_by_id=regular_user.id
        )
        workflow = await engine.start_workflow(
            document_id=test_document.id,
            template_id=template.id,
            initiated_by_id=regular_user.id,
        )

        # other_user tries to approve
        with pytest.raises(AuthorizationException, match="Not assigned"):
            await engine.approve_step(
                workflow_id=workflow.id,
                step_number=1,
                user_id=other_user.id,  # Wrong user
            )

    @pytest.mark.asyncio
    async def test_reject_step(
        self, db_session, test_document, regular_user
    ):
        """Test rejecting a workflow step."""
        engine = WorkflowEngine(db_session)

        steps = [WorkflowStepDefinition(
            1, "Approval", WorkflowStepType.APPROVAL,
            assignee_id=regular_user.id
        )]
        template = await engine.create_template(
            name="Test", description="Test", steps=steps,
            created_by_id=regular_user.id
        )
        workflow = await engine.start_workflow(
            document_id=test_document.id,
            template_id=template.id,
            initiated_by_id=regular_user.id,
        )

        # Reject step
        updated = await engine.reject_step(
            workflow_id=workflow.id,
            step_number=1,
            user_id=regular_user.id,
            reason="Not ready",
        )

        # Workflow should be rejected
        assert updated.status == WorkflowStatus.REJECTED
        assert updated.step_instances[0].status == WorkflowStatus.REJECTED
        assert updated.step_instances[0].comments == "Not ready"
        assert updated.completed_at is not None

    @pytest.mark.asyncio
    async def test_reassign_step(
        self, db_session, test_document, regular_user, other_user
    ):
        """Test reassigning a workflow step."""
        engine = WorkflowEngine(db_session)

        steps = [WorkflowStepDefinition(
            1, "Review", WorkflowStepType.REVIEW,
            assignee_id=regular_user.id,
            allow_delegation=True,  # Allow reassignment
        )]
        template = await engine.create_template(
            name="Test", description="Test", steps=steps,
            created_by_id=regular_user.id
        )
        workflow = await engine.start_workflow(
            document_id=test_document.id,
            template_id=template.id,
            initiated_by_id=regular_user.id,
        )

        # Reassign to other_user
        updated = await engine.reassign_step(
            workflow_id=workflow.id,
            step_number=1,
            current_user_id=regular_user.id,
            new_assignee_id=other_user.id,
        )

        assert updated.step_instances[0].assigned_to_id == other_user.id

    @pytest.mark.asyncio
    async def test_reassign_step_delegation_not_allowed(
        self, db_session, test_document, regular_user, other_user
    ):
        """Test that reassignment fails if delegation not allowed."""
        engine = WorkflowEngine(db_session)

        steps = [WorkflowStepDefinition(
            1, "Review", WorkflowStepType.REVIEW,
            assignee_id=regular_user.id,
            allow_delegation=False,  # Don't allow
        )]
        template = await engine.create_template(
            name="Test", description="Test", steps=steps,
            created_by_id=regular_user.id
        )
        workflow = await engine.start_workflow(
            document_id=test_document.id,
            template_id=template.id,
            initiated_by_id=regular_user.id,
        )

        with pytest.raises(AuthorizationException, match="delegation not allowed"):
            await engine.reassign_step(
                workflow_id=workflow.id,
                step_number=1,
                current_user_id=regular_user.id,
                new_assignee_id=other_user.id,
            )

    @pytest.mark.asyncio
    async def test_cancel_workflow(
        self, db_session, test_document, regular_user
    ):
        """Test cancelling an active workflow."""
        engine = WorkflowEngine(db_session)

        steps = [WorkflowStepDefinition(
            1, "Review", WorkflowStepType.REVIEW,
            assignee_id=regular_user.id
        )]
        template = await engine.create_template(
            name="Test", description="Test", steps=steps,
            created_by_id=regular_user.id
        )
        workflow = await engine.start_workflow(
            document_id=test_document.id,
            template_id=template.id,
            initiated_by_id=regular_user.id,
        )

        # Cancel workflow
        cancelled = await engine.cancel_workflow(
            workflow_id=workflow.id,
            user_id=regular_user.id,
            reason="No longer needed",
        )

        assert cancelled.status == WorkflowStatus.CANCELLED
        assert cancelled.completed_at is not None
        assert "cancellation_reason" in cancelled.metadata

    @pytest.mark.asyncio
    async def test_cancel_workflow_requires_authorization(
        self, db_session, test_document, regular_user, other_user
    ):
        """Test that only initiator or owner can cancel workflow."""
        engine = WorkflowEngine(db_session)

        steps = [WorkflowStepDefinition(
            1, "Review", WorkflowStepType.REVIEW,
            assignee_id=regular_user.id
        )]
        template = await engine.create_template(
            name="Test", description="Test", steps=steps,
            created_by_id=regular_user.id
        )
        workflow = await engine.start_workflow(
            document_id=test_document.id,
            template_id=template.id,
            initiated_by_id=regular_user.id,
        )

        # other_user tries to cancel
        with pytest.raises(AuthorizationException, match="Not authorized"):
            await engine.cancel_workflow(
                workflow_id=workflow.id,
                user_id=other_user.id,
            )

    @pytest.mark.asyncio
    async def test_get_user_tasks(
        self, db_session, test_document, regular_user
    ):
        """Test retrieving tasks assigned to user."""
        engine = WorkflowEngine(db_session)

        # Start workflow with task for regular_user
        steps = [WorkflowStepDefinition(
            1, "My Task", WorkflowStepType.REVIEW,
            assignee_id=regular_user.id
        )]
        template = await engine.create_template(
            name="Test", description="Test", steps=steps,
            created_by_id=regular_user.id
        )
        workflow = await engine.start_workflow(
            document_id=test_document.id,
            template_id=template.id,
            initiated_by_id=regular_user.id,
        )

        # Get user tasks
        tasks = await engine.get_user_tasks(regular_user.id)

        assert len(tasks) >= 1
        assert any(t["workflow_id"] == workflow.id for t in tasks)

    @pytest.mark.asyncio
    async def test_get_user_tasks_filters_completed(
        self, db_session, test_document, regular_user
    ):
        """Test that completed workflows don't show in tasks."""
        engine = WorkflowEngine(db_session)

        # Start and complete workflow
        steps = [WorkflowStepDefinition(
            1, "Task", WorkflowStepType.APPROVAL,
            assignee_id=regular_user.id
        )]
        template = await engine.create_template(
            name="Test", description="Test", steps=steps,
            created_by_id=regular_user.id
        )
        workflow = await engine.start_workflow(
            document_id=test_document.id,
            template_id=template.id,
            initiated_by_id=regular_user.id,
        )

        # Complete workflow
        await engine.approve_step(
            workflow_id=workflow.id,
            step_number=1,
            user_id=regular_user.id,
        )

        # Get tasks - completed workflow shouldn't appear
        tasks = await engine.get_user_tasks(regular_user.id)

        # Completed workflow should not be in tasks
        task_workflow_ids = [t["workflow_id"] for t in tasks]
        assert workflow.id not in task_workflow_ids


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
