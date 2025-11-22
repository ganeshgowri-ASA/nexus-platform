"""Task execution engine with retry logic and error handling."""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import traceback
import logging

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from ..db.models import (
    TaskExecution,
    TaskStatus,
    WorkflowExecution,
    WorkflowStatus,
)
from ..db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)


class TaskExecutionError(Exception):
    """Raised when task execution fails."""
    pass


class BaseTaskExecutor(ABC):
    """Base class for task executors."""

    def __init__(self, task_config: Dict[str, Any]):
        self.task_config = task_config

    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the task.

        Args:
            input_data: Input data for the task

        Returns:
            Output data from the task
        """
        pass

    async def validate_config(self) -> bool:
        """Validate task configuration."""
        return True


class PythonTaskExecutor(BaseTaskExecutor):
    """Executor for Python code tasks."""

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Python code."""
        code = self.task_config.get("code")
        if not code:
            raise TaskExecutionError("No code specified for Python task")

        # Create execution context
        context = {
            "input": input_data,
            "output": {},
        }

        try:
            # Execute the code
            exec(code, context)
            return context.get("output", {})
        except Exception as e:
            raise TaskExecutionError(f"Python execution failed: {str(e)}")


class HTTPTaskExecutor(BaseTaskExecutor):
    """Executor for HTTP request tasks."""

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute HTTP request."""
        import httpx

        method = self.task_config.get("method", "GET")
        url = self.task_config.get("url")
        headers = self.task_config.get("headers", {})
        params = self.task_config.get("params", {})
        json_data = self.task_config.get("json")
        timeout = self.task_config.get("timeout", 30)

        if not url:
            raise TaskExecutionError("No URL specified for HTTP task")

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_data or input_data,
                )
                response.raise_for_status()

                return {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "body": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                }
        except Exception as e:
            raise TaskExecutionError(f"HTTP request failed: {str(e)}")


class BashTaskExecutor(BaseTaskExecutor):
    """Executor for bash command tasks."""

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute bash command."""
        command = self.task_config.get("command")
        if not command:
            raise TaskExecutionError("No command specified for Bash task")

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            return {
                "return_code": process.returncode,
                "stdout": stdout.decode(),
                "stderr": stderr.decode(),
            }
        except Exception as e:
            raise TaskExecutionError(f"Bash execution failed: {str(e)}")


