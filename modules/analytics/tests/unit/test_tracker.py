"""
Unit Tests for Event Tracker

Tests for event tracking system with batching and validation.
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from modules.analytics.core.tracker import EventTracker
from modules.analytics.models.event import EventCreate, EventBatch
from shared.utils import generate_uuid, get_utc_now


class TestEventTracker:
    """Test suite for EventTracker class."""

    def test_tracker_initialization(self, tracker):
        """Test tracker initializes with correct settings."""
        assert tracker.batch_size == 10
        assert tracker.flush_interval == 5
        assert not tracker.is_running()

    def test_tracker_auto_start(self, test_db):
        """Test tracker auto-starts when enabled."""
        tracker = EventTracker(db=test_db, auto_start=True)
        time.sleep(0.2)  # Give thread time to start
        assert tracker.is_running()
        tracker.stop()

    def test_track_event_success(self, tracker, sample_event_data):
        """Test successful event tracking."""
        event_id = tracker.track(**sample_event_data)

        assert event_id is not None
        assert tracker.get_queue_size() == 1

    def test_track_event_validation_error(self, tracker):
        """Test tracking with invalid event data."""
        event_id = tracker.track(
            name="",  # Invalid: empty name
            event_type="page_view"
        )

        assert event_id is None
        assert tracker.get_queue_size() == 0

    def test_track_event_with_defaults(self, tracker):
        """Test tracking event with minimal data."""
        event_id = tracker.track(
            name="simple_event",
            event_type="click"
        )

        assert event_id is not None
        assert tracker.get_queue_size() == 1

    def test_track_event_with_kwargs(self, tracker):
        """Test tracking event with extra kwargs."""
        event_id = tracker.track(
            name="test_event",
            event_type="page_view",
            user_id="user_123",
            session_id="session_456",
            custom_field="custom_value"
        )

        assert event_id is not None

    def test_track_batch_success(self, tracker, sample_events_batch):
        """Test batch event tracking."""
        events = [EventCreate(**e) for e in sample_events_batch]
        success = tracker.track_batch(events)

        assert success is True
        assert tracker.get_queue_size() == len(events)

    def test_track_batch_validation_error(self, tracker):
        """Test batch tracking with invalid data."""
        events = [EventCreate(name="", event_type="click")]  # Invalid
        success = tracker.track_batch(events)

        assert success is False

    def test_track_batch_empty(self, tracker):
        """Test batch tracking with empty list."""
        success = tracker.track_batch([])
        assert success is False

    def test_flush_events(self, tracker, sample_event_data, db_session):
        """Test flushing events to database."""
        # Track multiple events
        for i in range(5):
            tracker.track(**sample_event_data)

        assert tracker.get_queue_size() == 5

        # Flush events
        count = tracker.flush()

        assert count == 5
        assert tracker.get_queue_size() == 0

    def test_flush_empty_queue(self, tracker):
        """Test flushing with empty queue."""
        count = tracker.flush()
        assert count == 0

    def test_flush_respects_batch_size(self, tracker, sample_event_data):
        """Test flush respects batch size limit."""
        # Track more events than batch size
        for i in range(15):
            tracker.track(**sample_event_data)

        assert tracker.get_queue_size() == 15

        # Flush should only process batch_size events
        count = tracker.flush()

        assert count == 10
        assert tracker.get_queue_size() == 5

    def test_start_worker_thread(self, tracker):
        """Test starting background worker."""
        assert not tracker.is_running()

        tracker.start()
        time.sleep(0.2)

        assert tracker.is_running()
        tracker.stop()

    def test_start_already_running(self, tracker):
        """Test starting worker when already running."""
        tracker.start()
        time.sleep(0.2)

        # Try starting again
        tracker.start()  # Should log warning

        assert tracker.is_running()
        tracker.stop()

    def test_stop_worker_thread(self, tracker):
        """Test stopping background worker."""
        tracker.start()
        time.sleep(0.2)
        assert tracker.is_running()

        tracker.stop()
        time.sleep(0.2)

        assert not tracker.is_running()

    def test_stop_with_flush(self, tracker, sample_event_data):
        """Test stopping with flush_remaining=True."""
        tracker.track(**sample_event_data)
        assert tracker.get_queue_size() == 1

        tracker.stop(flush_remaining=True)

        # Queue should be empty after flush
        assert tracker.get_queue_size() == 0

    def test_stop_without_flush(self, tracker, sample_event_data):
        """Test stopping without flushing."""
        tracker.track(**sample_event_data)
        assert tracker.get_queue_size() == 1

        tracker.stop(flush_remaining=False)

        # Queue should still have events
        assert tracker.get_queue_size() == 1

    def test_worker_auto_flush_on_batch_size(self, test_db, sample_event_data):
        """Test worker auto-flushes when batch size reached."""
        tracker = EventTracker(db=test_db, batch_size=5, auto_start=True)

        # Track batch_size events
        for i in range(5):
            tracker.track(**sample_event_data)

        # Wait for auto-flush
        time.sleep(0.5)

        # Queue should be flushed
        assert tracker.get_queue_size() == 0
        tracker.stop()

    def test_worker_auto_flush_on_interval(self, test_db, sample_event_data):
        """Test worker auto-flushes after interval."""
        tracker = EventTracker(db=test_db, flush_interval=1, auto_start=True)

        # Track a few events
        tracker.track(**sample_event_data)

        # Wait for flush interval
        time.sleep(1.5)

        # Queue should be flushed
        assert tracker.get_queue_size() == 0
        tracker.stop()

    def test_enrich_event_with_request(self, tracker):
        """Test event enrichment from request object."""
        mock_request = Mock()
        mock_request.headers = {"User-Agent": "Test Browser", "Referer": "https://example.com"}
        mock_request.client.host = "127.0.0.1"
        mock_request.url = "https://example.com/page"

        event_data = {"name": "test", "event_type": "page_view"}
        enriched = tracker.enrich_event(event_data, mock_request)

        assert enriched["user_agent"] == "Test Browser"
        assert enriched["referrer"] == "https://example.com"
        assert enriched["ip_address"] == "127.0.0.1"
        assert enriched["page_url"] == "https://example.com/page"

    def test_enrich_event_without_request(self, tracker):
        """Test enrichment without request object."""
        event_data = {"name": "test", "event_type": "page_view"}
        enriched = tracker.enrich_event(event_data, None)

        assert enriched == event_data

    def test_enrich_event_preserves_existing(self, tracker):
        """Test enrichment preserves existing values."""
        mock_request = Mock()
        mock_request.headers = {"User-Agent": "Test Browser"}

        event_data = {
            "name": "test",
            "event_type": "page_view",
            "user_agent": "Custom Agent"
        }
        enriched = tracker.enrich_event(event_data, mock_request)

        assert enriched["user_agent"] == "Custom Agent"

    def test_context_manager(self, test_db, sample_event_data):
        """Test tracker as context manager."""
        with EventTracker(db=test_db, auto_start=False) as tracker:
            tracker.track(**sample_event_data)
            assert tracker.get_queue_size() == 1

        # Should flush on exit
        # Note: Queue size check would need to happen inside context

    def test_get_queue_size(self, tracker, sample_event_data):
        """Test queue size tracking."""
        assert tracker.get_queue_size() == 0

        tracker.track(**sample_event_data)
        assert tracker.get_queue_size() == 1

        tracker.track(**sample_event_data)
        assert tracker.get_queue_size() == 2

    def test_concurrent_tracking(self, tracker, sample_event_data):
        """Test concurrent event tracking."""
        import threading

        def track_events():
            for i in range(10):
                tracker.track(**sample_event_data)

        threads = [threading.Thread(target=track_events) for _ in range(3)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        assert tracker.get_queue_size() == 30

    @pytest.mark.parametrize("batch_size", [10, 50, 100])
    def test_different_batch_sizes(self, test_db, batch_size, sample_event_data):
        """Test tracker with different batch sizes."""
        tracker = EventTracker(db=test_db, batch_size=batch_size, auto_start=False)

        assert tracker.batch_size == batch_size

        # Track events
        for i in range(batch_size + 5):
            tracker.track(**sample_event_data)

        # Flush should process batch_size events
        count = tracker.flush()
        assert count == batch_size

    @pytest.mark.parametrize("event_type", ["page_view", "click", "form_submit"])
    def test_different_event_types(self, tracker, event_type):
        """Test tracking different event types."""
        event_id = tracker.track(
            name=f"test_{event_type}",
            event_type=event_type,
            user_id="user_123"
        )

        assert event_id is not None


# Test count: 32 tests
