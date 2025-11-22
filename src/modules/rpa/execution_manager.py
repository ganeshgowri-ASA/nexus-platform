"""
Execution Manager - Manages automation executions
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc

from src.database.models import (
    Automation,
    AutomationExecution,
    ExecutionStatus,
    TriggerType,
)
from src.utils.logger import get_logger
from src.utils.helpers import generate_id, current_timestamp

logger = get_logger(__name__)


class ExecutionManager:
    """Manages automation executions"""

    def __init__(self, db: Session):
        self.db = db

    def create_execution(
        self,
        automation_id: str,
        trigger_type: TriggerType,
        input_data: dict,
        triggered_by: str,
    ) -> AutomationExecution:
        """
        Create a new execution record

        Args:
            automation_id: ID of the automation to execute
            trigger_type: How the execution was triggered
            input_data: Input data for the execution
            triggered_by: User/system that triggered the execution

        Returns:
            AutomationExecution object
        """
        execution = AutomationExecution(
            id=generate_id(),
            automation_id=automation_id,
            trigger_type=trigger_type,
            status=ExecutionStatus.PENDING,
            input_data=input_data,
            triggered_by=triggered_by,
            created_at=current_timestamp(),
        )

        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)

        logger.info(
            f"Created execution {execution.id} for automation {automation_id}"
        )
        return execution

    def get_execution(self, execution_id: str) -> Optional[AutomationExecution]:
        """Get execution by ID"""
        return (
            self.db.query(AutomationExecution)
            .filter(AutomationExecution.id == execution_id)
            .first()
        )

    def list_executions(
        self,
        automation_id: Optional[str] = None,
        status: Optional[ExecutionStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[AutomationExecution]:
        """
        List executions with optional filtering

        Args:
            automation_id: Filter by automation ID
            status: Filter by execution status
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of AutomationExecution objects
        """
        query = self.db.query(AutomationExecution)

        if automation_id:
            query = query.filter(AutomationExecution.automation_id == automation_id)

        if status:
            query = query.filter(AutomationExecution.status == status)

        executions = (
            query.order_by(desc(AutomationExecution.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

        return executions

    def update_execution_status(
        self, execution_id: str, status: ExecutionStatus, error_message: str = None
    ) -> AutomationExecution:
        """Update execution status"""
        execution = self.get_execution(execution_id)
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")

        execution.status = status

        if status in [ExecutionStatus.SUCCESS, ExecutionStatus.FAILED]:
            execution.completed_at = current_timestamp()
            if execution.started_at:
                execution.duration = int(
                    (execution.completed_at - execution.started_at).total_seconds()
                )

        if error_message:
            execution.error_message = error_message

        self.db.commit()
        self.db.refresh(execution)

        logger.info(f"Updated execution {execution_id} status to {status}")
        return execution

    def cancel_execution(self, execution_id: str) -> AutomationExecution:
        """Cancel a running execution"""
        execution = self.get_execution(execution_id)
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")

        if execution.status not in [ExecutionStatus.PENDING, ExecutionStatus.RUNNING]:
            raise ValueError(
                f"Cannot cancel execution in status {execution.status}"
            )

        execution.status = ExecutionStatus.CANCELLED
        execution.completed_at = current_timestamp()
        if execution.started_at:
            execution.duration = int(
                (execution.completed_at - execution.started_at).total_seconds()
            )

        self.db.commit()
        self.db.refresh(execution)

        logger.info(f"Cancelled execution {execution_id}")
        return execution

    def get_execution_logs(self, execution_id: str) -> List[dict]:
        """Get execution logs"""
        execution = self.get_execution(execution_id)
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")

        return execution.logs or []

    def add_execution_log(
        self, execution_id: str, level: str, message: str, **kwargs
    ):
        """Add a log entry to an execution"""
        execution = self.get_execution(execution_id)
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")

        log_entry = {
            "timestamp": current_timestamp().isoformat(),
            "level": level,
            "message": message,
            **kwargs,
        }

        if execution.logs is None:
            execution.logs = []

        execution.logs.append(log_entry)
        self.db.commit()

    def get_execution_statistics(
        self, automation_id: Optional[str] = None
    ) -> dict:
        """Get execution statistics"""
        query = self.db.query(AutomationExecution)

        if automation_id:
            query = query.filter(AutomationExecution.automation_id == automation_id)

        total = query.count()
        success = query.filter(
            AutomationExecution.status == ExecutionStatus.SUCCESS
        ).count()
        failed = query.filter(
            AutomationExecution.status == ExecutionStatus.FAILED
        ).count()
        running = query.filter(
            AutomationExecution.status == ExecutionStatus.RUNNING
        ).count()
        pending = query.filter(
            AutomationExecution.status == ExecutionStatus.PENDING
        ).count()

        return {
            "total": total,
            "success": success,
            "failed": failed,
            "running": running,
            "pending": pending,
            "success_rate": (success / total * 100) if total > 0 else 0,
        }
