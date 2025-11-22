"""Audit logging for tracking important business events and user actions."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

import structlog


class AuditEventType(str, Enum):
    """Types of audit events."""

    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    PERMISSION_CHANGE = "permission_change"
    DATA_ACCESS = "data_access"
    DATA_CREATE = "data_create"
    DATA_UPDATE = "data_update"
    DATA_DELETE = "data_delete"
    CONFIG_CHANGE = "config_change"
    SECURITY_EVENT = "security_event"
    API_KEY_CREATE = "api_key_create"
    API_KEY_REVOKE = "api_key_revoke"
    EXPORT_DATA = "export_data"
    IMPORT_DATA = "import_data"


class AuditLogger:
    """Centralized audit logging for compliance and security tracking."""

    def __init__(self) -> None:
        """Initialize audit logger."""
        self.logger = structlog.get_logger("nexus.audit")

    def log(
        self,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        action: Optional[str] = None,
        status: str = "success",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Log an audit event.

        Args:
            event_type: Type of audit event
            user_id: User identifier
            user_email: User email address
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            action: Specific action performed
            status: Status of the action (success/failure)
            ip_address: IP address of the client
            user_agent: User agent string
            details: Additional event details
            **kwargs: Additional context fields
        """
        log_data = {
            "event_type": event_type.value,
            "timestamp": datetime.utcnow().isoformat(),
            "status": status,
        }

        if user_id:
            log_data["user_id"] = user_id
        if user_email:
            log_data["user_email"] = user_email
        if resource_type:
            log_data["resource_type"] = resource_type
        if resource_id:
            log_data["resource_id"] = resource_id
        if action:
            log_data["action"] = action
        if ip_address:
            log_data["ip_address"] = ip_address
        if user_agent:
            log_data["user_agent"] = user_agent
        if details:
            log_data["details"] = details

        # Add any additional context
        log_data.update(kwargs)

        self.logger.info("audit_event", **log_data)

    def log_user_login(
        self,
        user_id: str,
        user_email: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = "success",
        **kwargs: Any,
    ) -> None:
        """Log user login event.

        Args:
            user_id: User identifier
            user_email: User email address
            ip_address: IP address of the client
            user_agent: User agent string
            status: Login status (success/failure)
            **kwargs: Additional context
        """
        self.log(
            event_type=AuditEventType.USER_LOGIN,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            **kwargs,
        )

    def log_user_logout(
        self,
        user_id: str,
        user_email: str,
        **kwargs: Any,
    ) -> None:
        """Log user logout event.

        Args:
            user_id: User identifier
            user_email: User email address
            **kwargs: Additional context
        """
        self.log(
            event_type=AuditEventType.USER_LOGOUT,
            user_id=user_id,
            user_email=user_email,
            **kwargs,
        )

    def log_data_access(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str = "read",
        **kwargs: Any,
    ) -> None:
        """Log data access event.

        Args:
            user_id: User identifier
            resource_type: Type of resource accessed
            resource_id: ID of resource accessed
            action: Action performed (read/list/search)
            **kwargs: Additional context
        """
        self.log(
            event_type=AuditEventType.DATA_ACCESS,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            **kwargs,
        )

    def log_data_modification(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        changes: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Log data modification event.

        Args:
            user_id: User identifier
            resource_type: Type of resource modified
            resource_id: ID of resource modified
            action: Action performed (create/update/delete)
            changes: Details of changes made
            **kwargs: Additional context
        """
        event_type_map = {
            "create": AuditEventType.DATA_CREATE,
            "update": AuditEventType.DATA_UPDATE,
            "delete": AuditEventType.DATA_DELETE,
        }

        event_type = event_type_map.get(action.lower(), AuditEventType.DATA_UPDATE)

        self.log(
            event_type=event_type,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            details={"changes": changes} if changes else None,
            **kwargs,
        )

    def log_security_event(
        self,
        event_description: str,
        severity: str = "medium",
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Log security-related event.

        Args:
            event_description: Description of the security event
            severity: Severity level (low/medium/high/critical)
            user_id: User identifier if applicable
            ip_address: IP address if applicable
            **kwargs: Additional context
        """
        self.log(
            event_type=AuditEventType.SECURITY_EVENT,
            user_id=user_id,
            ip_address=ip_address,
            details={
                "description": event_description,
                "severity": severity,
            },
            **kwargs,
        )

    def log_config_change(
        self,
        user_id: str,
        config_key: str,
        old_value: Any,
        new_value: Any,
        **kwargs: Any,
    ) -> None:
        """Log configuration change.

        Args:
            user_id: User identifier
            config_key: Configuration key changed
            old_value: Previous value
            new_value: New value
            **kwargs: Additional context
        """
        self.log(
            event_type=AuditEventType.CONFIG_CHANGE,
            user_id=user_id,
            details={
                "config_key": config_key,
                "old_value": str(old_value),
                "new_value": str(new_value),
            },
            **kwargs,
        )
