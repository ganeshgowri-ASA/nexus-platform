"""Tests for audit logging."""

import tempfile
from pathlib import Path

import pytest

from nexus.logging.audit import AuditEventType, AuditLogger
from nexus.logging.config import LogConfig, setup_logging


class TestAuditLogger:
    """Test audit logger."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test environment."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self.tmpdir = tmpdir
            config = LogConfig(log_dir=Path(tmpdir))
            setup_logging(config)
            self.audit_logger = AuditLogger()

    def test_audit_logger_initialization(self) -> None:
        """Test audit logger initialization."""
        assert self.audit_logger is not None
        assert self.audit_logger.logger.name == "nexus.audit"

    def test_log_user_login(self) -> None:
        """Test logging user login."""
        self.audit_logger.log_user_login(
            user_id="user123",
            user_email="user@example.com",
            ip_address="192.168.1.1",
            status="success",
        )

        # Verify log entry exists
        audit_log = Path(self.tmpdir) / "nexus.audit.log"
        assert audit_log.exists()

    def test_log_user_logout(self) -> None:
        """Test logging user logout."""
        self.audit_logger.log_user_logout(
            user_id="user123",
            user_email="user@example.com",
        )

    def test_log_data_access(self) -> None:
        """Test logging data access."""
        self.audit_logger.log_data_access(
            user_id="user123",
            resource_type="document",
            resource_id="doc456",
            action="read",
        )

    def test_log_data_modification(self) -> None:
        """Test logging data modification."""
        self.audit_logger.log_data_modification(
            user_id="user123",
            resource_type="document",
            resource_id="doc456",
            action="update",
            changes={"title": "New Title"},
        )

    def test_log_security_event(self) -> None:
        """Test logging security event."""
        self.audit_logger.log_security_event(
            event_description="Failed login attempt",
            severity="high",
            user_id="user123",
            ip_address="192.168.1.1",
        )

    def test_log_config_change(self) -> None:
        """Test logging configuration change."""
        self.audit_logger.log_config_change(
            user_id="admin123",
            config_key="max_file_size",
            old_value=10,
            new_value=20,
        )

    def test_audit_event_types(self) -> None:
        """Test audit event type enumeration."""
        assert AuditEventType.USER_LOGIN.value == "user_login"
        assert AuditEventType.USER_LOGOUT.value == "user_logout"
        assert AuditEventType.DATA_ACCESS.value == "data_access"
        assert AuditEventType.SECURITY_EVENT.value == "security_event"
