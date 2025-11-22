"""
Audit logging system for RPA module
"""
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from src.database.models import AuditLog
from src.utils.logger import get_logger
from src.utils.helpers import generate_id, current_timestamp

logger = get_logger(__name__)


class AuditLogger:
    """Audit logger for RPA actions"""

    def __init__(self, db: Session):
        self.db = db

    def log(
        self,
        action: str,
        entity_type: str,
        entity_id: str,
        details: Dict[str, Any] = None,
        user_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        automation_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """
        Create an audit log entry

        Args:
            action: Action performed (e.g., "create", "update", "delete", "execute")
            entity_type: Type of entity (e.g., "automation", "bot", "schedule")
            entity_id: ID of the entity
            details: Additional details about the action
            user_id: User who performed the action
            execution_id: Related execution ID
            automation_id: Related automation ID
            ip_address: IP address of the request
            user_agent: User agent of the request

        Returns:
            AuditLog object
        """
        audit_log = AuditLog(
            id=generate_id(),
            execution_id=execution_id,
            automation_id=automation_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details or {},
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=current_timestamp(),
        )

        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)

        logger.info(
            f"Audit log created: {action} on {entity_type} {entity_id} by {user_id}"
        )
        return audit_log

    def get_logs(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        user_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        automation_id: Optional[str] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[AuditLog]:
        """
        Retrieve audit logs with filtering

        Args:
            entity_type: Filter by entity type
            entity_id: Filter by entity ID
            user_id: Filter by user ID
            execution_id: Filter by execution ID
            automation_id: Filter by automation ID
            action: Filter by action
            start_date: Filter logs after this date
            end_date: Filter logs before this date
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of AuditLog objects
        """
        query = self.db.query(AuditLog)

        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)

        if entity_id:
            query = query.filter(AuditLog.entity_id == entity_id)

        if user_id:
            query = query.filter(AuditLog.user_id == user_id)

        if execution_id:
            query = query.filter(AuditLog.execution_id == execution_id)

        if automation_id:
            query = query.filter(AuditLog.automation_id == automation_id)

        if action:
            query = query.filter(AuditLog.action == action)

        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)

        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)

        logs = (
            query.order_by(AuditLog.timestamp.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return logs

    def get_user_activity(
        self, user_id: str, days: int = 30
    ) -> List[AuditLog]:
        """
        Get user activity for the specified number of days

        Args:
            user_id: User ID
            days: Number of days to look back

        Returns:
            List of AuditLog objects
        """
        start_date = current_timestamp() - timedelta(days=days)

        return self.get_logs(user_id=user_id, start_date=start_date)

    def get_entity_history(
        self, entity_type: str, entity_id: str
    ) -> List[AuditLog]:
        """
        Get complete history for an entity

        Args:
            entity_type: Type of entity
            entity_id: Entity ID

        Returns:
            List of AuditLog objects
        """
        return self.get_logs(entity_type=entity_type, entity_id=entity_id)

    def get_execution_audit_trail(
        self, execution_id: str
    ) -> List[AuditLog]:
        """
        Get complete audit trail for an execution

        Args:
            execution_id: Execution ID

        Returns:
            List of AuditLog objects
        """
        return self.get_logs(execution_id=execution_id)

    def cleanup_old_logs(self, days: int = 90) -> int:
        """
        Delete audit logs older than specified days

        Args:
            days: Number of days to keep

        Returns:
            Number of deleted records
        """
        cutoff_date = current_timestamp() - timedelta(days=days)

        deleted = (
            self.db.query(AuditLog)
            .filter(AuditLog.timestamp < cutoff_date)
            .delete()
        )

        self.db.commit()

        logger.info(f"Cleaned up {deleted} audit logs older than {days} days")
        return deleted

    def get_statistics(
        self,
        entity_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get audit log statistics

        Args:
            entity_type: Filter by entity type
            start_date: Start date for statistics
            end_date: End date for statistics

        Returns:
            Dictionary with statistics
        """
        query = self.db.query(AuditLog)

        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)

        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)

        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)

        total_logs = query.count()

        # Count by action
        actions = {}
        for log in query.all():
            action = log.action
            actions[action] = actions.get(action, 0) + 1

        # Count by entity type
        entity_types = {}
        for log in query.all():
            etype = log.entity_type
            entity_types[etype] = entity_types.get(etype, 0) + 1

        return {
            "total_logs": total_logs,
            "actions": actions,
            "entity_types": entity_types,
            "date_range": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None,
            },
        }
