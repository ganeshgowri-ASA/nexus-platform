"""Audit logging example for NEXUS platform.

This example demonstrates:
- Audit logging for user actions
- Data access logging
- Security event logging
- Configuration change logging
"""

from pathlib import Path

from nexus.logging import AuditLogger, setup_logging, LogLevel
from nexus.logging.config import LogConfig


def main() -> None:
    """Run audit logging example."""
    # Set up logging
    config = LogConfig(
        log_dir=Path("logs"),
        log_level=LogLevel.INFO,
    )
    setup_logging(config)

    # Create audit logger
    audit = AuditLogger()

    # Log user login
    audit.log_user_login(
        user_id="user123",
        user_email="john.doe@example.com",
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        status="success",
    )

    # Log data access
    audit.log_data_access(
        user_id="user123",
        resource_type="document",
        resource_id="doc456",
        action="read",
    )

    # Log data modification
    audit.log_data_modification(
        user_id="user123",
        resource_type="document",
        resource_id="doc456",
        action="update",
        changes={
            "title": "Updated Document Title",
            "content_length": 1234,
        },
    )

    # Log security event
    audit.log_security_event(
        event_description="Multiple failed login attempts detected",
        severity="high",
        user_id="user789",
        ip_address="10.0.0.50",
        details={"attempt_count": 5, "time_window": "5 minutes"},
    )

    # Log configuration change
    audit.log_config_change(
        user_id="admin001",
        config_key="session_timeout",
        old_value=3600,
        new_value=7200,
    )

    # Log data deletion
    audit.log_data_modification(
        user_id="user123",
        resource_type="project",
        resource_id="proj789",
        action="delete",
    )

    # Log user logout
    audit.log_user_logout(
        user_id="user123",
        user_email="john.doe@example.com",
    )

    print("Audit logging examples completed. Check logs/nexus.audit.log")


if __name__ == "__main__":
    main()
