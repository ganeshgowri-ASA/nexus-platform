"""
Comprehensive audit logging system for document management.

This module provides audit trail functionality including:
- Action logging for all document operations
- Access tracking
- Change history
- Compliance reporting
- Forensics support
- Data retention policies
"""

import json
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.core.config import get_settings
from backend.core.exceptions import NEXUSException, ResourceNotFoundException, ValidationException
from backend.core.logging import get_logger
from backend.models.document import Document, DocumentAuditLog
from backend.models.user import User

logger = get_logger(__name__)
settings = get_settings()


class AuditAction(str, Enum):
    """Enumeration of auditable actions."""

    # Document actions
    DOCUMENT_CREATED = "document.created"
    DOCUMENT_VIEWED = "document.viewed"
    DOCUMENT_DOWNLOADED = "document.downloaded"
    DOCUMENT_UPDATED = "document.updated"
    DOCUMENT_DELETED = "document.deleted"
    DOCUMENT_RESTORED = "document.restored"
    DOCUMENT_LOCKED = "document.locked"
    DOCUMENT_UNLOCKED = "document.unlocked"
    DOCUMENT_ARCHIVED = "document.archived"
    DOCUMENT_UNARCHIVED = "document.unarchived"

    # Version actions
    VERSION_CREATED = "version.created"
    VERSION_RESTORED = "version.restored"
    VERSION_DELETED = "version.deleted"
    VERSION_COMPARED = "version.compared"

    # Permission actions
    PERMISSION_GRANTED = "permission.granted"
    PERMISSION_REVOKED = "permission.revoked"
    PERMISSION_MODIFIED = "permission.modified"

    # Share actions
    SHARE_CREATED = "share.created"
    SHARE_ACCESSED = "share.accessed"
    SHARE_REVOKED = "share.revoked"

    # Metadata actions
    METADATA_ADDED = "metadata.added"
    METADATA_UPDATED = "metadata.updated"
    METADATA_DELETED = "metadata.deleted"

    # Folder actions
    FOLDER_CREATED = "folder.created"
    FOLDER_UPDATED = "folder.updated"
    FOLDER_DELETED = "folder.deleted"
    FOLDER_MOVED = "folder.moved"

    # Comment actions
    COMMENT_ADDED = "comment.added"
    COMMENT_UPDATED = "comment.updated"
    COMMENT_DELETED = "comment.deleted"
    COMMENT_RESOLVED = "comment.resolved"

    # Workflow actions
    WORKFLOW_INITIATED = "workflow.initiated"
    WORKFLOW_APPROVED = "workflow.approved"
    WORKFLOW_REJECTED = "workflow.rejected"
    WORKFLOW_COMPLETED = "workflow.completed"

    # Security actions
    ACCESS_DENIED = "security.access_denied"
    SUSPICIOUS_ACTIVITY = "security.suspicious_activity"
    BULK_OPERATION = "security.bulk_operation"


class AuditException(NEXUSException):
    """Exception raised for audit-related errors."""

    def __init__(self, message: str = "Audit operation failed", **kwargs: Any) -> None:
        super().__init__(message, status_code=500, **kwargs)


