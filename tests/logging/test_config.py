"""Tests for logging configuration."""

import logging
import tempfile
from pathlib import Path

import pytest
import structlog

from nexus.logging.config import LogConfig, LogLevel, get_logger, setup_logging


class TestLoggingConfig:
    """Test logging configuration."""

    def test_log_config_defaults(self) -> None:
        """Test default log configuration."""
        config = LogConfig()

        assert config.log_dir == Path("logs")
        assert config.log_level == LogLevel.INFO
        assert config.enable_json is True
        assert config.enable_console is True
        assert config.max_bytes == 10 * 1024 * 1024
        assert config.backup_count == 10
        assert config.app_name == "nexus"

    def test_log_config_custom(self) -> None:
        """Test custom log configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = LogConfig(
                log_dir=Path(tmpdir),
                log_level=LogLevel.DEBUG,
                enable_json=False,
                enable_console=False,
                max_bytes=1024,
                backup_count=5,
                app_name="test",
            )

            assert config.log_dir == Path(tmpdir)
            assert config.log_level == LogLevel.DEBUG
            assert config.enable_json is False
            assert config.enable_console is False
            assert config.max_bytes == 1024
            assert config.backup_count == 5
            assert config.app_name == "test"

    def test_setup_logging(self) -> None:
        """Test logging setup."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = LogConfig(
                log_dir=Path(tmpdir),
                log_level=LogLevel.INFO,
            )

            setup_logging(config)

            # Verify log files are created when logging
            logger = get_logger("test")
            logger.info("test message", key="value")

            # Check that log files exist
            json_log = Path(tmpdir) / "nexus.json.log"
            error_log = Path(tmpdir) / "nexus.error.log"

            assert json_log.exists()
            assert error_log.exists()

    def test_get_logger(self) -> None:
        """Test getting a logger instance."""
        logger = get_logger("test_logger")

        assert isinstance(logger, structlog.stdlib.BoundLogger)
        assert logger.name == "test_logger"

    def test_log_level_enum(self) -> None:
        """Test log level enumeration."""
        assert LogLevel.DEBUG.value == "DEBUG"
        assert LogLevel.INFO.value == "INFO"
        assert LogLevel.WARNING.value == "WARNING"
        assert LogLevel.ERROR.value == "ERROR"
        assert LogLevel.CRITICAL.value == "CRITICAL"

    def test_logging_output(self) -> None:
        """Test that logging produces output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = LogConfig(
                log_dir=Path(tmpdir),
                log_level=LogLevel.DEBUG,
            )

            setup_logging(config)

            logger = get_logger("test")
            logger.debug("debug message")
            logger.info("info message")
            logger.warning("warning message")
            logger.error("error message")
            logger.critical("critical message")

            # Read log file and verify entries
            json_log = Path(tmpdir) / "nexus.json.log"
            with open(json_log, "r") as f:
                content = f.read()
                assert "debug message" in content
                assert "info message" in content
                assert "warning message" in content
                assert "error message" in content
                assert "critical message" in content

    def test_error_log_separation(self) -> None:
        """Test that errors are logged to separate file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = LogConfig(
                log_dir=Path(tmpdir),
                log_level=LogLevel.INFO,
            )

            setup_logging(config)

            logger = get_logger("test")
            logger.info("info message")
            logger.error("error message")

            # Read error log file
            error_log = Path(tmpdir) / "nexus.error.log"
            with open(error_log, "r") as f:
                content = f.read()
                assert "error message" in content
                assert "info message" not in content
