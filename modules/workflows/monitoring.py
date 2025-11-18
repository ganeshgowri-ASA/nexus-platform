"""
NEXUS Workflow Monitoring
Comprehensive monitoring, logging, error handling, and alerting system
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, deque
import json
import asyncio


class LogLevel(Enum):
    """Log levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class LogEntry:
    """Log entry"""
    id: str
    workflow_id: str
    execution_id: Optional[str]
    node_id: Optional[str]
    level: LogLevel
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None


@dataclass
class ExecutionMetrics:
    """Metrics for workflow execution"""
    workflow_id: str
    execution_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    status: str = "running"
    nodes_executed: int = 0
    nodes_failed: int = 0
    nodes_skipped: int = 0
    retry_count: int = 0
    error_count: int = 0
    data_processed_bytes: int = 0
    api_calls_made: int = 0


@dataclass
class Alert:
    """Alert definition"""
    id: str
    name: str
    description: str
    severity: AlertSeverity
    condition: Dict[str, Any]
    channels: List[str]  # slack, email, webhook, etc.
    enabled: bool = True
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
    cooldown_minutes: int = 5


@dataclass
class ErrorRecord:
    """Error record"""
    id: str
    workflow_id: str
    execution_id: str
    node_id: Optional[str]
    error_type: str
    error_message: str
    stack_trace: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    retry_count: int = 0
    resolved: bool = False
    resolution_notes: Optional[str] = None


class WorkflowLogger:
    """Centralized logging system for workflows"""

    def __init__(self):
        self.logs: deque = deque(maxlen=10000)  # Keep last 10k logs in memory
        self.log_handlers: List[Callable] = []

    def add_handler(self, handler: Callable) -> None:
        """Add a log handler"""
        self.log_handlers.append(handler)

    def log(
        self,
        workflow_id: str,
        level: LogLevel,
        message: str,
        execution_id: Optional[str] = None,
        node_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        stack_trace: Optional[str] = None
    ) -> LogEntry:
        """Log a message"""
        import uuid

        entry = LogEntry(
            id=str(uuid.uuid4()),
            workflow_id=workflow_id,
            execution_id=execution_id,
            node_id=node_id,
            level=level,
            message=message,
            metadata=metadata or {},
            stack_trace=stack_trace
        )

        self.logs.append(entry)

        # Call handlers
        for handler in self.log_handlers:
            try:
                handler(entry)
            except Exception as e:
                print(f"Error in log handler: {e}")

        return entry

    def debug(self, workflow_id: str, message: str, **kwargs) -> LogEntry:
        """Log debug message"""
        return self.log(workflow_id, LogLevel.DEBUG, message, **kwargs)

    def info(self, workflow_id: str, message: str, **kwargs) -> LogEntry:
        """Log info message"""
        return self.log(workflow_id, LogLevel.INFO, message, **kwargs)

    def warning(self, workflow_id: str, message: str, **kwargs) -> LogEntry:
        """Log warning message"""
        return self.log(workflow_id, LogLevel.WARNING, message, **kwargs)

    def error(self, workflow_id: str, message: str, **kwargs) -> LogEntry:
        """Log error message"""
        return self.log(workflow_id, LogLevel.ERROR, message, **kwargs)

    def critical(self, workflow_id: str, message: str, **kwargs) -> LogEntry:
        """Log critical message"""
        return self.log(workflow_id, LogLevel.CRITICAL, message, **kwargs)

    def get_logs(
        self,
        workflow_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        level: Optional[LogLevel] = None,
        limit: int = 100
    ) -> List[LogEntry]:
        """Get logs with filters"""
        logs = list(self.logs)

        if workflow_id:
            logs = [l for l in logs if l.workflow_id == workflow_id]

        if execution_id:
            logs = [l for l in logs if l.execution_id == execution_id]

        if level:
            logs = [l for l in logs if l.level == level]

        # Sort by timestamp descending
        logs.sort(key=lambda x: x.timestamp, reverse=True)

        return logs[:limit]


