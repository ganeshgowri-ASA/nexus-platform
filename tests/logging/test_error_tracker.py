"""Tests for error tracking."""

import tempfile
from pathlib import Path

import pytest

from nexus.logging.config import LogConfig, setup_logging
from nexus.logging.error_tracker import ErrorTracker


class TestErrorTracker:
    """Test error tracker."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test environment."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = LogConfig(log_dir=Path(tmpdir))
            setup_logging(config)
            self.error_tracker = ErrorTracker()

    def test_error_tracker_initialization(self) -> None:
        """Test error tracker initialization."""
        assert self.error_tracker is not None
        assert self.error_tracker.logger.name == "nexus.errors"

    def test_track_error(self) -> None:
        """Test tracking an error."""
        try:
            raise ValueError("Test error")
        except ValueError as e:
            self.error_tracker.track_error(
                error=e,
                context={"operation": "test"},
                user_id="user123",
                severity="error",
            )

    def test_track_validation_error(self) -> None:
        """Test tracking validation error."""
        self.error_tracker.track_validation_error(
            field="email",
            value="invalid-email",
            expected="valid email format",
            user_id="user123",
        )

    def test_track_http_error(self) -> None:
        """Test tracking HTTP error."""
        self.error_tracker.track_http_error(
            status_code=404,
            method="GET",
            url="/api/resource/123",
            error_message="Resource not found",
            user_id="user123",
            request_id="req123",
        )

    def test_track_database_error(self) -> None:
        """Test tracking database error."""
        error = Exception("Connection timeout")

        self.error_tracker.track_database_error(
            operation="insert",
            table="users",
            error=error,
            query="INSERT INTO users (name) VALUES (?)",
        )

    def test_track_exception(self) -> None:
        """Test tracking exception with traceback."""
        try:
            raise RuntimeError("Test exception")
        except RuntimeError:
            import sys

            exc_type, exc_value, exc_traceback = sys.exc_info()
            self.error_tracker.track_exception(
                exc_type=exc_type,
                exc_value=exc_value,
                exc_traceback=exc_traceback,
                context={"test": "context"},
            )
