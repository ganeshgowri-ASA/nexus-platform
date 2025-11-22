"""
Event Tracker

Event tracking system with batching and validation.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from queue import Queue
import threading
import time

from pydantic import ValidationError

from modules.analytics.models.event import Event, EventCreate, EventBatch
from modules.analytics.storage.database import Database
from modules.analytics.storage.repositories import EventRepository
from shared.constants import MAX_BATCH_SIZE
from shared.utils import generate_uuid, get_utc_now

logger = logging.getLogger(__name__)


class EventTracker:
    """
    Event tracking system with batching and validation.

    Features:
    - Event validation
    - Batch processing
    - Async event queue
    - Auto-enrichment
    """

    def __init__(
        self,
        db: Database,
        batch_size: int = 100,
        flush_interval: int = 5,
        auto_start: bool = True,
    ):
        """
        Initialize event tracker.

        Args:
            db: Database instance
            batch_size: Number of events per batch
            flush_interval: Flush interval in seconds
            auto_start: Auto-start background worker
        """
        self.db = db
        self.batch_size = min(batch_size, MAX_BATCH_SIZE)
        self.flush_interval = flush_interval
        self.repository = EventRepository()

        # Event queue
        self._queue: Queue = Queue()
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None
        self._last_flush = time.time()

        if auto_start:
            self.start()

        logger.info(
            f"Event tracker initialized: batch_size={self.batch_size}, "
            f"flush_interval={self.flush_interval}s"
        )

    def track(
        self,
        name: str,
        event_type: str,
        properties: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs
    ) -> Optional[str]:
        """
        Track an event.

        Args:
            name: Event name
            event_type: Event type
            properties: Event properties
            user_id: User ID
            session_id: Session ID
            **kwargs: Additional event fields

        Returns:
            Event ID if successful, None otherwise

        Example:
            >>> tracker.track("button_click", "click", {"button_id": "submit"})
        """
        try:
            # Create event data
            event_data = {
                "name": name,
                "event_type": event_type,
                "properties": properties or {},
                "user_id": user_id,
                "session_id": session_id,
                **kwargs,
            }

            # Validate event
            event_create = EventCreate(**event_data)

            # Generate event ID
            event_id = generate_uuid()

            # Add to queue
            self._queue.put((event_id, event_create))

            logger.debug(f"Event tracked: {name} ({event_type})")
            return event_id

        except ValidationError as e:
            logger.error(f"Event validation error: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Error tracking event: {e}", exc_info=True)
            return None

    def track_batch(self, events: List[EventCreate]) -> bool:
        """
        Track multiple events at once.

        Args:
            events: List of events to track

        Returns:
            True if successful

        Example:
            >>> events = [EventCreate(...), EventCreate(...)]
            >>> tracker.track_batch(events)
        """
        try:
            # Validate batch
            batch = EventBatch(events=events)

            # Add events to queue
            for event in events:
                event_id = generate_uuid()
                self._queue.put((event_id, event))

            logger.info(f"Batch tracked: {len(events)} events")
            return True

        except ValidationError as e:
            logger.error(f"Batch validation error: {e}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Error tracking batch: {e}", exc_info=True)
            return False

    def flush(self) -> int:
        """
        Flush events from queue to database.

        Returns:
            Number of events flushed

        Example:
            >>> count = tracker.flush()
        """
        if self._queue.empty():
            return 0

        events_to_save = []

        # Collect events from queue
        while not self._queue.empty() and len(events_to_save) < self.batch_size:
            try:
                event_id, event_create = self._queue.get_nowait()

                # Convert to full event
                event_data = event_create.model_dump()
                event_data["id"] = event_id
                event_data["timestamp"] = event_data.get("timestamp") or get_utc_now()

                events_to_save.append(event_data)

            except Exception as e:
                logger.error(f"Error processing event from queue: {e}")
                continue

        if not events_to_save:
            return 0

        # Save to database
        try:
            with self.db.session() as session:
                self.repository.bulk_create(session, events_to_save)
                session.commit()

            count = len(events_to_save)
            logger.info(f"Flushed {count} events to database")
            self._last_flush = time.time()
            return count

        except Exception as e:
            logger.error(f"Error flushing events to database: {e}", exc_info=True)
            return 0

    def start(self) -> None:
        """
        Start background worker thread.

        Example:
            >>> tracker.start()
        """
        if self._running:
            logger.warning("Event tracker already running")
            return

        self._running = True
        self._worker_thread = threading.Thread(target=self._worker, daemon=True)
        self._worker_thread.start()

        logger.info("Event tracker worker started")

    def stop(self, flush_remaining: bool = True) -> None:
        """
        Stop background worker thread.

        Args:
            flush_remaining: Flush remaining events before stopping

        Example:
            >>> tracker.stop()
        """
        if not self._running:
            return

        self._running = False

        if flush_remaining:
            self.flush()

        if self._worker_thread:
            self._worker_thread.join(timeout=10)

        logger.info("Event tracker worker stopped")

    def _worker(self) -> None:
        """Background worker thread."""
        logger.info("Event tracker worker thread started")

        while self._running:
            try:
                # Check if we should flush
                should_flush = (
                    self._queue.qsize() >= self.batch_size
                    or (time.time() - self._last_flush) >= self.flush_interval
                )

                if should_flush:
                    self.flush()

                # Sleep briefly
                time.sleep(0.1)

            except Exception as e:
                logger.error(f"Error in worker thread: {e}", exc_info=True)
                time.sleep(1)

        logger.info("Event tracker worker thread stopped")

    def get_queue_size(self) -> int:
        """
        Get current queue size.

        Returns:
            Number of events in queue

        Example:
            >>> size = tracker.get_queue_size()
        """
        return self._queue.qsize()

    def is_running(self) -> bool:
        """
        Check if tracker is running.

        Returns:
            True if running

        Example:
            >>> if tracker.is_running():
            ...     print("Tracker is running")
        """
        return self._running

    def enrich_event(
        self,
        event_data: Dict[str, Any],
        request: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Enrich event with additional data.

        Args:
            event_data: Event data
            request: Optional HTTP request object

        Returns:
            Enriched event data

        Example:
            >>> enriched = tracker.enrich_event(event_data, request)
        """
        if request is None:
            return event_data

        # Extract data from request
        try:
            # User agent
            if not event_data.get("user_agent") and hasattr(request, "headers"):
                event_data["user_agent"] = request.headers.get("User-Agent")

            # IP address
            if not event_data.get("ip_address"):
                if hasattr(request, "client"):
                    event_data["ip_address"] = request.client.host
                elif hasattr(request, "remote_addr"):
                    event_data["ip_address"] = request.remote_addr

            # Referrer
            if not event_data.get("referrer") and hasattr(request, "headers"):
                event_data["referrer"] = request.headers.get("Referer")

            # Page URL
            if not event_data.get("page_url") and hasattr(request, "url"):
                event_data["page_url"] = str(request.url)

        except Exception as e:
            logger.error(f"Error enriching event: {e}")

        return event_data

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop(flush_remaining=True)
