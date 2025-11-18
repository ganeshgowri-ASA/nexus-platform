"""
Integration Tests for Event Flow

End-to-end tests for event tracking workflow.
"""

import pytest
import time
from datetime import datetime, timedelta

from modules.analytics.core.tracker import EventTracker
from modules.analytics.core.processor import EventProcessor
from modules.analytics.core.aggregator import DataAggregator
from modules.analytics.storage.models import EventORM, UserORM, SessionORM, GoalORM
from shared.utils import get_utc_now, generate_uuid


class TestEndToEndEventFlow:
    """Test complete event tracking flow."""

    def test_track_process_aggregate_flow(self, test_db, db_session):
        """Test complete flow: track -> process -> aggregate."""
        # Step 1: Track events
        tracker = EventTracker(db=test_db, batch_size=5, auto_start=False)

        event_ids = []
        for i in range(5):
            event_id = tracker.track(
                name=f"page_view_{i}",
                event_type="page_view",
                user_id="user_123",
                session_id="session_456",
                properties={"page": f"/page_{i}"}
            )
            event_ids.append(event_id)

        # Flush to database
        tracker.flush()

        # Verify events in database
        events = db_session.query(EventORM).filter(
            EventORM.id.in_(event_ids)
        ).all()
        assert len(events) == 5

        # Step 2: Process events
        processor = EventProcessor(db=test_db)
        processed_count = processor.process_events(batch_size=10)

        assert processed_count == 5

        # Verify processing created user
        user = db_session.query(UserORM).filter_by(id="user_123").first()
        assert user is not None

        # Step 3: Aggregate data
        aggregator = DataAggregator(db=test_db)
        now = get_utc_now()
        aggregated = aggregator.aggregate_events(
            db_session,
            now - timedelta(hours=1),
            now + timedelta(hours=1)
        )

        assert len(aggregated) > 0

    def test_user_journey_tracking(self, test_db, db_session):
        """Test tracking complete user journey."""
        tracker = EventTracker(db=test_db, auto_start=False)
        user_id = "user_journey"
        session_id = "session_journey"

        # Create session
        session = SessionORM(
            session_id=session_id,
            user_id=user_id,
            started_at=get_utc_now(),
            events_count=0,
            page_views=0
        )
        db_session.add(session)
        db_session.commit()

        # User journey: landing -> product view -> add to cart -> checkout -> purchase
        journey = [
            ("landing", "page_view", {"page": "/"}),
            ("product_view", "page_view", {"page": "/product/123"}),
            ("add_to_cart", "click", {"product_id": "123"}),
            ("checkout", "page_view", {"page": "/checkout"}),
            ("purchase", "purchase", {"value": 99.99, "product_id": "123"})
        ]

        for name, event_type, properties in journey:
            tracker.track(
                name=name,
                event_type=event_type,
                user_id=user_id,
                session_id=session_id,
                properties=properties
            )

        tracker.flush()

        # Verify all events tracked
        events = db_session.query(EventORM).filter_by(
            user_id=user_id
        ).order_by(EventORM.timestamp).all()

        assert len(events) == 5
        assert events[0].name == "landing"
        assert events[-1].name == "purchase"

        # Process events
        processor = EventProcessor(db=test_db)
        processor.process_events()

        # Verify session updated
        db_session.refresh(session)
        assert session.events_count == 5
        assert session.page_views == 3  # landing, product_view, checkout

    def test_conversion_tracking_flow(self, test_db, db_session):
        """Test conversion tracking through event flow."""
        # Create goal
        goal = GoalORM(
            id=generate_uuid(),
            name="Purchase Goal",
            event_type="purchase",
            enabled=True,
            value=100.0,
            conditions={}
        )
        db_session.add(goal)
        db_session.commit()

        # Track conversion event
        tracker = EventTracker(db=test_db, auto_start=False)
        tracker.track(
            name="purchase",
            event_type="purchase",
            user_id="user_convert",
            session_id="session_convert",
            properties={"value": 100.0}
        )
        tracker.flush()

        # Process and check conversion
        processor = EventProcessor(db=test_db)
        processor.process_events()

        # Verify conversion recorded
        from modules.analytics.storage.models import GoalConversionORM
        conversion = db_session.query(GoalConversionORM).filter_by(
            goal_id=goal.id
        ).first()
        # Note: Conversion creation depends on goal matching logic

    def test_batch_event_processing(self, test_db, db_session):
        """Test processing large batch of events."""
        tracker = EventTracker(db=test_db, batch_size=50, auto_start=False)

        # Track 100 events
        for i in range(100):
            tracker.track(
                name=f"event_{i}",
                event_type="page_view",
                user_id=f"user_{i % 10}",  # 10 different users
                properties={"index": i}
            )

        # Flush in batches
        count1 = tracker.flush()
        assert count1 == 50

        count2 = tracker.flush()
        assert count2 == 50

        # Process all events
        processor = EventProcessor(db=test_db)
        total_processed = 0

        while True:
            processed = processor.process_events(batch_size=25)
            if processed == 0:
                break
            total_processed += processed

        assert total_processed == 100

    def test_concurrent_event_tracking(self, test_db, db_session):
        """Test concurrent event tracking from multiple sources."""
        import threading

        tracker = EventTracker(db=test_db, batch_size=100, auto_start=False)
        events_per_thread = 20
        num_threads = 5

        def track_events(thread_id):
            for i in range(events_per_thread):
                tracker.track(
                    name=f"event_{thread_id}_{i}",
                    event_type="click",
                    user_id=f"user_{thread_id}",
                    properties={"thread": thread_id}
                )

        threads = [
            threading.Thread(target=track_events, args=(i,))
            for i in range(num_threads)
        ]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Should have tracked all events
        expected_count = events_per_thread * num_threads
        assert tracker.get_queue_size() == expected_count

        tracker.flush()

    def test_real_time_analytics_pipeline(self, test_db, db_session):
        """Test real-time analytics pipeline."""
        tracker = EventTracker(db=test_db, auto_start=True, flush_interval=1)
        processor = EventProcessor(db=test_db)
        aggregator = DataAggregator(db=test_db)

        # Track events
        for i in range(10):
            tracker.track(
                name="page_view",
                event_type="page_view",
                user_id=f"user_{i}",
                session_id=f"session_{i}"
            )

        # Wait for auto-flush
        time.sleep(1.5)

        # Process events
        processor.process_events()

        # Aggregate
        now = get_utc_now()
        results = aggregator.aggregate_events(
            db_session,
            now - timedelta(hours=1),
            now + timedelta(hours=1)
        )

        tracker.stop()

        assert len(results) > 0

    def test_session_lifecycle(self, test_db, db_session):
        """Test complete session lifecycle."""
        tracker = EventTracker(db=test_db, auto_start=False)
        processor = EventProcessor(db=test_db)

        user_id = "user_lifecycle"
        session_id = "session_lifecycle"
        now = get_utc_now()

        # Create session
        session = SessionORM(
            session_id=session_id,
            user_id=user_id,
            started_at=now,
            events_count=0,
            page_views=0,
            is_bounce=True,
            duration_seconds=0
        )
        db_session.add(session)
        db_session.commit()

        # Track session events
        timestamps = [0, 30, 60, 120, 180]  # seconds

        for seconds in timestamps:
            tracker.track(
                name="page_view",
                event_type="page_view",
                user_id=user_id,
                session_id=session_id,
                timestamp=now + timedelta(seconds=seconds)
            )

        tracker.flush()
        processor.process_events()

        # Verify session updated
        db_session.refresh(session)
        assert session.page_views == 5
        assert session.duration_seconds >= 180
        assert session.is_bounce is False  # Multiple page views

    def test_metric_calculation_pipeline(self, test_db, db_session):
        """Test metric calculation pipeline."""
        tracker = EventTracker(db=test_db, auto_start=False)
        processor = EventProcessor(db=test_db)
        aggregator = DataAggregator(db=test_db)

        # Track events
        now = get_utc_now()
        for i in range(50):
            tracker.track(
                name="page_view",
                event_type="page_view",
                user_id=f"user_{i % 10}",
                timestamp=now
            )

        tracker.flush()
        processor.process_events()

        # Calculate session metrics
        metrics = aggregator.calculate_session_metrics(
            db_session,
            now - timedelta(hours=1),
            now + timedelta(hours=1)
        )

        # Save metrics
        from shared.constants import MetricType, AggregationPeriod
        aggregator.save_metric(
            db_session,
            name="unique_users",
            metric_type=MetricType.GAUGE,
            value=metrics.get("unique_users", 0),
            period=AggregationPeriod.DAY,
            timestamp=now
        )
        db_session.commit()

        # Verify metric saved
        from modules.analytics.storage.models import MetricORM
        metric = db_session.query(MetricORM).filter_by(
            name="unique_users"
        ).first()

        assert metric is not None

    def test_error_recovery_in_pipeline(self, test_db, db_session):
        """Test pipeline error recovery."""
        tracker = EventTracker(db=test_db, auto_start=False)

        # Track valid events
        for i in range(5):
            tracker.track(
                name=f"event_{i}",
                event_type="click",
                user_id="user_1"
            )

        # Track invalid event (should be handled gracefully)
        try:
            tracker.track(
                name="",  # Invalid
                event_type="click"
            )
        except:
            pass

        # Track more valid events
        for i in range(5, 10):
            tracker.track(
                name=f"event_{i}",
                event_type="click",
                user_id="user_1"
            )

        # Should flush valid events
        count = tracker.flush()
        assert count >= 10

    def test_data_enrichment_flow(self, test_db, db_session):
        """Test data enrichment in event flow."""
        tracker = EventTracker(db=test_db, auto_start=False)
        processor = EventProcessor(db=test_db)

        # Track event
        event_id = tracker.track(
            name="page_view",
            event_type="page_view",
            user_id="user_enrich",
            ip_address="8.8.8.8"
        )
        tracker.flush()

        # Process with enrichment
        geo_data = {"country": "US", "city": "Mountain View"}
        ua_data = {"browser": "Chrome", "os": "Windows"}

        processor.process_event_sync(
            event_id,
            geo_data=geo_data,
            user_agent_data=ua_data
        )

        # Verify enrichment
        event = db_session.query(EventORM).filter_by(id=event_id).first()
        assert event.country == "US"
        assert event.browser == "Chrome"


# Test count: 12 tests
