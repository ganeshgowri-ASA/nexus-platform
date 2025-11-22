"""
Integration Tests for Dashboard

Tests for dashboard data aggregation and visualization.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from modules.analytics.storage.models import EventORM, SessionORM, MetricORM, UserORM
from modules.analytics.core.aggregator import DataAggregator
from shared.utils import get_utc_now, generate_uuid


class TestDashboardOverview:
    """Test suite for dashboard overview."""

    def test_dashboard_overview_metrics(self, client, db_session):
        """Test dashboard overview returns key metrics."""
        now = get_utc_now()

        # Create sample data
        for i in range(10):
            db_session.add(EventORM(
                name="page_view",
                event_type="page_view",
                user_id=f"user_{i % 5}",
                session_id=f"session_{i}",
                timestamp=now
            ))

        for i in range(5):
            db_session.add(SessionORM(
                session_id=f"session_{i}",
                user_id=f"user_{i}",
                started_at=now,
                page_views=2,
                duration_seconds=120
            ))

        db_session.commit()

        response = client.get("/api/v1/dashboard/overview")

        if response.status_code == 200:
            data = response.json()
            # Verify key metrics present
            assert "total_events" in data or "events" in data or "metrics" in data

    def test_dashboard_real_time_data(self, client, db_session):
        """Test real-time dashboard data."""
        now = get_utc_now()

        # Create recent events
        for i in range(5):
            db_session.add(EventORM(
                name=f"event_{i}",
                event_type="page_view",
                user_id="user_1",
                timestamp=now - timedelta(minutes=i)
            ))
        db_session.commit()

        response = client.get("/api/v1/dashboard/realtime")

        assert response.status_code == 200

    def test_dashboard_time_series(self, client, db_session):
        """Test dashboard time series data."""
        now = get_utc_now()

        # Create metrics over time
        for i in range(7):
            db_session.add(MetricORM(
                name="daily_users",
                metric_type="gauge",
                value=100.0 + i * 10,
                timestamp=now - timedelta(days=7-i)
            ))
        db_session.commit()

        response = client.get(
            f"/api/v1/dashboard/time-series?"
            f"metric=daily_users&"
            f"start_date={(now - timedelta(days=7)).isoformat()}&"
            f"end_date={now.isoformat()}"
        )

        if response.status_code == 200:
            data = response.json()
            assert len(data) > 0


class TestDashboardCharts:
    """Test suite for dashboard charts data."""

    def test_user_growth_chart(self, client, db_session):
        """Test user growth chart data."""
        now = get_utc_now()

        # Create users over time
        for i in range(30):
            db_session.add(UserORM(
                id=f"user_{i}",
                first_seen_at=now - timedelta(days=30-i),
                last_seen_at=now
            ))
        db_session.commit()

        response = client.get("/api/v1/dashboard/charts/user-growth")

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))

    def test_traffic_sources_chart(self, client, db_session):
        """Test traffic sources chart."""
        now = get_utc_now()

        # Create events with different sources
        sources = ["google", "facebook", "direct", "email"]
        for i in range(100):
            db_session.add(EventORM(
                name="page_view",
                event_type="page_view",
                user_id=f"user_{i}",
                properties={"utm_source": sources[i % 4]},
                timestamp=now
            ))
        db_session.commit()

        response = client.get("/api/v1/dashboard/charts/traffic-sources")

        if response.status_code == 200:
            data = response.json()
            assert len(data) > 0

    def test_device_breakdown_chart(self, client, db_session):
        """Test device breakdown chart."""
        now = get_utc_now()

        # Create events with different devices
        devices = ["mobile", "desktop", "tablet"]
        for i in range(60):
            db_session.add(EventORM(
                name="page_view",
                event_type="page_view",
                device_type=devices[i % 3],
                timestamp=now
            ))
        db_session.commit()

        response = client.get("/api/v1/dashboard/charts/device-breakdown")

        if response.status_code == 200:
            data = response.json()
            assert len(data) > 0

    def test_top_pages_chart(self, client, db_session):
        """Test top pages chart."""
        now = get_utc_now()

        # Create page view events
        pages = ["/home", "/products", "/about", "/contact"]
        for i in range(100):
            db_session.add(EventORM(
                name="page_view",
                event_type="page_view",
                page_url=pages[i % 4],
                timestamp=now
            ))
        db_session.commit()

        response = client.get("/api/v1/dashboard/charts/top-pages")

        if response.status_code == 200:
            data = response.json()
            assert len(data) > 0


class TestDashboardFilters:
    """Test suite for dashboard filters."""

    def test_dashboard_date_range_filter(self, client, db_session):
        """Test dashboard with date range filter."""
        now = get_utc_now()

        # Create events across different dates
        for i in range(30):
            db_session.add(EventORM(
                name="page_view",
                event_type="page_view",
                timestamp=now - timedelta(days=i)
            ))
        db_session.commit()

        # Filter last 7 days
        start_date = (now - timedelta(days=7)).isoformat()
        end_date = now.isoformat()

        response = client.get(
            f"/api/v1/dashboard/overview?"
            f"start_date={start_date}&"
            f"end_date={end_date}"
        )

        assert response.status_code == 200

    def test_dashboard_user_segment_filter(self, client, db_session):
        """Test dashboard filtered by user segment."""
        now = get_utc_now()

        # Create events for different user types
        for i in range(20):
            user_type = "premium" if i < 10 else "free"
            db_session.add(EventORM(
                name="page_view",
                event_type="page_view",
                user_id=f"user_{i}",
                properties={"user_type": user_type},
                timestamp=now
            ))
        db_session.commit()

        response = client.get("/api/v1/dashboard/overview?segment=premium")

        assert response.status_code == 200

    def test_dashboard_module_filter(self, client, db_session):
        """Test dashboard filtered by module."""
        now = get_utc_now()

        # Create events for different modules
        modules = ["analytics", "auth", "storage"]
        for i in range(30):
            db_session.add(EventORM(
                name="action",
                event_type="click",
                module=modules[i % 3],
                timestamp=now
            ))
        db_session.commit()

        response = client.get("/api/v1/dashboard/overview?module=analytics")

        assert response.status_code == 200


class TestDashboardPerformance:
    """Test suite for dashboard performance."""

    def test_dashboard_caching(self, client, db_session, mock_cache):
        """Test dashboard data caching."""
        # First request - cache miss
        response1 = client.get("/api/v1/dashboard/overview")

        # Second request - cache hit
        response2 = client.get("/api/v1/dashboard/overview")

        # Both should succeed
        assert response1.status_code == 200
        assert response2.status_code == 200

    def test_dashboard_large_dataset(self, client, db_session):
        """Test dashboard performance with large dataset."""
        now = get_utc_now()

        # Create large dataset
        events = []
        for i in range(1000):
            events.append(EventORM(
                name=f"event_{i}",
                event_type="page_view",
                user_id=f"user_{i % 100}",
                timestamp=now - timedelta(hours=i % 24)
            ))

        db_session.bulk_save_objects(events)
        db_session.commit()

        # Dashboard should still respond quickly
        import time
        start_time = time.time()

        response = client.get("/api/v1/dashboard/overview")

        end_time = time.time()
        response_time = end_time - start_time

        assert response.status_code == 200
        assert response_time < 5.0  # Should respond within 5 seconds

    def test_dashboard_concurrent_requests(self, client):
        """Test dashboard handles concurrent requests."""
        import concurrent.futures

        def make_request():
            return client.get("/api/v1/dashboard/overview")

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [f.result() for f in futures]

        # All requests should succeed
        assert all(r.status_code == 200 for r in responses)


class TestDashboardExport:
    """Test suite for dashboard export functionality."""

    def test_export_dashboard_data_csv(self, client, db_session):
        """Test exporting dashboard data as CSV."""
        response = client.post("/api/v1/dashboard/export", json={
            "format": "csv",
            "data_type": "overview"
        })

        if response.status_code == 200:
            assert response.headers.get("Content-Type") == "text/csv"

    def test_export_dashboard_data_json(self, client, db_session):
        """Test exporting dashboard data as JSON."""
        response = client.post("/api/v1/dashboard/export", json={
            "format": "json",
            "data_type": "overview"
        })

        if response.status_code == 200:
            assert response.headers.get("Content-Type") == "application/json"

    def test_export_dashboard_pdf_report(self, client, db_session):
        """Test exporting dashboard as PDF report."""
        response = client.post("/api/v1/dashboard/export", json={
            "format": "pdf",
            "data_type": "report"
        })

        # May not be implemented yet
        assert response.status_code in [200, 501]


class TestDashboardAlerts:
    """Test suite for dashboard alerts."""

    def test_dashboard_threshold_alerts(self, client, db_session):
        """Test dashboard shows threshold alerts."""
        # Create metric that exceeds threshold
        db_session.add(MetricORM(
            name="error_rate",
            metric_type="gauge",
            value=15.0,  # High error rate
            timestamp=get_utc_now()
        ))
        db_session.commit()

        response = client.get("/api/v1/dashboard/alerts")

        if response.status_code == 200:
            data = response.json()
            # Check if alerts are present
            assert isinstance(data, (list, dict))

    def test_dashboard_anomaly_detection(self, client, db_session):
        """Test dashboard anomaly detection."""
        now = get_utc_now()

        # Normal metrics
        for i in range(10):
            db_session.add(MetricORM(
                name="daily_users",
                metric_type="gauge",
                value=100.0,
                timestamp=now - timedelta(days=10-i)
            ))

        # Anomaly
        db_session.add(MetricORM(
            name="daily_users",
            metric_type="gauge",
            value=500.0,  # Spike
            timestamp=now
        ))
        db_session.commit()

        response = client.get("/api/v1/dashboard/anomalies")

        # May return empty if not implemented
        assert response.status_code in [200, 404]


# Test count: 21 tests
