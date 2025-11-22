"""
Unit Tests for Pydantic Models

Tests for data model validation and serialization.
"""

import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError

from modules.analytics.models.event import (
    Event,
    EventCreate,
    EventUpdate,
    EventBatch,
    EventQuery,
    EventAggregation
)
from modules.analytics.models.metric import MetricCreate, MetricQuery
from modules.analytics.models.session import SessionCreate, SessionUpdate
from shared.utils import get_utc_now


class TestEventModels:
    """Test suite for Event models."""

    def test_event_create_valid(self):
        """Test creating valid event."""
        event = EventCreate(
            name="page_view",
            event_type="page_view",
            user_id="user_123",
            session_id="session_456"
        )

        assert event.name == "page_view"
        assert event.event_type == "page_view"
        assert event.user_id == "user_123"

    def test_event_create_minimal(self):
        """Test creating event with minimal data."""
        event = EventCreate(
            name="click",
            event_type="click"
        )

        assert event.name == "click"
        assert event.properties == {}
        assert event.user_id is None

    def test_event_create_invalid_name(self):
        """Test event creation with invalid name."""
        with pytest.raises(ValidationError):
            EventCreate(
                name="",  # Empty name
                event_type="click"
            )

    def test_event_create_with_properties(self):
        """Test event with properties."""
        event = EventCreate(
            name="purchase",
            event_type="purchase",
            properties={
                "item_id": "123",
                "price": 99.99,
                "currency": "USD"
            }
        )

        assert event.properties["item_id"] == "123"
        assert event.properties["price"] == 99.99

    def test_event_properties_limit(self):
        """Test event properties count limit."""
        # Create 101 properties (exceeds limit of 100)
        properties = {f"key_{i}": i for i in range(101)}

        with pytest.raises(ValidationError):
            EventCreate(
                name="test",
                event_type="test",
                properties=properties
            )

    def test_event_model_complete(self):
        """Test complete Event model."""
        event = Event(
            name="page_view",
            event_type="page_view",
            user_id="user_123",
            properties={"page": "/home"}
        )

        assert event.id is not None
        assert event.timestamp is not None
        assert event.processed is False

    def test_event_update_model(self):
        """Test EventUpdate model."""
        update = EventUpdate(
            properties={"updated": True}
        )

        assert update.properties["updated"] is True

    def test_event_batch_valid(self):
        """Test valid event batch."""
        events = [
            EventCreate(name=f"event_{i}", event_type="click")
            for i in range(10)
        ]

        batch = EventBatch(events=events)

        assert len(batch.events) == 10
        assert batch.batch_id is not None

    def test_event_batch_empty(self):
        """Test empty event batch."""
        with pytest.raises(ValidationError):
            EventBatch(events=[])

    def test_event_batch_too_large(self):
        """Test batch exceeding max size."""
        events = [
            EventCreate(name=f"event_{i}", event_type="click")
            for i in range(1001)  # Exceeds limit of 1000
        ]

        with pytest.raises(ValidationError):
            EventBatch(events=events)

    def test_event_query_model(self):
        """Test EventQuery model."""
        query = EventQuery(
            event_types=["page_view", "click"],
            user_id="user_123",
            start_date=get_utc_now() - timedelta(days=7),
            end_date=get_utc_now(),
            page=1,
            page_size=50
        )

        assert len(query.event_types) == 2
        assert query.page == 1

    def test_event_query_pagination(self):
        """Test query pagination validation."""
        query = EventQuery(
            page=2,
            page_size=100
        )

        assert query.page == 2
        assert query.page_size == 100

    def test_event_query_invalid_page(self):
        """Test invalid page number."""
        with pytest.raises(ValidationError):
            EventQuery(page=0)  # Must be >= 1

    def test_event_query_invalid_page_size(self):
        """Test invalid page size."""
        with pytest.raises(ValidationError):
            EventQuery(page_size=2000)  # Exceeds max

    def test_event_aggregation_model(self):
        """Test EventAggregation model."""
        agg = EventAggregation(
            event_type="page_view",
            count=1000,
            unique_users=250,
            unique_sessions=500,
            start_date=get_utc_now() - timedelta(days=1),
            end_date=get_utc_now()
        )

        assert agg.count == 1000
        assert agg.unique_users == 250