class AuditService:
    """
    Service for comprehensive audit logging.

    Provides audit trail functionality with support for compliance,
    forensics, and security monitoring.
    """

    def __init__(self, db_session: AsyncSession) -> None:
        """
        Initialize audit service.

        Args:
            db_session: Database session
        """
        self.db = db_session

    async def log_action(
        self,
        action: AuditAction,
        user_id: int,
        document_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> DocumentAuditLog:
        """
        Log an audit action.

        Args:
            action: Action being performed
            user_id: User performing the action
            document_id: Document ID (if applicable)
            details: Additional details about the action
            ip_address: User's IP address
            user_agent: User's browser/client user agent

        Returns:
            DocumentAuditLog: Created audit log entry
        """
        logger.info(
            "Logging audit action",
            action=action.value,
            user_id=user_id,
            document_id=document_id,
        )

        # Serialize details to JSON
        details_json = json.dumps(details) if details else None

        # Create audit log entry
        audit_log = DocumentAuditLog(
            document_id=document_id,
            user_id=user_id,
            action=action.value,
            details=details_json,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.add(audit_log)
        await self.db.commit()
        await self.db.refresh(audit_log)

        logger.debug(
            "Audit action logged",
            audit_log_id=audit_log.id,
            action=action.value,
        )

        return audit_log

    async def log_document_access(
        self,
        document_id: int,
        user_id: int,
        action: AuditAction,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        **extra_details: Any,
    ) -> DocumentAuditLog:
        """
        Log document access (view, download, etc.).

        Args:
            document_id: Document ID
            user_id: User accessing the document
            action: Type of access
            ip_address: User's IP address
            user_agent: User's browser/client user agent
            **extra_details: Additional details to log

        Returns:
            DocumentAuditLog: Created audit log entry
        """
        details = {
            "timestamp": datetime.utcnow().isoformat(),
            **extra_details,
        }

        return await self.log_action(
            action=action,
            user_id=user_id,
            document_id=document_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_document_modification(
        self,
        document_id: int,
        user_id: int,
        action: AuditAction,
        changes: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> DocumentAuditLog:
        """
        Log document modification.

        Args:
            document_id: Document ID
            user_id: User modifying the document
            action: Type of modification
            changes: Dictionary of changes (field -> value)
            ip_address: User's IP address
            user_agent: User's browser/client user agent

        Returns:
            DocumentAuditLog: Created audit log entry
        """
        details = {
            "timestamp": datetime.utcnow().isoformat(),
            "changes": changes,
        }

        return await self.log_action(
            action=action,
            user_id=user_id,
            document_id=document_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_permission_change(
        self,
        document_id: Optional[int],
        user_id: int,
        action: AuditAction,
        target_user_id: int,
        permission_details: Dict[str, Any],
        ip_address: Optional[str] = None,
    ) -> DocumentAuditLog:
        """
        Log permission change.

        Args:
            document_id: Document ID (if applicable)
            user_id: User making the change
            action: Type of permission action
            target_user_id: User whose permissions are being changed
            permission_details: Details about the permission change
            ip_address: User's IP address

        Returns:
            DocumentAuditLog: Created audit log entry
        """
        details = {
            "timestamp": datetime.utcnow().isoformat(),
            "target_user_id": target_user_id,
            **permission_details,
        }

        return await self.log_action(
            action=action,
            user_id=user_id,
            document_id=document_id,
            details=details,
            ip_address=ip_address,
        )

    async def log_security_event(
        self,
        action: AuditAction,
        user_id: int,
        document_id: Optional[int],
        reason: str,
        severity: str = "medium",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> DocumentAuditLog:
        """
        Log security event (access denied, suspicious activity, etc.).

        Args:
            action: Security action
            user_id: User involved in the event
            document_id: Document ID (if applicable)
            reason: Reason for the security event
            severity: Event severity (low, medium, high, critical)
            ip_address: User's IP address
            user_agent: User's browser/client user agent

        Returns:
            DocumentAuditLog: Created audit log entry
        """
        details = {
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason,
            "severity": severity,
            "event_type": "security",
        }

        audit_log = await self.log_action(
            action=action,
            user_id=user_id,
            document_id=document_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Also log to application logger for critical events
        if severity in ["high", "critical"]:
            logger.warning(
                "Security event logged",
                action=action.value,
                user_id=user_id,
                document_id=document_id,
                reason=reason,
                severity=severity,
            )

        return audit_log

    async def get_document_audit_trail(
        self,
        document_id: int,
        limit: int = 100,
        offset: int = 0,
        action_filter: Optional[List[AuditAction]] = None,
        user_id_filter: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[DocumentAuditLog]:
        """
        Get audit trail for a document.

        Args:
            document_id: Document ID
            limit: Maximum number of entries to return
            offset: Number of entries to skip
            action_filter: Filter by specific actions
            user_id_filter: Filter by specific user
            start_date: Filter entries after this date
            end_date: Filter entries before this date

        Returns:
            List[DocumentAuditLog]: List of audit log entries
        """
        logger.info(
            "Retrieving document audit trail",
            document_id=document_id,
            limit=limit,
            offset=offset,
        )

        # Build query
        query = select(DocumentAuditLog).where(DocumentAuditLog.document_id == document_id)

        # Apply filters
        if action_filter:
            action_values = [action.value for action in action_filter]
            query = query.where(DocumentAuditLog.action.in_(action_values))

        if user_id_filter:
            query = query.where(DocumentAuditLog.user_id == user_id_filter)

        if start_date:
            query = query.where(DocumentAuditLog.created_at >= start_date)

        if end_date:
            query = query.where(DocumentAuditLog.created_at <= end_date)

        # Order and paginate
        query = (
            query.order_by(desc(DocumentAuditLog.created_at))
            .limit(limit)
            .offset(offset)
            .options(selectinload(DocumentAuditLog.user))
        )

        result = await self.db.execute(query)
        audit_logs = result.scalars().all()

        logger.info(
            "Retrieved document audit trail",
            document_id=document_id,
            count=len(audit_logs),
        )

        return list(audit_logs)

    async def get_user_activity(
        self,
        user_id: int,
        limit: int = 100,
        offset: int = 0,
        action_filter: Optional[List[AuditAction]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[DocumentAuditLog]:
        """
        Get activity log for a user.

        Args:
            user_id: User ID
            limit: Maximum number of entries to return
            offset: Number of entries to skip
            action_filter: Filter by specific actions
            start_date: Filter entries after this date
            end_date: Filter entries before this date

        Returns:
            List[DocumentAuditLog]: List of audit log entries
        """
        logger.info(
            "Retrieving user activity",
            user_id=user_id,
            limit=limit,
            offset=offset,
        )

        # Build query
        query = select(DocumentAuditLog).where(DocumentAuditLog.user_id == user_id)

        # Apply filters
        if action_filter:
            action_values = [action.value for action in action_filter]
            query = query.where(DocumentAuditLog.action.in_(action_values))

        if start_date:
            query = query.where(DocumentAuditLog.created_at >= start_date)

        if end_date:
            query = query.where(DocumentAuditLog.created_at <= end_date)

        # Order and paginate
        query = (
            query.order_by(desc(DocumentAuditLog.created_at))
            .limit(limit)
            .offset(offset)
            .options(selectinload(DocumentAuditLog.document))
        )

        result = await self.db.execute(query)
        audit_logs = result.scalars().all()

        logger.info("Retrieved user activity", user_id=user_id, count=len(audit_logs))

        return list(audit_logs)

    async def get_activity_summary(
        self,
        document_id: Optional[int] = None,
        user_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get summary of activity.

        Args:
            document_id: Filter by document ID
            user_id: Filter by user ID
            start_date: Filter entries after this date
            end_date: Filter entries before this date

        Returns:
            Dict containing activity summary statistics
        """
        logger.info(
            "Generating activity summary",
            document_id=document_id,
            user_id=user_id,
        )

        # Build base query
        query = select(DocumentAuditLog)

        # Apply filters
        if document_id:
            query = query.where(DocumentAuditLog.document_id == document_id)

        if user_id:
            query = query.where(DocumentAuditLog.user_id == user_id)

        if start_date:
            query = query.where(DocumentAuditLog.created_at >= start_date)

        if end_date:
            query = query.where(DocumentAuditLog.created_at <= end_date)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        result = await self.db.execute(count_query)
        total_count = result.scalar()

        # Get action counts
        action_query = (
            select(DocumentAuditLog.action, func.count(DocumentAuditLog.id))
            .select_from(query.subquery())
            .group_by(DocumentAuditLog.action)
        )
        result = await self.db.execute(action_query)
        action_counts = dict(result.all())

        # Get date range
        result = await self.db.execute(query)
        logs = result.scalars().all()

        if logs:
            dates = [log.created_at for log in logs if log.created_at]
            date_range = {
                "earliest": min(dates).isoformat() if dates else None,
                "latest": max(dates).isoformat() if dates else None,
            }
        else:
            date_range = {"earliest": None, "latest": None}

        summary = {
            "total_actions": total_count,
            "action_counts": action_counts,
            "date_range": date_range,
            "filters": {
                "document_id": document_id,
                "user_id": user_id,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
            },
        }

        logger.info("Activity summary generated", total_actions=total_count)

        return summary

    async def generate_compliance_report(
        self,
        start_date: datetime,
        end_date: datetime,
        document_ids: Optional[List[int]] = None,
        user_ids: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """
        Generate compliance report for audit trail.

        Args:
            start_date: Report start date
            end_date: Report end date
            document_ids: Filter by specific documents
            user_ids: Filter by specific users

        Returns:
            Dict containing compliance report data
        """
        logger.info(
            "Generating compliance report",
            start_date=start_date,
            end_date=end_date,
        )

        # Build query
        query = select(DocumentAuditLog).where(
            and_(
                DocumentAuditLog.created_at >= start_date,
                DocumentAuditLog.created_at <= end_date,
            )
        )

        if document_ids:
            query = query.where(DocumentAuditLog.document_id.in_(document_ids))

        if user_ids:
            query = query.where(DocumentAuditLog.user_id.in_(user_ids))

        result = await self.db.execute(query)
        logs = result.scalars().all()

        # Categorize actions
        access_logs = []
        modification_logs = []
        permission_logs = []
        security_logs = []

        for log in logs:
            if log.action in [
                AuditAction.DOCUMENT_VIEWED.value,
                AuditAction.DOCUMENT_DOWNLOADED.value,
            ]:
                access_logs.append(log)
            elif log.action in [
                AuditAction.DOCUMENT_UPDATED.value,
                AuditAction.DOCUMENT_DELETED.value,
                AuditAction.VERSION_CREATED.value,
            ]:
                modification_logs.append(log)
            elif "permission" in log.action:
                permission_logs.append(log)
            elif "security" in log.action:
                security_logs.append(log)

        # Get unique users and documents
        unique_users = set(log.user_id for log in logs)
        unique_documents = set(log.document_id for log in logs if log.document_id)

        report = {
            "report_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "summary": {
                "total_actions": len(logs),
                "unique_users": len(unique_users),
                "unique_documents": len(unique_documents),
            },
            "categories": {
                "access_actions": len(access_logs),
                "modification_actions": len(modification_logs),
                "permission_actions": len(permission_logs),
                "security_actions": len(security_logs),
            },
            "security_events": [
                {
                    "id": log.id,
                    "action": log.action,
                    "user_id": log.user_id,
                    "document_id": log.document_id,
                    "timestamp": log.created_at.isoformat() if log.created_at else None,
                    "details": json.loads(log.details) if log.details else {},
                }
                for log in security_logs
            ],
            "generated_at": datetime.utcnow().isoformat(),
        }

        logger.info(
            "Compliance report generated",
            total_actions=len(logs),
            security_events=len(security_logs),
        )

        return report

    async def search_audit_logs(
        self,
        search_term: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[DocumentAuditLog]:
        """
        Search audit logs by term.

        Args:
            search_term: Term to search for in details
            limit: Maximum number of entries to return
            offset: Number of entries to skip

        Returns:
            List[DocumentAuditLog]: List of matching audit log entries
        """
        logger.info("Searching audit logs", search_term=search_term)

        # Search in details field
        query = (
            select(DocumentAuditLog)
            .where(DocumentAuditLog.details.contains(search_term))
            .order_by(desc(DocumentAuditLog.created_at))
            .limit(limit)
            .offset(offset)
            .options(
                selectinload(DocumentAuditLog.user),
                selectinload(DocumentAuditLog.document),
            )
        )

        result = await self.db.execute(query)
        audit_logs = result.scalars().all()

        logger.info("Audit logs search completed", count=len(audit_logs))

        return list(audit_logs)

    async def cleanup_old_logs(
        self,
        retention_days: Optional[int] = None,
        dry_run: bool = True,
    ) -> int:
        """
        Clean up old audit logs based on retention policy.

        Args:
            retention_days: Number of days to retain logs (default from settings)
            dry_run: If True, only count logs to be deleted without deleting

        Returns:
            int: Number of logs deleted (or would be deleted if dry_run)

        Note:
            Critical security logs are never deleted regardless of retention policy.
        """
        if retention_days is None:
            retention_days = settings.AUDIT_LOG_RETENTION_DAYS

        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

        logger.info(
            "Cleaning up old audit logs",
            retention_days=retention_days,
            cutoff_date=cutoff_date,
            dry_run=dry_run,
        )

        # Build query - exclude security events
        query = select(DocumentAuditLog).where(
            and_(
                DocumentAuditLog.created_at < cutoff_date,
                ~DocumentAuditLog.action.in_(
                    [
                        AuditAction.ACCESS_DENIED.value,
                        AuditAction.SUSPICIOUS_ACTIVITY.value,
                    ]
                ),
            )
        )

        result = await self.db.execute(query)
        logs_to_delete = result.scalars().all()
        count = len(logs_to_delete)

        if not dry_run:
            for log in logs_to_delete:
                await self.db.delete(log)
            await self.db.commit()

            logger.info("Old audit logs cleaned up", count=count)
        else:
            logger.info("Audit log cleanup dry run", count=count)

        return count

    async def export_audit_trail(
        self,
        document_id: Optional[int] = None,
        user_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        format: str = "json",
    ) -> str:
        """
        Export audit trail to a specific format.

        Args:
            document_id: Filter by document ID
            user_id: Filter by user ID
            start_date: Filter entries after this date
            end_date: Filter entries before this date
            format: Export format (json, csv)

        Returns:
            str: Exported data as string

        Raises:
            ValidationException: If format is not supported
        """
        logger.info(
            "Exporting audit trail",
            document_id=document_id,
            user_id=user_id,
            format=format,
        )

        # Get audit logs
        if document_id:
            logs = await self.get_document_audit_trail(
                document_id=document_id,
                limit=10000,
                start_date=start_date,
                end_date=end_date,
            )
        elif user_id:
            logs = await self.get_user_activity(
                user_id=user_id,
                limit=10000,
                start_date=start_date,
                end_date=end_date,
            )
        else:
            raise ValidationException("Must specify either document_id or user_id")

        # Convert to exportable format
        export_data = []
        for log in logs:
            export_data.append(
                {
                    "id": log.id,
                    "action": log.action,
                    "user_id": log.user_id,
                    "username": log.user.username if log.user else None,
                    "document_id": log.document_id,
                    "timestamp": log.created_at.isoformat() if log.created_at else None,
                    "details": json.loads(log.details) if log.details else {},
                    "ip_address": log.ip_address,
                    "user_agent": log.user_agent,
                }
            )

        # Format output
        if format == "json":
            output = json.dumps(export_data, indent=2)
        elif format == "csv":
            # Simple CSV format
            import csv
            import io

            output_io = io.StringIO()
            if export_data:
                writer = csv.DictWriter(output_io, fieldnames=export_data[0].keys())
                writer.writeheader()
                writer.writerows(export_data)
            output = output_io.getvalue()
        else:
            raise ValidationException(
                f"Unsupported export format: {format}",
                errors={"format": "Must be 'json' or 'csv'"},
            )

        logger.info("Audit trail exported", count=len(export_data), format=format)

        return output
