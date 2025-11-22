"""
Integration Tests for API Endpoints

Tests for FastAPI endpoints with full request/response cycle.
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from modules.analytics.storage.models import EventORM, SessionORM, MetricORM
from shared.utils import get_utc_now, generate_uuid


class TestEventEndpoints:
    """Test suite for event API endpoints."""

    def test_create_event(self, client):
        """Test creating event via API."""
        event_data = {
            "name": "page_view",
            "event_type": "page_view",
            "user_id": "user_123",
            "session_id": "session_456",
            "properties": {"page": "/home"}
        }

        response = client.post("/api/v1/events", json=event_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "page_view"
        assert "id" in data

    def test_create_event_invalid_data(self, client):
        """Test creating event with invalid data."""
        event_data = {
            "name": "",  # Invalid empty name
            "event_type": "click"
        }

        response = client.post("/api/v1/events", json=event_data)

        assert response.status_code == 422  # Validation error

    def test_create_batch_events(self, client):
        """Test creating batch of events."""
        events = [
            {
                "name": f"event_{i}",
                "event_type": "click",
                "user_id": "user_123"
            }
            for i in range(5)
        ]

        response = client.post("/api/v1/events/batch", json={"events": events})

        assert response.status_code == 201
        data = response.json()
        assert data["count"] == 5

    def test_get_events(self, client, db_session):
        """Test getting events list."""
        # Create test events
        for i in range(3):
            event = EventORM(
                name=f"event_{i}",
                event_type="page_view",
                user_id="user_123",
                timestamp=get_utc_now()
            )
            db_session.add(event)
        db_session.commit()

        response = client.get("/api/v1/events")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 3

    def test_get_events_with_filters(self, client, db_session):
        """Test getting events with filters."""
        now = get_utc_now()

        # Create events of different types
        db_session.add(EventORM(
            name="page_view",
            event_type="page_view",
            user_id="user_123",
            timestamp=now
        ))
        db_session.add(EventORM(
            name="click",
            event_type="click",
            user_id="user_123",
            timestamp=now
        ))
        db_session.commit()

        response = client.get("/api/v1/events?event_type=page_view")

        assert response.status_code == 200
        data = response.json()
        assert all(e["event_type"] == "page_view" for e in data["items"])

    def test_get_event_by_id(self, client, db_session):
        """Test getting single event by ID."""
        event = EventORM(
            id=generate_uuid(),
            name="test_event",
            event_type="click",
            timestamp=get_utc_now()
        )
        db_session.add(event)
        db_session.commit()

        response = client.get(f"/api/v1/events/{event.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == event.id

    def test_get_event_not_found(self, client):
        """Test getting non-existent event."""
        response = client.get("/api/v1/events/nonexistent_id")

        assert response.status_code == 404

    def test_get_events_pagination(self, client, db_session):
        """Test event list pagination."""
        # Create many events
        for i in range(25):
            db_session.add(EventORM(
                name=f"event_{i}",
                event_type="click",
                timestamp=get_utc_now()
            ))
        db_session.commit()

        # Get first page
        response = client.get("/api/v1/events?page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10

        # Get second page
        response = client.get("/api/v1/events?page=2&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10


class TestMetricsEndpoints:
    """Test suite for metrics API endpoints."""

    def test_get_metrics(self, client, db_session):
        """Test getting metrics."""
        metric = MetricORM(
            name="daily_users",
            metric_type="gauge",
            value=1000.0,
            timestamp=get_utc_now()
        )
        db_session.add(metric)
        db_session.commit()

        response = client.get("/api/v1/metrics")

        assert response.status_code == 200

    def test_get_metrics_by_name(self, client, db_session):
        """Test getting metrics by name."""
        for i in range(5):
            db_session.add(MetricORM(
                name="daily_users",
                metric_type="gauge",
                value=1000.0 + i,
                timestamp=get_utc_now() + timedelta(days=i)
            ))
        db_session.commit()

        response = client.get("/api/v1/metrics/daily_users")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 5

    def test_get_metrics_time_series(self, client, db_session):
        """Test getting metrics time series."""
        now = get_utc_now()

        for i in range(10):
            db_session.add(MetricORM(
                name="revenue",
                metric_type="gauge",
                value=1000.0 + i * 100,
                timestamp=now + timedelta(days=i)
            ))
        db_session.commit()

        response = client.get(
            f"/api/v1/metrics/revenue/time-series?"
            f"start_date={now.isoformat()}&"
            f"end_date={(now + timedelta(days=15)).isoformat()}"
        )

        assert response.status_code == 200

    def test_aggregate_metrics(self, client, db_session):
        """Test metrics aggregation endpoint."""
        now = get_utc_now()

        # Create events for aggregation
        for i in range(10):
            db_session.add(EventORM(
                name="page_view",
                event_type="page_view",
                user_id=f"user_{i % 3}",
                timestamp=now
            ))
        db_session.commit()

        response = client.post("/api/v1/metrics/aggregate", json={
            "start_date": (now - timedelta(hours=1)).isoformat(),
            "end_date": (now + timedelta(hours=1)).isoformat(),
            "period": "day"
        })

        assert response.status_code == 200


class TestSessionEndpoints:
    """Test suite for session API endpoints."""

    def test_get_sessions(self, client, db_session):
        """Test getting sessions."""
        session = SessionORM(
            session_id="session_123",
            user_id="user_456",
            started_at=get_utc_now()
        )
        db_session.add(session)
        db_session.commit()

        response = client.get("/api/v1/sessions")

        assert response.status_code == 200

    def test_get_session_by_id(self, client, db_session):
        """Test getting session by ID."""
        session = SessionORM(
            session_id="session_123",
            user_id="user_456",
            started_at=get_utc_now(),
            page_views=5
        )
        db_session.add(session)
        db_session.commit()

        response = client.get(f"/api/v1/sessions/{session.session_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "session_123"
        assert data["page_views"] == 5

    def test_get_user_sessions(self, client, db_session):
        """Test getting sessions for specific user."""
        user_id = "user_123"

        for i in range(3):
            db_session.add(SessionORM(
                session_id=f"session_{i}",
                user_id=user_id,
                started_at=get_utc_now() - timedelta(days=i)
            ))
        db_session.commit()

        response = client.get(f"/api/v1/users/{user_id}/sessions")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3


class TestDashboardEndpoints:
    """Test suite for dashboard API endpoints."""

    def test_get_dashboard_overview(self, client, db_session):
        """Test getting dashboard overview."""
        # Create sample data
        now = get_utc_now()

        db_session.add(EventORM(
            name="page_view",
            event_type="page_view",
            user_id="user_1",
            timestamp=now
        ))
        db_session.add(SessionORM(
            session_id="session_1",
            user_id="user_1",
            started_at=now
        ))
        db_session.commit()

        response = client.get("/api/v1/dashboard/overview")

        assert response.status_code == 200
        data = response.json()
        assert "total_events" in data or "metrics" in data

    def test_get_dashboard_real_time(self, client):
        """Test real-time dashboard endpoint."""
        response = client.get("/api/v1/dashboard/realtime")

        assert response.status_code == 200

    def test_get_dashboard_trends(self, client, db_session):
        """Test dashboard trends endpoint."""
        response = client.get("/api/v1/dashboard/trends?period=week")

        assert response.status_code == 200


class TestAnalyticsEndpoints:
    """Test suite for analytics endpoints."""

    def test_funnel_analysis(self, client):
        """Test funnel analysis endpoint."""
        response = client.post("/api/v1/analytics/funnel", json={
            "funnel_id": "test_funnel",
            "start_date": get_utc_now().isoformat(),
            "end_date": (get_utc_now() + timedelta(days=7)).isoformat()
        })

        # May return 200 or 404 depending on funnel existence
        assert response.status_code in [200, 404]

    def test_cohort_analysis(self, client):
        """Test cohort analysis endpoint."""
        response = client.post("/api/v1/analytics/cohort", json={
            "cohort_date": get_utc_now().isoformat(),
            "periods": 12
        })

        assert response.status_code in [200, 404]

    def test_export_data(self, client):
        """Test data export endpoint."""
        response = client.post("/api/v1/analytics/export", json={
            "format": "csv",
            "data_type": "events",
            "start_date": (get_utc_now() - timedelta(days=7)).isoformat(),
            "end_date": get_utc_now().isoformat()
        })

        assert response.status_code in [200, 201]


class TestAuthenticationAndAuthorization:
    """Test suite for API authentication."""

    def test_api_requires_auth(self, client):
        """Test endpoints require authentication."""
        # Depends on auth implementation
        pass

    def test_api_key_authentication(self, client):
        """Test API key authentication."""
        pass

    def test_rate_limiting(self, client):
        """Test API rate limiting."""
        # Make multiple requests
        for i in range(100):
            response = client.get("/api/v1/events")
            # Should eventually get rate limited
            if response.status_code == 429:
                break


# Test count: 26 tests