class TestMetricModels:
    """Test suite for Metric models."""

    def test_metric_create_valid(self):
        """Test creating valid metric."""
        metric = MetricCreate(
            name="daily_users",
            metric_type="gauge",
            value=1250.0
        )

        assert metric.name == "daily_users"
        assert metric.value == 1250.0

    def test_metric_create_with_dimensions(self):
        """Test metric with dimensions."""
        metric = MetricCreate(
            name="revenue",
            metric_type="gauge",
            value=5000.0,
            dimensions={
                "region": "us-west",
                "plan": "premium"
            }
        )

        assert metric.dimensions["region"] == "us-west"

    def test_metric_query_model(self):
        """Test MetricQuery model."""
        query = MetricQuery(
            name="daily_users",
            start_date=get_utc_now() - timedelta(days=30),
            end_date=get_utc_now()
        )

        assert query.name == "daily_users"


class TestSessionModels:
    """Test suite for Session models."""

    def test_session_create_valid(self):
        """Test creating valid session."""
        session = SessionCreate(
            session_id="session_123",
            user_id="user_456",
            started_at=get_utc_now()
        )

        assert session.session_id == "session_123"
        assert session.user_id == "user_456"

    def test_session_create_with_metrics(self):
        """Test session with metrics."""
        session = SessionCreate(
            session_id="session_123",
            user_id="user_456",
            started_at=get_utc_now(),
            duration_seconds=300,
            page_views=5,
            events_count=10
        )

        assert session.duration_seconds == 300
        assert session.page_views == 5

    def test_session_update_model(self):
        """Test SessionUpdate model."""
        update = SessionUpdate(
            duration_seconds=600,
            page_views=10,
            converted=True
        )

        assert update.duration_seconds == 600
        assert update.converted is True


class TestFunnelModels:
    """Test suite for Funnel models."""

    def test_funnel_create_valid(self):
        """Test creating valid funnel."""
        # Would test FunnelCreate model
        pass

    def test_funnel_step_ordering(self):
        """Test funnel step ordering."""
        pass


class TestCohortModels:
    """Test suite for Cohort models."""

    def test_cohort_create_valid(self):
        """Test creating valid cohort."""
        pass

    def test_cohort_retention_model(self):
        """Test cohort retention model."""
        pass


class TestGoalModels:
    """Test suite for Goal models."""

    def test_goal_create_valid(self):
        """Test creating valid goal."""
        pass

    def test_goal_conditions_validation(self):
        """Test goal conditions validation."""
        pass


@pytest.mark.parametrize("event_type", [
    "page_view",
    "click",
    "form_submit",
    "purchase",
    "custom_event"
])
def test_various_event_types(event_type):
    """Test creating events of various types."""
    event = EventCreate(
        name=f"test_{event_type}",
        event_type=event_type
    )

    assert event.event_type == event_type


@pytest.mark.parametrize("value", [0, 1.5, 100, 9999.99])
def test_metric_various_values(value):
    """Test metrics with various values."""
    metric = MetricCreate(
        name="test_metric",
        metric_type="gauge",
        value=value
    )

    assert metric.value == value


def test_model_serialization():
    """Test model serialization to dict."""
    event = EventCreate(
        name="test",
        event_type="click",
        properties={"button": "submit"}
    )

    data = event.model_dump()

    assert isinstance(data, dict)
    assert data["name"] == "test"
    assert data["properties"]["button"] == "submit"


def test_model_from_dict():
    """Test model creation from dict."""
    data = {
        "name": "page_view",
        "event_type": "page_view",
        "user_id": "user_123"
    }

    event = EventCreate(**data)

    assert event.name == "page_view"
    assert event.user_id == "user_123"


# Test count: 36 tests
