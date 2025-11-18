"""Tests for cron utilities"""
import pytest
from datetime import datetime
import pytz
from modules.scheduler.utils.cron_utils import (
    validate_cron_expression,
    get_cron_description,
    get_next_run_times,
    calculate_next_run
)
from modules.scheduler.models.schemas import JobType


class TestCronValidation:
    """Test cron expression validation"""

    def test_valid_cron_expression(self):
        """Test valid cron expression"""
        is_valid, description, error = validate_cron_expression("*/5 * * * *")
        assert is_valid is True
        assert description is not None
        assert error is None

    def test_invalid_cron_expression(self):
        """Test invalid cron expression"""
        is_valid, description, error = validate_cron_expression("invalid")
        assert is_valid is False
        assert error is not None

    def test_cron_description(self):
        """Test cron description generation"""
        description = get_cron_description("0 0 * * *")
        assert "midnight" in description.lower() or "0:00" in description


class TestNextRunTimes:
    """Test next run time calculation"""

    def test_get_next_run_times(self):
        """Test getting next run times"""
        runs = get_next_run_times("*/5 * * * *", count=3, timezone="UTC")
        assert len(runs) == 3
        assert all(isinstance(run, datetime) for run in runs)

    def test_calculate_next_run_cron(self):
        """Test calculate next run for cron job"""
        next_run = calculate_next_run(
            job_type=JobType.CRON,
            cron_expression="0 0 * * *",
            timezone="UTC"
        )
        assert next_run is not None
        assert isinstance(next_run, datetime)

    def test_calculate_next_run_interval(self):
        """Test calculate next run for interval job"""
        next_run = calculate_next_run(
            job_type=JobType.INTERVAL,
            interval_seconds=3600,
            timezone="UTC"
        )
        assert next_run is not None
        assert isinstance(next_run, datetime)

    def test_calculate_next_run_date(self):
        """Test calculate next run for date job"""
        scheduled_time = datetime(2025, 12, 31, 23, 59, tzinfo=pytz.UTC)
        next_run = calculate_next_run(
            job_type=JobType.DATE,
            scheduled_time=scheduled_time,
            timezone="UTC"
        )
        assert next_run == scheduled_time