class MetricsCollector:
    """Collects and aggregates workflow metrics"""

    def __init__(self):
        self.metrics: Dict[str, ExecutionMetrics] = {}
        self.aggregated_metrics: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "average_duration_ms": 0,
            "total_duration_ms": 0,
            "error_rate": 0.0
        })

    def start_execution(self, workflow_id: str, execution_id: str) -> ExecutionMetrics:
        """Start tracking execution"""
        metrics = ExecutionMetrics(
            workflow_id=workflow_id,
            execution_id=execution_id,
            start_time=datetime.utcnow()
        )

        self.metrics[execution_id] = metrics
        return metrics

    def end_execution(
        self,
        execution_id: str,
        status: str,
        error_count: int = 0
    ) -> Optional[ExecutionMetrics]:
        """End tracking execution"""
        metrics = self.metrics.get(execution_id)
        if not metrics:
            return None

        metrics.end_time = datetime.utcnow()
        metrics.duration_ms = (metrics.end_time - metrics.start_time).total_seconds() * 1000
        metrics.status = status
        metrics.error_count = error_count

        # Update aggregated metrics
        self._update_aggregated_metrics(metrics)

        return metrics

    def record_node_execution(
        self,
        execution_id: str,
        node_id: str,
        success: bool
    ) -> None:
        """Record node execution"""
        metrics = self.metrics.get(execution_id)
        if not metrics:
            return

        metrics.nodes_executed += 1
        if not success:
            metrics.nodes_failed += 1

    def record_retry(self, execution_id: str) -> None:
        """Record a retry"""
        metrics = self.metrics.get(execution_id)
        if metrics:
            metrics.retry_count += 1

    def _update_aggregated_metrics(self, metrics: ExecutionMetrics) -> None:
        """Update aggregated metrics"""
        agg = self.aggregated_metrics[metrics.workflow_id]

        agg["total_executions"] += 1
        agg["total_duration_ms"] += metrics.duration_ms or 0

        if metrics.status == "success":
            agg["successful_executions"] += 1
        elif metrics.status == "failed":
            agg["failed_executions"] += 1

        if agg["total_executions"] > 0:
            agg["average_duration_ms"] = agg["total_duration_ms"] / agg["total_executions"]
            agg["error_rate"] = agg["failed_executions"] / agg["total_executions"]

    def get_metrics(self, execution_id: str) -> Optional[ExecutionMetrics]:
        """Get metrics for execution"""
        return self.metrics.get(execution_id)

    def get_workflow_metrics(self, workflow_id: str) -> Dict[str, Any]:
        """Get aggregated metrics for workflow"""
        return dict(self.aggregated_metrics.get(workflow_id, {}))

    def get_all_workflow_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics for all workflows"""
        return dict(self.aggregated_metrics)


class ErrorHandler:
    """Handles errors and implements retry logic"""

    def __init__(self):
        self.errors: List[ErrorRecord] = []
        self.error_handlers: Dict[str, Callable] = {}

    def record_error(
        self,
        workflow_id: str,
        execution_id: str,
        error: Exception,
        node_id: Optional[str] = None
    ) -> ErrorRecord:
        """Record an error"""
        import uuid
        import traceback

        error_record = ErrorRecord(
            id=str(uuid.uuid4()),
            workflow_id=workflow_id,
            execution_id=execution_id,
            node_id=node_id,
            error_type=type(error).__name__,
            error_message=str(error),
            stack_trace=traceback.format_exc()
        )

        self.errors.append(error_record)

        # Call error handlers
        error_type = type(error).__name__
        if error_type in self.error_handlers:
            try:
                self.error_handlers[error_type](error_record)
            except Exception as e:
                print(f"Error in error handler: {e}")

        return error_record

    def register_error_handler(self, error_type: str, handler: Callable) -> None:
        """Register a handler for specific error type"""
        self.error_handlers[error_type] = handler

    def should_retry(
        self,
        error: Exception,
        retry_count: int,
        max_retries: int = 3
    ) -> bool:
        """Determine if operation should be retried"""
        if retry_count >= max_retries:
            return False

        # Don't retry certain error types
        non_retryable = [
            "ValueError",
            "TypeError",
            "KeyError",
            "AttributeError"
        ]

        if type(error).__name__ in non_retryable:
            return False

        return True

    async def retry_with_backoff(
        self,
        operation: Callable,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0
    ) -> Any:
        """Retry operation with exponential backoff"""
        delay = initial_delay

        for attempt in range(max_retries):
            try:
                return await operation()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise

                if not self.should_retry(e, attempt, max_retries):
                    raise

                await asyncio.sleep(delay)
                delay *= backoff_factor

    def get_errors(
        self,
        workflow_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        resolved: Optional[bool] = None,
        limit: int = 100
    ) -> List[ErrorRecord]:
        """Get errors with filters"""
        errors = self.errors.copy()

        if workflow_id:
            errors = [e for e in errors if e.workflow_id == workflow_id]

        if execution_id:
            errors = [e for e in errors if e.execution_id == execution_id]

        if resolved is not None:
            errors = [e for e in errors if e.resolved == resolved]

        # Sort by timestamp descending
        errors.sort(key=lambda x: x.timestamp, reverse=True)

        return errors[:limit]

    def resolve_error(self, error_id: str, notes: str) -> bool:
        """Mark error as resolved"""
        for error in self.errors:
            if error.id == error_id:
                error.resolved = True
                error.resolution_notes = notes
                return True
        return False


class AlertManager:
    """Manages alerts and notifications"""

    def __init__(self):
        self.alerts: Dict[str, Alert] = {}
        self.alert_handlers: Dict[str, Callable] = {}
        self.recent_triggers: deque = deque(maxlen=1000)

    def create_alert(
        self,
        name: str,
        description: str,
        severity: AlertSeverity,
        condition: Dict[str, Any],
        channels: List[str]
    ) -> Alert:
        """Create a new alert"""
        import uuid

        alert = Alert(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            severity=severity,
            condition=condition,
            channels=channels
        )

        self.alerts[alert.id] = alert
        return alert

    def register_alert_handler(self, channel: str, handler: Callable) -> None:
        """Register handler for alert channel"""
        self.alert_handlers[channel] = handler

    async def check_and_trigger_alerts(
        self,
        workflow_id: str,
        execution_id: str,
        metrics: ExecutionMetrics
    ) -> List[Alert]:
        """Check conditions and trigger alerts"""
        triggered_alerts = []

        for alert in self.alerts.values():
            if not alert.enabled:
                continue

            # Check cooldown
            if alert.last_triggered:
                time_since_trigger = datetime.utcnow() - alert.last_triggered
                if time_since_trigger < timedelta(minutes=alert.cooldown_minutes):
                    continue

            # Check condition
            if self._evaluate_alert_condition(alert.condition, metrics):
                await self._trigger_alert(alert, workflow_id, execution_id, metrics)
                triggered_alerts.append(alert)

        return triggered_alerts

    def _evaluate_alert_condition(
        self,
        condition: Dict[str, Any],
        metrics: ExecutionMetrics
    ) -> bool:
        """Evaluate alert condition"""
        condition_type = condition.get("type")

        if condition_type == "execution_failed":
            return metrics.status == "failed"

        elif condition_type == "duration_exceeded":
            threshold = condition.get("threshold_ms", 60000)
            return (metrics.duration_ms or 0) > threshold

        elif condition_type == "error_rate_exceeded":
            threshold = condition.get("threshold", 0.1)
            if metrics.nodes_executed > 0:
                error_rate = metrics.nodes_failed / metrics.nodes_executed
                return error_rate > threshold

        elif condition_type == "retry_limit_exceeded":
            threshold = condition.get("threshold", 3)
            return metrics.retry_count > threshold

        return False

    async def _trigger_alert(
        self,
        alert: Alert,
        workflow_id: str,
        execution_id: str,
        metrics: ExecutionMetrics
    ) -> None:
        """Trigger an alert"""
        alert.last_triggered = datetime.utcnow()
        alert.trigger_count += 1

        self.recent_triggers.append({
            "alert_id": alert.id,
            "alert_name": alert.name,
            "workflow_id": workflow_id,
            "execution_id": execution_id,
            "timestamp": alert.last_triggered,
            "severity": alert.severity.value
        })

        # Send to all channels
        for channel in alert.channels:
            handler = self.alert_handlers.get(channel)
            if handler:
                try:
                    await handler(alert, workflow_id, execution_id, metrics)
                except Exception as e:
                    print(f"Error sending alert to {channel}: {e}")

    def get_recent_alerts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent alert triggers"""
        return list(self.recent_triggers)[-limit:]