class SQLTaskExecutor(BaseTaskExecutor):
    """Executor for SQL query tasks."""

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute SQL query."""
        from sqlalchemy import text
        from ..db.session import AsyncSessionLocal

        query = self.task_config.get("query")
        if not query:
            raise TaskExecutionError("No query specified for SQL task")

        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(text(query))
                rows = result.fetchall()

                return {
                    "rows": [dict(row._mapping) for row in rows],
                    "row_count": len(rows),
                }
        except Exception as e:
            raise TaskExecutionError(f"SQL execution failed: {str(e)}")


# Executor registry
EXECUTOR_REGISTRY = {
    "python": PythonTaskExecutor,
    "http": HTTPTaskExecutor,
    "bash": BashTaskExecutor,
    "sql": SQLTaskExecutor,
}


def get_executor(task_type: str, task_config: Dict[str, Any]) -> BaseTaskExecutor:
    """Get executor for task type."""
    executor_class = EXECUTOR_REGISTRY.get(task_type)
    if not executor_class:
        raise TaskExecutionError(f"Unknown task type: {task_type}")
    return executor_class(task_config)


class TaskExecutionEngine:
    """
    Task execution engine with retry logic and error handling.

    Features:
    - Execute tasks with retry logic
    - Track execution state in database
    - Handle errors and timeouts
    - Support for different task types
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def execute_task(
        self,
        task_execution_id: int,
        task_type: str,
        task_config: Dict[str, Any],
        input_data: Dict[str, Any],
        max_retries: int = 3,
        retry_delay: int = 60,
        timeout: int = 3600,
    ) -> Dict[str, Any]:
        """
        Execute a task with retry logic.

        Args:
            task_execution_id: Task execution database ID
            task_type: Type of task to execute
            task_config: Task configuration
            input_data: Input data for the task
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            timeout: Task timeout in seconds

        Returns:
            Task output data
        """
        async with AsyncSessionLocal() as session:
            # Get task execution record
            task_execution = await session.get(TaskExecution, task_execution_id)
            if not task_execution:
                raise TaskExecutionError(f"Task execution {task_execution_id} not found")

            # Update status to running
            task_execution.status = TaskStatus.RUNNING
            task_execution.started_at = datetime.utcnow()
            await session.commit()

        # Get executor
        executor = get_executor(task_type, task_config)

        # Execute with retry logic
        retry_decorator = retry(
            stop=stop_after_attempt(max_retries),
            wait=wait_exponential(multiplier=1, min=retry_delay, max=retry_delay * 10),
            retry=retry_if_exception_type(TaskExecutionError),
            reraise=True,
        )

        @retry_decorator
        async def execute_with_retry():
            try:
                return await asyncio.wait_for(
                    executor.execute(input_data),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                raise TaskExecutionError(f"Task execution timed out after {timeout} seconds")

        try:
            # Execute task
            output_data = await execute_with_retry()

            # Update status to completed
            async with AsyncSessionLocal() as session:
                task_execution = await session.get(TaskExecution, task_execution_id)
                task_execution.status = TaskStatus.COMPLETED
                task_execution.completed_at = datetime.utcnow()
                task_execution.duration = (
                    task_execution.completed_at - task_execution.started_at
                ).total_seconds()
                task_execution.output_data = output_data
                await session.commit()

            self.logger.info(f"Task execution {task_execution_id} completed successfully")
            return output_data

        except Exception as e:
            # Update status to failed
            error_message = str(e)
            error_stack = traceback.format_exc()

            async with AsyncSessionLocal() as session:
                task_execution = await session.get(TaskExecution, task_execution_id)
                task_execution.status = TaskStatus.FAILED
                task_execution.completed_at = datetime.utcnow()
                task_execution.duration = (
                    task_execution.completed_at - task_execution.started_at
                ).total_seconds()
                task_execution.error_message = error_message
                task_execution.error_stack_trace = error_stack
                await session.commit()

            self.logger.error(f"Task execution {task_execution_id} failed: {error_message}")
            raise TaskExecutionError(error_message)


class WorkflowExecutionEngine:
    """
    Workflow execution engine.

    Features:
    - Execute workflows with DAG-based task scheduling
    - Parallel task execution
    - Error handling and recovery
    - State tracking
    """

    def __init__(self):
        self.task_engine = TaskExecutionEngine()
        self.logger = logging.getLogger(__name__)

    async def execute_workflow(
        self,
        workflow_execution_id: int,
        dag_definition: Dict[str, Any],
        input_data: Optional[Dict[str, Any]] = None,
        max_parallel_tasks: int = 10,
    ) -> Dict[str, Any]:
        """
        Execute a workflow.

        Args:
            workflow_execution_id: Workflow execution database ID
            dag_definition: DAG definition
            input_data: Input data for the workflow
            max_parallel_tasks: Maximum number of parallel tasks

        Returns:
            Workflow output data
        """
        from .dag import DAGEngine

        # Load DAG
        dag = DAGEngine.from_dict(dag_definition)

        # Validate DAG
        is_valid, error = dag.validate()
        if not is_valid:
            raise TaskExecutionError(f"Invalid DAG: {error}")

        # Get parallel execution groups
        parallel_groups = dag.get_parallel_groups()

        # Track task outputs
        task_outputs: Dict[str, Any] = {}

        # Execute groups sequentially, tasks within groups in parallel
        for group in parallel_groups:
            # Limit parallel execution
            semaphore = asyncio.Semaphore(max_parallel_tasks)

            async def execute_task_with_semaphore(task_key: str):
                async with semaphore:
                    return await self._execute_task_in_workflow(
                        workflow_execution_id,
                        task_key,
                        dag.tasks[task_key],
                        task_outputs,
                        input_data or {},
                    )

            # Execute tasks in parallel
            tasks = [execute_task_with_semaphore(task_key) for task_key in group]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Check for errors
            for i, result in enumerate(results):
                task_key = list(group)[i]
                if isinstance(result, Exception):
                    self.logger.error(f"Task {task_key} failed: {result}")
                    # Mark workflow as failed
                    async with AsyncSessionLocal() as session:
                        workflow_execution = await session.get(
                            WorkflowExecution, workflow_execution_id
                        )
                        workflow_execution.status = WorkflowStatus.FAILED
                        workflow_execution.error_message = str(result)
                        await session.commit()
                    raise result
                else:
                    task_outputs[task_key] = result

        # Mark workflow as completed
        async with AsyncSessionLocal() as session:
            workflow_execution = await session.get(
                WorkflowExecution, workflow_execution_id
            )
            workflow_execution.status = WorkflowStatus.COMPLETED
            workflow_execution.completed_at = datetime.utcnow()
            workflow_execution.duration = (
                workflow_execution.completed_at - workflow_execution.started_at
            ).total_seconds()
            workflow_execution.output_data = task_outputs
            await session.commit()

        self.logger.info(f"Workflow execution {workflow_execution_id} completed successfully")
        return task_outputs

    async def _execute_task_in_workflow(
        self,
        workflow_execution_id: int,
        task_key: str,
        task_node: Any,
        task_outputs: Dict[str, Any],
        workflow_input: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a single task within a workflow."""
        # Prepare input data from dependencies
        input_data = {"workflow_input": workflow_input}
        for dep in task_node.depends_on:
            if dep in task_outputs:
                input_data[dep] = task_outputs[dep]

        # Create task execution record
        async with AsyncSessionLocal() as session:
            task_execution = TaskExecution(
                workflow_execution_id=workflow_execution_id,
                task_id=None,  # Will be set if task is persisted
                execution_id=str(uuid.uuid4()),
                status=TaskStatus.PENDING,
                input_data=input_data,
            )
            session.add(task_execution)
            await session.commit()
            await session.refresh(task_execution)
            task_execution_id = task_execution.id

        # Execute task
        output_data = await self.task_engine.execute_task(
            task_execution_id=task_execution_id,
            task_type=task_node.task_type,
            task_config=task_node.config,
            input_data=input_data,
            max_retries=task_node.retry_config.get("max_retries", 3),
            retry_delay=task_node.retry_config.get("retry_delay", 60),
            timeout=task_node.retry_config.get("timeout", 3600),
        )

        return output_data
