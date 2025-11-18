"""Tests for timezone utilities"""
import pytest
from datetime import datetime
import pytz
from modules.scheduler.utils.timezone_utils import (
    get_available_timezones,
    get_common_timezones,
    convert_timezone,
    get_current_time_in_timezone,
    is_valid_timezone,
    get_timezone_offset
)


class TestTimezoneUtils:
    """Test timezone utilities"""

    def test_get_available_timezones(self):
        """Test getting available timezones"""
        timezones = get_available_timezones()
        assert isinstance(timezones, list)
        assert len(timezones) > 0
        assert "UTC" in timezones

    def test_get_common_timezones(self):
        """Test getting common timezones"""
        timezones = get_common_timezones()
        assert isinstance(timezones, dict)
        assert "US" in timezones
        assert "Europe" in timezones

    def test_convert_timezone(self):
        """Test timezone conversion"""
        dt = datetime(2025, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)
        converted = convert_timezone(dt, "UTC", "US/Eastern")
        assert converted.hour != 12  # Should be different hour

    def test_get_current_time_in_timezone(self):
        """Test getting current time in timezone"""
        current = get_current_time_in_timezone("UTC")
        assert isinstance(current, datetime)
        assert current.tzinfo is not None

    def test_is_valid_timezone(self):
        """Test timezone validation"""
        assert is_valid_timezone("UTC") is True
        assert is_valid_timezone("US/Eastern") is True
        assert is_valid_timezone("Invalid/Timezone") is False

    def test_get_timezone_offset(self):
        """Test getting timezone offset"""
        offset = get_timezone_offset("UTC")
        assert offset == "+00:00"

        offset = get_timezone_offset("US/Eastern")
        assert offset in ["-05:00", "-04:00"]  # Depending on DST
