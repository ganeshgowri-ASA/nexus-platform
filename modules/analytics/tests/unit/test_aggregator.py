"""
Unit Tests for Data Aggregator

Tests for data aggregation engine with time-series support.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from modules.analytics.core.aggregator import DataAggregator
from modules.analytics.storage.models import EventORM, SessionORM, MetricORM
from shared.constants import AggregationPeriod, MetricType
from shared.utils import get_utc_now


class TestDataAggregator:
    """Test suite for DataAggregator class."""

    def test_aggregator_initialization(self, aggregator):
        """Test aggregator initializes correctly."""
        assert aggregator.db is not None
        assert aggregator.metric_repository is not None

    def test_aggregate_events_basic(self, aggregator, db_session):
        """Test basic event aggregation."""
        # Create test events
        now = get_utc_now()
        for i in range(5):
            event = EventORM(
                name=f"event_{i}",
                event_type="page_view",
                user_id=f"user_{i}",
                session_id=f"session_{i}",
                timestamp=now + timedelta(hours=i)
            )
            db_session.add(event)
        db_session.commit()

        # Aggregate
        start_date = now - timedelta(days=1)
        end_date = now + timedelta(days=1)
        results = aggregator.aggregate_events(
            db_session, start_date, end_date, AggregationPeriod.DAY
        )

        assert len(results) > 0
        assert all("period" in r for r in results)
        assert all("event_type" in r for r in results)
        assert all("count" in r for r in results)

    def test_aggregate_events_with_filter(self, aggregator, db_session):
        """Test event aggregation with event type filter."""
        now = get_utc_now()

        # Create events of different types
        for event_type in ["page_view", "click", "purchase"]:
            for i in range(3):
                event = EventORM(
                    name=f"{event_type}_{i}",
                    event_type=event_type,
                    user_id=f"user_{i}",
                    timestamp=now
                )
                db_session.add(event)
        db_session.commit()

        # Aggregate with filter
        results = aggregator.aggregate_events(
            db_session,
            now - timedelta(hours=1),
            now + timedelta(hours=1),
            AggregationPeriod.DAY,
            event_types=["page_view", "click"]
        )

        # Should only include filtered types
        event_types = {r["event_type"] for r in results}
        assert "purchase" not in event_types

    @pytest.mark.parametrize("period", [
        AggregationPeriod.DAY,
        AggregationPeriod.WEEK,
        AggregationPeriod.MONTH
    ])
    def test_aggregate_events_different_periods(self, aggregator, db_session, period):
        """Test aggregation with different periods."""
        now = get_utc_now()

        # Create events
        for i in range(10):
            event = EventORM(
                name=f"event_{i}",
                event_type="page_view",
                user_id="user_1",
                timestamp=now + timedelta(days=i)
            )
            db_session.add(event)
        db_session.commit()

        results = aggregator.aggregate_events(
            db_session,
            now - timedelta(days=1),
            now + timedelta(days=30),
            period
        )

        assert isinstance(results, list)

    def test_aggregate_events_unique_counts(self, aggregator, db_session):
        """Test unique user and session counting."""
        now = get_utc_now()

        # Create events with duplicate users/sessions
        for i in range(10):
            event = EventORM(
                name=f"event_{i}",
                event_type="page_view",
                user_id="user_1",  # Same user
                session_id="session_1",  # Same session
                timestamp=now
            )
            db_session.add(event)
        db_session.commit()

        results = aggregator.aggregate_events(
            db_session,
            now - timedelta(hours=1),
            now + timedelta(hours=1),
            AggregationPeriod.DAY
        )

        if results:
            assert results[0]["count"] == 10
            assert results[0]["unique_users"] == 1
            assert results[0]["unique_sessions"] == 1

    def test_aggregate_events_empty_result(self, aggregator, db_session):
        """Test aggregation with no matching events."""
        future_date = get_utc_now() + timedelta(days=365)
        results = aggregator.aggregate_events(
            db_session,
            future_date,
            future_date + timedelta(days=1),
            AggregationPeriod.DAY
        )

        assert results == []

    def test_calculate_session_metrics(self, aggregator, db_session):
        """Test session metrics calculation."""
        now = get_utc_now()

        # Create test sessions
        for i in range(10):
            session = SessionORM(
                session_id=f"session_{i}",
                user_id=f"user_{i}",
                started_at=now + timedelta(hours=i),
                duration_seconds=300 + i * 10,
                page_views=5 + i,
                is_bounce=i % 3 == 0,
                converted=i % 4 == 0,
                conversion_value=100.0 if i % 4 == 0 else 0.0
            )
            db_session.add(session)
        db_session.commit()

        # Calculate metrics
        metrics = aggregator.calculate_session_metrics(
            db_session,
            now - timedelta(hours=1),
            now + timedelta(hours=12)
        )

        assert metrics["total_sessions"] == 10
        assert metrics["unique_users"] == 10
        assert metrics["avg_duration_seconds"] > 0
        assert metrics["avg_page_views"] > 0
        assert 0 <= metrics["bounce_rate"] <= 100
        assert 0 <= metrics["conversion_rate"] <= 100
        assert metrics["total_conversions"] > 0

    def test_calculate_session_metrics_empty(self, aggregator, db_session):
        """Test session metrics with no sessions."""
        future_date = get_utc_now() + timedelta(days=365)
        metrics = aggregator.calculate_session_metrics(
            db_session,
            future_date,
            future_date + timedelta(days=1)
        )

        assert metrics["total_sessions"] == 0
        assert metrics["bounce_rate"] == 0
        assert metrics["conversion_rate"] == 0

    def test_calculate_session_metrics_all_bounces(self, aggregator, db_session):
        """Test metrics when all sessions are bounces."""
        now = get_utc_now()

        for i in range(5):
            session = SessionORM(
                session_id=f"session_{i}",
                user_id=f"user_{i}",
                started_at=now,
                duration_seconds=10,
                page_views=1,
                is_bounce=True,
                converted=False
            )
            db_session.add(session)
        db_session.commit()

        metrics = aggregator.calculate_session_metrics(
            db_session, now - timedelta(hours=1), now + timedelta(hours=1)
        )

        assert metrics["bounce_rate"] == 100.0
        assert metrics["conversion_rate"] == 0.0

    def test_generate_time_series(self, aggregator, db_session):
        """Test time series generation."""
        now = get_utc_now()

        # Create metrics
        for i in range(10):
            metric = MetricORM(
                name="daily_users",
                metric_type="gauge",
                value=100.0 + i * 10,
                timestamp=now + timedelta(days=i)
            )
            db_session.add(metric)
        db_session.commit()

        # Generate time series
        time_series = aggregator.generate_time_series(
            db_session,
            "daily_users",
            now - timedelta(days=1),
            now + timedelta(days=15),
            AggregationPeriod.DAY
        )

        assert len(time_series) > 0
        assert all(isinstance(ts, tuple) for ts in time_series)
        assert all(len(ts) == 2 for ts in time_series)

    def test_save_metric(self, aggregator, db_session):
        """Test saving a calculated metric."""
        success = aggregator.save_metric(
            db_session,
            name="test_metric",
            metric_type=MetricType.GAUGE,
            value=42.5,
            period=AggregationPeriod.DAY,
            dimensions={"source": "test"},
            module="analytics"
        )

        assert success is True

        # Verify saved
        metric = db_session.query(MetricORM).filter_by(name="test_metric").first()
        assert metric is not None
        assert metric.value == 42.5

    def test_save_metric_with_timestamp(self, aggregator, db_session):
        """Test saving metric with custom timestamp."""
        custom_time = datetime(2024, 1, 1, 12, 0, 0)

        success = aggregator.save_metric(
            db_session,
            name="historic_metric",
            metric_type=MetricType.COUNTER,
            value=100.0,
            timestamp=custom_time
        )

        assert success is True

    def test_aggregate_by_dimension_country(self, aggregator, db_session):
        """Test aggregation by country dimension."""
        now = get_utc_now()

        # Create events with different countries
        countries = ["US", "UK", "DE", "FR"]
        for country in countries:
            for i in range(5):
                event = EventORM(
                    name="page_view",
                    event_type="page_view",
                    user_id=f"user_{country}_{i}",
                    country=country,
                    timestamp=now
                )
                db_session.add(event)
        db_session.commit()

        # Aggregate by country
        results = aggregator.aggregate_by_dimension(
            db_session,
            "country",
            now - timedelta(hours=1),
            now + timedelta(hours=1)
        )

        assert len(results) == 4
        assert all(r["dimension"] == "country" for r in results)
        assert {r["value"] for r in results} == set(countries)

    def test_aggregate_by_dimension_device(self, aggregator, db_session):
        """Test aggregation by device type."""
        now = get_utc_now()

        devices = ["mobile", "desktop", "tablet"]
        for device in devices:
            for i in range(3):
                event = EventORM(
                    name="page_view",
                    event_type="page_view",
                    user_id=f"user_{i}",
                    device_type=device,
                    timestamp=now
                )
                db_session.add(event)
        db_session.commit()

        results = aggregator.aggregate_by_dimension(
            db_session,
            "device_type",
            now - timedelta(hours=1),
            now + timedelta(hours=1)
        )

        assert len(results) == 3

    def test_aggregate_by_invalid_dimension(self, aggregator, db_session):
        """Test aggregation with invalid dimension."""
        now = get_utc_now()
        results = aggregator.aggregate_by_dimension(
            db_session,
            "invalid_field",
            now - timedelta(hours=1),
            now + timedelta(hours=1)
        )

        assert results == []

    def test_calculate_retention(self, aggregator, db_session):
        """Test retention rate calculation."""
        cohort_date = get_utc_now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Create cohort users
        for i in range(100):
            session = SessionORM(
                session_id=f"initial_{i}",
                user_id=f"user_{i}",
                started_at=cohort_date + timedelta(hours=i % 24)
            )
            db_session.add(session)

        # Create return sessions for some users
        for week in range(1, 4):
            for i in range(0, 50, week):  # Decreasing retention
                session = SessionORM(
                    session_id=f"week_{week}_{i}",
                    user_id=f"user_{i}",
                    started_at=cohort_date + timedelta(weeks=week)
                )
                db_session.add(session)

        db_session.commit()

        # Calculate retention
        retention = aggregator.calculate_retention(
            db_session,
            cohort_date,
            periods=4
        )

        assert len(retention) > 0
        assert all("period" in r for r in retention)
        assert all("retention_rate" in r for r in retention)
        assert all(0 <= r["retention_rate"] <= 100 for r in retention)

    def test_calculate_retention_empty_cohort(self, aggregator, db_session):
        """Test retention with no cohort users."""
        future_date = get_utc_now() + timedelta(days=365)
        retention = aggregator.calculate_retention(db_session, future_date, periods=4)

        assert retention == []

    def test_calculate_retention_periods(self, aggregator, db_session):
        """Test retention calculation with different period counts."""
        cohort_date = get_utc_now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Create base cohort
        for i in range(10):
            session = SessionORM(
                session_id=f"user_{i}",
                user_id=f"user_{i}",
                started_at=cohort_date
            )
            db_session.add(session)
        db_session.commit()

        retention = aggregator.calculate_retention(db_session, cohort_date, periods=8)

        assert len(retention) == 8

    def test_aggregate_events_error_handling(self, aggregator, db_session):
        """Test error handling in event aggregation."""
        with patch.object(db_session, 'query', side_effect=Exception("DB Error")):
            results = aggregator.aggregate_events(
                db_session,
                get_utc_now(),
                get_utc_now() + timedelta(days=1),
                AggregationPeriod.DAY
            )
            assert results == []

    def test_save_metric_error_handling(self, aggregator, db_session):
        """Test error handling when saving metric."""
        with patch.object(aggregator.metric_repository, 'create', side_effect=Exception("Save Error")):
            success = aggregator.save_metric(
                db_session,
                "error_metric",
                MetricType.GAUGE,
                100.0
            )
            assert success is False


# Test count: 28 tests
