"""Monitoring and metrics collection"""
from typing import Dict, Any
from datetime import datetime
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
workflow_executions_total = Counter(
    'workflow_executions_total',
    'Total number of workflow executions',
    ['status', 'workflow_id']
)

workflow_execution_duration = Histogram(
    'workflow_execution_duration_seconds',
    'Workflow execution duration in seconds',
    ['workflow_id']
)

active_workflows = Gauge(
    'active_workflows_total',
    'Number of currently active workflows'
)

browser_sessions = Gauge(
    'browser_sessions_active',
    'Number of active browser sessions'
)

errors_total = Counter(
    'errors_total',
    'Total number of errors',
    ['error_type']
)


class MetricsCollector:
    """Collect and export metrics"""

    @staticmethod
    def record_workflow_execution(
        workflow_id: int,
        status: str,
        duration: float
    ):
        """Record workflow execution metrics"""
        workflow_executions_total.labels(
            status=status,
            workflow_id=str(workflow_id)
        ).inc()

        if duration > 0:
            workflow_execution_duration.labels(
                workflow_id=str(workflow_id)
            ).observe(duration)

        logger.info(
            f"Workflow {workflow_id} execution {status} in {duration:.2f}s"
        )

    @staticmethod
    def record_error(error_type: str, error_message: str):
        """Record error metrics"""
        errors_total.labels(error_type=error_type).inc()
        logger.error(f"{error_type}: {error_message}")

    @staticmethod
    def update_active_workflows(count: int):
        """Update active workflows gauge"""
        active_workflows.set(count)

    @staticmethod
    def update_browser_sessions(count: int):
        """Update browser sessions gauge"""
        browser_sessions.set(count)

    @staticmethod
    def get_metrics() -> bytes:
        """Get Prometheus metrics"""
        return generate_latest()

    @staticmethod
    def log_workflow_start(workflow_id: int, workflow_name: str):
        """Log workflow start"""
        logger.info(f"Starting workflow {workflow_id}: {workflow_name}")

    @staticmethod
    def log_workflow_complete(
        workflow_id: int,
        workflow_name: str,
        duration: float,
        success: bool
    ):
        """Log workflow completion"""
        status = "SUCCESS" if success else "FAILED"
        logger.info(
            f"Workflow {workflow_id} ({workflow_name}) completed: "
            f"{status} in {duration:.2f}s"
        )

    @staticmethod
    def log_step_execution(
        workflow_id: int,
        step_order: int,
        step_name: str,
        success: bool
    ):
        """Log step execution"""
        status = "✓" if success else "✗"
        logger.info(
            f"Workflow {workflow_id} - Step {step_order} ({step_name}): {status}"
        )


class ErrorHandler:
    """Centralized error handling"""

    @staticmethod
    def handle_workflow_error(
        workflow_id: int,
        step_order: int,
        error: Exception
    ) -> Dict[str, Any]:
        """Handle workflow execution error"""
        error_info = {
            "workflow_id": workflow_id,
            "step_order": step_order,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.utcnow().isoformat()
        }

        MetricsCollector.record_error(
            error_type=error_info["error_type"],
            error_message=error_info["error_message"]
        )

        logger.error(
            f"Workflow {workflow_id} failed at step {step_order}: "
            f"{error_info['error_type']} - {error_info['error_message']}"
        )

        return error_info

    @staticmethod
    def handle_browser_error(error: Exception) -> Dict[str, Any]:
        """Handle browser-specific errors"""
        error_info = {
            "error_type": "BrowserError",
            "error_message": str(error),
            "timestamp": datetime.utcnow().isoformat()
        }

        MetricsCollector.record_error(
            error_type="BrowserError",
            error_message=str(error)
        )

        return error_info
