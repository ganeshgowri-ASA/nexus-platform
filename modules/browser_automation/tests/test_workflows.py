"""Tests for workflow functionality"""
import pytest
from modules.browser_automation.models import Workflow, WorkflowStep


@pytest.mark.asyncio
async def test_create_workflow(db_session, sample_workflow_data):
    """Test creating a workflow"""
    workflow = Workflow(
        name=sample_workflow_data["name"],
        description=sample_workflow_data["description"],
        is_active=sample_workflow_data["is_active"],
        headless=sample_workflow_data["headless"],
        browser_type=sample_workflow_data["browser_type"],
        timeout=sample_workflow_data["timeout"],
    )

    db_session.add(workflow)
    await db_session.flush()

    assert workflow.id is not None
    assert workflow.name == "Test Workflow"
    assert workflow.is_active is True


@pytest.mark.asyncio
async def test_create_workflow_with_steps(db_session, sample_workflow_data):
    """Test creating a workflow with steps"""
    workflow = Workflow(
        name=sample_workflow_data["name"],
        description=sample_workflow_data["description"],
        is_active=sample_workflow_data["is_active"],
        headless=sample_workflow_data["headless"],
        browser_type=sample_workflow_data["browser_type"],
        timeout=sample_workflow_data["timeout"],
    )

    db_session.add(workflow)
    await db_session.flush()

    # Add steps
    for step_data in sample_workflow_data["steps"]:
        step = WorkflowStep(
            workflow_id=workflow.id,
            **step_data
        )
        db_session.add(step)

    await db_session.commit()

    # Verify
    await db_session.refresh(workflow)
    assert len(workflow.steps) == 2
    assert workflow.steps[0].name == "Go to website"
    assert workflow.steps[1].name == "Extract title"


@pytest.mark.asyncio
async def test_workflow_update(db_session, sample_workflow_data):
    """Test updating a workflow"""
    workflow = Workflow(
        name=sample_workflow_data["name"],
        description=sample_workflow_data["description"],
        is_active=sample_workflow_data["is_active"],
        headless=sample_workflow_data["headless"],
        browser_type=sample_workflow_data["browser_type"],
        timeout=sample_workflow_data["timeout"],
    )

    db_session.add(workflow)
    await db_session.commit()

    # Update
    workflow.name = "Updated Workflow"
    workflow.is_active = False
    await db_session.commit()

    # Verify
    await db_session.refresh(workflow)
    assert workflow.name == "Updated Workflow"
    assert workflow.is_active is False