class WorkflowMonitor:
    """Main monitoring system that combines all monitoring components"""

    def __init__(self):
        self.logger = WorkflowLogger()
        self.metrics_collector = MetricsCollector()
        self.error_handler = ErrorHandler()
        self.alert_manager = AlertManager()

    async def start_execution_monitoring(
        self,
        workflow_id: str,
        execution_id: str
    ) -> ExecutionMetrics:
        """Start monitoring workflow execution"""
        self.logger.info(
            workflow_id,
            f"Starting execution {execution_id}",
            execution_id=execution_id
        )

        return self.metrics_collector.start_execution(workflow_id, execution_id)

    async def end_execution_monitoring(
        self,
        workflow_id: str,
        execution_id: str,
        status: str,
        error_count: int = 0
    ) -> ExecutionMetrics:
        """End monitoring workflow execution"""
        metrics = self.metrics_collector.end_execution(execution_id, status, error_count)

        self.logger.info(
            workflow_id,
            f"Execution {execution_id} completed with status: {status}",
            execution_id=execution_id,
            metadata={
                "duration_ms": metrics.duration_ms if metrics else None,
                "status": status
            }
        )

        # Check alerts
        if metrics:
            await self.alert_manager.check_and_trigger_alerts(
                workflow_id,
                execution_id,
                metrics
            )

        return metrics

    async def record_node_execution(
        self,
        workflow_id: str,
        execution_id: str,
        node_id: str,
        success: bool,
        error: Optional[Exception] = None
    ) -> None:
        """Record node execution"""
        self.metrics_collector.record_node_execution(execution_id, node_id, success)

        if not success and error:
            self.error_handler.record_error(workflow_id, execution_id, error, node_id)
            self.logger.error(
                workflow_id,
                f"Node {node_id} failed: {str(error)}",
                execution_id=execution_id,
                node_id=node_id
            )

    def get_dashboard_data(self, workflow_id: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        if workflow_id:
            workflow_metrics = self.metrics_collector.get_workflow_metrics(workflow_id)
            recent_errors = self.error_handler.get_errors(workflow_id=workflow_id, limit=10)
            recent_logs = self.logger.get_logs(workflow_id=workflow_id, limit=50)
        else:
            workflow_metrics = self.metrics_collector.get_all_workflow_metrics()
            recent_errors = self.error_handler.get_errors(limit=10)
            recent_logs = self.logger.get_logs(limit=50)

        return {
            "metrics": workflow_metrics,
            "recent_errors": [
                {
                    "id": e.id,
                    "workflow_id": e.workflow_id,
                    "error_type": e.error_type,
                    "error_message": e.error_message,
                    "timestamp": e.timestamp.isoformat(),
                    "resolved": e.resolved
                }
                for e in recent_errors
            ],
            "recent_logs": [
                {
                    "id": l.id,
                    "level": l.level.value,
                    "message": l.message,
                    "timestamp": l.timestamp.isoformat()
                }
                for l in recent_logs
            ],
            "recent_alerts": self.alert_manager.get_recent_alerts(limit=10)
        }


# Global monitoring instance
workflow_monitor = WorkflowMonitor()
