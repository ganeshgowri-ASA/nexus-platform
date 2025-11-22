"""
Comprehensive tests for NEXUS Workflow Automation Engine
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from .engine import (
    workflow_engine,
    NodeType,
    ExecutionStatus,
    WorkflowNode,
    NodeConnection,
    ConnectionType
)
from .triggers import trigger_manager, TriggerType
from .actions import action_executor, ActionType, ActionResult
from .scheduler import workflow_scheduler, ScheduleType
from .conditions import condition_evaluator, Condition, ConditionType
from .templates import template_library
from .integrations import integration_registry
from .monitoring import workflow_monitor


class TestWorkflowEngine:
    """Test workflow engine functionality"""

    def test_create_workflow(self):
        """Test creating a workflow"""
        workflow = workflow_engine.create_workflow(
            name="Test Workflow",
            description="A test workflow",
            nodes=[
                {
                    "name": "Trigger",
                    "type": "trigger",
                    "config": {"trigger_type": "manual"}
                },
                {
                    "name": "Action",
                    "type": "action",
                    "config": {"action_type": "log"}
                }
            ],
            connections=[
                {
                    "source_node_id": None,
                    "target_node_id": None
                }
            ]
        )

        assert workflow is not None
        assert workflow.name == "Test Workflow"
        assert len(workflow.nodes) == 2
        assert workflow.is_active is True

    def test_get_workflow(self):
        """Test retrieving a workflow"""
        workflow = workflow_engine.create_workflow(
            name="Test Get",
            description="Test",
            nodes=[],
            connections=[]
        )

        retrieved = workflow_engine.get_workflow(workflow.id)
        assert retrieved is not None
        assert retrieved.id == workflow.id

    def test_update_workflow(self):
        """Test updating a workflow"""
        workflow = workflow_engine.create_workflow(
            name="Original Name",
            description="Test",
            nodes=[],
            connections=[]
        )

        updated = workflow_engine.update_workflow(
            workflow.id,
            name="Updated Name",
            description="Updated description"
        )

        assert updated.name == "Updated Name"
        assert updated.description == "Updated description"
        assert updated.version == 2

    def test_delete_workflow(self):
        """Test deleting a workflow"""
        workflow = workflow_engine.create_workflow(
            name="To Delete",
            description="Test",
            nodes=[],
            connections=[]
        )

        deleted = workflow_engine.delete_workflow(workflow.id)
        assert deleted is True

        retrieved = workflow_engine.get_workflow(workflow.id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_execute_workflow(self):
        """Test executing a workflow"""
        workflow = workflow_engine.create_workflow(
            name="Execute Test",
            description="Test execution",
            nodes=[
                {
                    "name": "Trigger",
                    "type": "trigger",
                    "config": {}
                }
            ],
            connections=[]
        )

        execution = await workflow_engine.execute_workflow(
            workflow.id,
            trigger_data={"test": "data"}
        )

        assert execution is not None
        assert execution.workflow_id == workflow.id
        assert execution.status in [ExecutionStatus.SUCCESS, ExecutionStatus.FAILED]

    def test_export_workflow(self):
        """Test exporting a workflow"""
        workflow = workflow_engine.create_workflow(
            name="Export Test",
            description="Test",
            nodes=[],
            connections=[]
        )

        exported = workflow_engine.export_workflow(workflow.id)
        assert exported is not None
        assert "Export Test" in exported

    def test_import_workflow(self):
        """Test importing a workflow"""
        workflow_json = '''{
            "name": "Imported Workflow",
            "description": "Test import",
            "nodes": [],
            "connections": [],
            "variables": {},
            "tags": ["test"]
        }'''

        workflow = workflow_engine.import_workflow(workflow_json)
        assert workflow is not None
        assert workflow.name == "Imported Workflow"


class TestTriggers:
    """Test trigger functionality"""

    def test_register_trigger(self):
        """Test registering a trigger"""
        trigger_config = trigger_manager.register_trigger(
            workflow_id="test-workflow",
            trigger_type=TriggerType.WEBHOOK,
            config={
                "path": "/test-webhook",
                "method": "POST"
            }
        )

        assert trigger_config is not None
        assert trigger_config.trigger_type == TriggerType.WEBHOOK

    @pytest.mark.asyncio
    async def test_start_trigger(self):
        """Test starting a trigger"""
        trigger_config = trigger_manager.register_trigger(
            workflow_id="test-workflow",
            trigger_type=TriggerType.SCHEDULE,
            config={
                "interval": 60
            }
        )

        await trigger_manager.start_trigger(trigger_config.id)
        trigger = trigger_manager.get_trigger(trigger_config.id)

        assert trigger is not None
        assert trigger.is_active is True

    @pytest.mark.asyncio
    async def test_stop_trigger(self):
        """Test stopping a trigger"""
        trigger_config = trigger_manager.register_trigger(
            workflow_id="test-workflow",
            trigger_type=TriggerType.SCHEDULE,
            config={"interval": 60}
        )

        await trigger_manager.start_trigger(trigger_config.id)
        await trigger_manager.stop_trigger(trigger_config.id)

        trigger = trigger_manager.get_trigger(trigger_config.id)
        assert trigger.is_active is False

    def test_list_triggers(self):
        """Test listing triggers"""
        trigger_manager.register_trigger(
            workflow_id="workflow1",
            trigger_type=TriggerType.WEBHOOK,
            config={}
        )

        triggers = trigger_manager.list_triggers(workflow_id="workflow1")
        assert len(triggers) > 0


class TestActions:
    """Test action functionality"""

    @pytest.mark.asyncio
    async def test_execute_action(self):
        """Test executing an action"""
        result = await action_executor.execute_action(
            action_type=ActionType.LOG,
            config={"message": "Test log"},
            input_data={"test": "data"},
            context={}
        )

        assert result is not None
        assert isinstance(result, ActionResult)

    @pytest.mark.asyncio
    async def test_transform_data_action(self):
        """Test data transformation action"""
        result = await action_executor.execute_action(
            action_type=ActionType.TRANSFORM_DATA,
            config={
                "transformations": [
                    {"type": "rename", "from": "old_name", "to": "new_name"}
                ]
            },
            input_data={"old_name": "value"},
            context={}
        )

        assert result.success is True
        assert "new_name" in result.data

    @pytest.mark.asyncio
    async def test_delay_action(self):
        """Test delay action"""
        start = datetime.utcnow()

        result = await action_executor.execute_action(
            action_type=ActionType.DELAY,
            config={"duration": 1, "unit": "seconds"},
            input_data={},
            context={}
        )

        end = datetime.utcnow()
        duration = (end - start).total_seconds()

        assert result.success is True
        assert duration >= 1.0


class TestConditions:
    """Test condition evaluation"""

    def test_evaluate_equals_condition(self):
        """Test equals condition"""
        condition = Condition(
            field="status",
            operator=ConditionType.EQUALS,
            value="active"
        )

        result = condition_evaluator.evaluate(
            condition,
            {"status": "active"}
        )

        assert result is True

    def test_evaluate_greater_than_condition(self):
        """Test greater than condition"""
        condition = Condition(
            field="age",
            operator=ConditionType.GREATER_THAN,
            value=18
        )

        result = condition_evaluator.evaluate(
            condition,
            {"age": 25}
        )

        assert result is True

    def test_evaluate_contains_condition(self):
        """Test contains condition"""
        condition = Condition(
            field="tags",
            operator=ConditionType.CONTAINS,
            value="important"
        )

        result = condition_evaluator.evaluate(
            condition,
            {"tags": ["urgent", "important", "review"]}
        )

        assert result is True


class TestScheduler:
    """Test scheduler functionality"""

    def test_create_schedule(self):
        """Test creating a schedule"""
        schedule = workflow_scheduler.create_schedule(
            workflow_id="test-workflow",
            schedule_type=ScheduleType.CRON,
            cron_expression="0 9 * * *"
        )

        assert schedule is not None
        assert schedule.cron_expression == "0 9 * * *"

    def test_update_schedule(self):
        """Test updating a schedule"""
        schedule = workflow_scheduler.create_schedule(
            workflow_id="test-workflow",
            schedule_type=ScheduleType.INTERVAL,
            interval_seconds=3600
        )

        updated = workflow_scheduler.update_schedule(
            schedule.id,
            interval_seconds=7200
        )

        assert updated.interval_seconds == 7200

    def test_delete_schedule(self):
        """Test deleting a schedule"""
        schedule = workflow_scheduler.create_schedule(
            workflow_id="test-workflow",
            schedule_type=ScheduleType.ONE_TIME
        )

        deleted = workflow_scheduler.delete_schedule(schedule.id)
        assert deleted is True

    def test_pause_schedule(self):
        """Test pausing a schedule"""
        schedule = workflow_scheduler.create_schedule(
            workflow_id="test-workflow",
            schedule_type=ScheduleType.INTERVAL,
            interval_seconds=3600
        )

        paused = workflow_scheduler.pause_schedule(schedule.id)
        assert paused is True


class TestIntegrations:
    """Test integrations"""

    def test_list_integrations(self):
        """Test listing integrations"""
        integrations = integration_registry.list_integrations()
        assert len(integrations) > 0

    def test_get_integration(self):
        """Test getting an integration"""
        integration = integration_registry.get_integration("slack")
        assert integration is not None
        assert integration.name == "Slack"

    def test_create_connection(self):
        """Test creating an integration connection"""
        connection = integration_registry.create_connection(
            integration_id="slack",
            name="My Slack",
            credentials={"api_key": "test-key"}
        )

        assert connection is not None
        assert connection.integration_id == "slack"


class TestTemplates:
    """Test templates"""

    def test_get_template(self):
        """Test getting a template"""
        template = template_library.get_template("email-to-slack")
        assert template is not None
        assert template.name == "Email to Slack Notification"

    def test_list_templates(self):
        """Test listing templates"""
        templates = template_library.list_templates()
        assert len(templates) > 0

    def test_create_workflow_from_template(self):
        """Test creating workflow from template"""
        workflow_def = template_library.create_workflow_from_template(
            template_id="email-to-slack",
            name="My Email to Slack"
        )

        assert workflow_def is not None
        assert workflow_def["name"] == "My Email to Slack"

    def test_export_template(self):
        """Test exporting a template"""
        exported = template_library.export_template("email-to-slack")
        assert exported is not None
        assert "email-to-slack" in exported


class TestMonitoring:
    """Test monitoring functionality"""

    @pytest.mark.asyncio
    async def test_start_execution_monitoring(self):
        """Test starting execution monitoring"""
        metrics = await workflow_monitor.start_execution_monitoring(
            workflow_id="test-workflow",
            execution_id="test-execution"
        )

        assert metrics is not None
        assert metrics.workflow_id == "test-workflow"

    @pytest.mark.asyncio
    async def test_end_execution_monitoring(self):
        """Test ending execution monitoring"""
        await workflow_monitor.start_execution_monitoring(
            workflow_id="test-workflow",
            execution_id="test-execution"
        )

        metrics = await workflow_monitor.end_execution_monitoring(
            workflow_id="test-workflow",
            execution_id="test-execution",
            status="success"
        )

        assert metrics is not None
        assert metrics.status == "success"
        assert metrics.duration_ms is not None

    def test_get_dashboard_data(self):
        """Test getting dashboard data"""
        data = workflow_monitor.get_dashboard_data()

        assert data is not None
        assert "metrics" in data
        assert "recent_errors" in data
        assert "recent_logs" in data


# Integration tests
class TestWorkflowIntegration:
    """Integration tests for complete workflows"""

    @pytest.mark.asyncio
    async def test_simple_workflow_execution(self):
        """Test executing a simple workflow end-to-end"""
        # Create workflow
        workflow = workflow_engine.create_workflow(
            name="Simple Test",
            description="Simple test workflow",
            nodes=[
                {
                    "name": "Start",
                    "type": "trigger",
                    "config": {}
                },
                {
                    "name": "Log",
                    "type": "action",
                    "config": {"action_type": "log"}
                }
            ],
            connections=[
                {
                    "source_node_id": "start_id",
                    "target_node_id": "log_id"
                }
            ]
        )

        # Execute
        execution = await workflow_engine.execute_workflow(
            workflow.id,
            trigger_data={"message": "Test"}
        )

        assert execution is not None
        assert execution.workflow_id == workflow.id

    @pytest.mark.asyncio
    async def test_workflow_with_condition(self):
        """Test workflow with conditional branching"""
        workflow = workflow_engine.create_workflow(
            name="Conditional Test",
            description="Test conditional logic",
            nodes=[
                {
                    "name": "Trigger",
                    "type": "trigger",
                    "config": {}
                },
                {
                    "name": "Check Value",
                    "type": "condition",
                    "config": {
                        "field": "value",
                        "operator": "greater_than",
                        "value": 10
                    }
                },
                {
                    "name": "High Value Action",
                    "type": "action",
                    "config": {}
                },
                {
                    "name": "Low Value Action",
                    "type": "action",
                    "config": {}
                }
            ],
            connections=[]
        )

        execution = await workflow_engine.execute_workflow(
            workflow.id,
            trigger_data={"value": 15}
        )

        assert execution is not None


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
