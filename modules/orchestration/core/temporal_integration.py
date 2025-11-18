"""Temporal workflow integration for advanced orchestration."""

import asyncio
from datetime import timedelta
from typing import Dict, Any, Optional
from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker
import logging

from ..config.settings import settings
from .executor import TaskExecutionEngine

logger = logging.getLogger(__name__)


# Temporal Activities
@activity.defn
async def execute_task_activity(
    task_execution_id: int,
    task_type: str,
    task_config: Dict[str, Any],
    input_data: Dict[str, Any],
    max_retries: int = 3,
    retry_delay: int = 60,
    timeout: int = 3600,
) -> Dict[str, Any]:
    """
    Temporal activity for executing a task.

    Args:
        task_execution_id: Task execution database ID
        task_type: Type of task
        task_config: Task configuration
        input_data: Input data
        max_retries: Maximum retries
        retry_delay: Retry delay
        timeout: Timeout

    Returns:
        Task output data
    """
    engine = TaskExecutionEngine()

    try:
        result = await engine.execute_task(
            task_execution_id=task_execution_id,
            task_type=task_type,
            task_config=task_config,
            input_data=input_data,
            max_retries=max_retries,
            retry_delay=retry_delay,
            timeout=timeout,
        )
        return result
    except Exception as e:
        logger.error(f"Task execution failed: {e}")
        raise


# Temporal Workflow
@workflow.defn
class WorkflowOrchestrationWorkflow:
    """Temporal workflow for orchestrating tasks."""

    @workflow.run
    async def run(
        self,
        workflow_execution_id: int,
        dag_definition: Dict[str, Any],
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute workflow with Temporal.

        Args:
            workflow_execution_id: Workflow execution ID
            dag_definition: DAG definition
            input_data: Input data

        Returns:
            Workflow output
        """
        from ..core.dag import DAGEngine

        # Load DAG
        dag = DAGEngine.from_dict(dag_definition)

        # Get parallel execution groups
        parallel_groups = dag.get_parallel_groups()

        # Track task outputs
        task_outputs: Dict[str, Any] = {}

        # Execute groups sequentially
        for group in parallel_groups:
            # Execute tasks in parallel within group
            tasks = []

            for task_key in group:
                task_node = dag.tasks[task_key]

                # Prepare input from dependencies
                task_input = {"workflow_input": input_data}
                for dep in task_node.depends_on:
                    if dep in task_outputs:
                        task_input[dep] = task_outputs[dep]

                # Schedule activity
                task = workflow.execute_activity(
                    execute_task_activity,
                    args=[
                        0,  # Will be set by service
                        task_node.task_type,
                        task_node.config,
                        task_input,
                        task_node.retry_config.get("max_retries", 3),
                        task_node.retry_config.get("retry_delay", 60),
                        task_node.retry_config.get("timeout", 3600),
                    ],
                    start_to_close_timeout=timedelta(
                        seconds=task_node.retry_config.get("timeout", 3600)
                    ),
                    retry_policy=workflow.RetryPolicy(
                        maximum_attempts=task_node.retry_config.get("max_retries", 3),
                    ),
                )
                tasks.append((task_key, task))

            # Wait for all tasks in group
            for task_key, task in tasks:
                try:
                    result = await task
                    task_outputs[task_key] = result
                except Exception as e:
                    logger.error(f"Task {task_key} failed: {e}")
                    raise

        return task_outputs


class TemporalClient:
    """Client for Temporal integration."""

    def __init__(self):
        self.client: Optional[Client] = None
        self.worker: Optional[Worker] = None

    async def connect(self):
        """Connect to Temporal server."""
        try:
            self.client = await Client.connect(
                settings.TEMPORAL_HOST,
                namespace=settings.TEMPORAL_NAMESPACE,
            )
            logger.info("Connected to Temporal server")
        except Exception as e:
            logger.error(f"Failed to connect to Temporal: {e}")
            raise

    async def start_worker(self, task_queue: str = "nexus-orchestration"):
        """Start Temporal worker."""
        if not self.client:
            await self.connect()

        self.worker = Worker(
            self.client,
            task_queue=task_queue,
            workflows=[WorkflowOrchestrationWorkflow],
            activities=[execute_task_activity],
        )

        logger.info(f"Starting Temporal worker on task queue: {task_queue}")
        await self.worker.run()

    async def execute_workflow(
        self,
        workflow_id: str,
        workflow_execution_id: int,
        dag_definition: Dict[str, Any],
        input_data: Dict[str, Any],
    ) -> str:
        """
        Execute workflow using Temporal.

        Args:
            workflow_id: Workflow ID
            workflow_execution_id: Workflow execution ID
            dag_definition: DAG definition
            input_data: Input data

        Returns:
            Workflow run ID
        """
        if not self.client:
            await self.connect()

        handle = await self.client.start_workflow(
            WorkflowOrchestrationWorkflow.run,
            args=[workflow_execution_id, dag_definition, input_data],
            id=workflow_id,
            task_queue="nexus-orchestration",
        )

        logger.info(f"Started Temporal workflow: {handle.id}")
        return handle.id

    async def get_workflow_result(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get workflow result.

        Args:
            workflow_id: Workflow ID

        Returns:
            Workflow result
        """
        if not self.client:
            await self.connect()

        handle = self.client.get_workflow_handle(workflow_id)
        result = await handle.result()

        return result

    async def cancel_workflow(self, workflow_id: str):
        """Cancel workflow execution."""
        if not self.client:
            await self.connect()

        handle = self.client.get_workflow_handle(workflow_id)
        await handle.cancel()

        logger.info(f"Cancelled Temporal workflow: {workflow_id}")

    async def close(self):
        """Close Temporal client."""
        if self.client:
            await self.client.close()


# Global Temporal client
temporal_client = TemporalClient()
