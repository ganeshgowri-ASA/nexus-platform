"""Pytest configuration for social media tests."""

import pytest
from uuid import uuid4


@pytest.fixture
def test_user_id():
    """Generate a test user ID."""
    return uuid4()


@pytest.fixture
def test_campaign_id():
    """Generate a test campaign ID."""
    return uuid4()
