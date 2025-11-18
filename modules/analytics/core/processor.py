"""
Event Processor

Event processing with async workers.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from modules.analytics.storage.database import Database
from modules.analytics.storage.models import EventORM
from modules.analytics.storage.repositories import (
    EventRepository,
    GoalConversionRepository,
    GoalRepository,
    SessionRepository,
    UserRepository,
)
from shared.utils import get_utc_now

logger = logging.getLogger(__name__)


class EventProcessor:
    """
    Event processor for analytics data.

    Features:
    - Event enrichment
    - Goal tracking
    - User/session updates
    - Real-time processing
    """

    def __init__(self, db: Database):
        """
        Initialize event processor.

        Args:
            db: Database instance
        """
        self.db = db
        self.event_repo = EventRepository()
        self.user_repo = UserRepository()
        self.session_repo = SessionRepository()
        self.goal_repo = GoalRepository()
        self.conversion_repo = GoalConversionRepository()

        logger.info("Event processor initialized")

    def process_events(self, batch_size: int = 1000) -> int:
        """
        Process unprocessed events.

        Args:
            batch_size: Number of events to process

        Returns:
            Number of events processed
        """
        try:
            with self.db.session() as session:
                # Get unprocessed events
                events = self.event_repo.get_unprocessed(session, limit=batch_size)

                if not events:
                    return 0

                event_ids = []

                for event in events:
                    try:
                        # Process individual event
                        self._process_event(session, event)
                        event_ids.append(event.id)

                    except Exception as e:
                        logger.error(f"Error processing event {event.id}: {e}")
                        continue

                # Mark as processed
                if event_ids:
                    self.event_repo.mark_processed(session, event_ids)
                    session.commit()

                logger.info(f"Processed {len(event_ids)} events")
                return len(event_ids)

        except Exception as e:
            logger.error(f"Error in process_events: {e}", exc_info=True)
            return 0

    def _process_event(self, session: Session, event: EventORM) -> None:
        """
        Process a single event.

        Args:
            session: Database session
            event: Event to process
        """
        # Update user stats
        if event.user_id:
            self._update_user_stats(session, event)

        # Update session stats
        if event.session_id:
            self._update_session_stats(session, event)

        # Check for goal conversions
        self._check_goal_conversions(session, event)

        logger.debug(f"Processed event: {event.id}")

    def _update_user_stats(self, session: Session, event: EventORM) -> None:
        """
        Update user statistics.

        Args:
            session: Database session
            event: Event
        """
        try:
            user = self.user_repo.get_by_id(session, event.user_id)
            if not user:
                # Create user if doesn't exist
                user = self.user_repo.create(
                    session,
                    id=event.user_id,
                    first_seen_at=event.timestamp,
                    last_seen_at=event.timestamp,
                )

            # Update stats
            self.user_repo.increment_stats(
                session,
                event.user_id,
                events=1,
            )

        except Exception as e:
            logger.error(f"Error updating user stats: {e}")

    def _update_session_stats(self, session: Session, event: EventORM) -> None:
        """
        Update session statistics.

        Args:
            session: Database session
            event: Event
        """
        try:
            sess = self.session_repo.get_by_id(session, event.session_id)
            if not sess:
                return

            # Update last activity
            sess.last_activity_at = event.timestamp
            sess.events_count += 1

            # Update page views for page_view events
            if event.event_type == "page_view":
                sess.page_views += 1

            # Update duration
            if sess.started_at and sess.last_activity_at:
                duration = (sess.last_activity_at - sess.started_at).total_seconds()
                sess.duration_seconds = int(duration)

            # Check if bounce (single page view, < 30 seconds)
            if sess.page_views == 1 and sess.duration_seconds < 30:
                sess.is_bounce = True

            session.flush()

        except Exception as e:
            logger.error(f"Error updating session stats: {e}")

    def _check_goal_conversions(self, session: Session, event: EventORM) -> None:
        """
        Check if event triggers goal conversions.

        Args:
            session: Database session
            event: Event
        """
        try:
            # Get enabled goals for this event type
            goals = session.query(self.goal_repo.model).filter(
                self.goal_repo.model.enabled == True,
                self.goal_repo.model.event_type == event.event_type,
            ).all()

            for goal in goals:
                # Check if conditions are met
                if self._check_goal_conditions(goal.conditions, event):
                    # Create conversion
                    self.conversion_repo.create(
                        session,
                        goal_id=goal.id,
                        user_id=event.user_id,
                        session_id=event.session_id,
                        event_id=event.id,
                        value=goal.value,
                        properties=event.properties,
                        converted_at=event.timestamp,
                    )

                    # Update goal stats
                    self.goal_repo.increment_conversions(
                        session,
                        goal.id,
                        value=goal.value or 0.0,
                    )

                    # Update session conversion
                    if event.session_id:
                        sess = self.session_repo.get_by_id(session, event.session_id)
                        if sess:
                            sess.converted = True
                            sess.conversion_value = (sess.conversion_value or 0) + (goal.value or 0)

                    # Update user conversions
                    if event.user_id:
                        self.user_repo.increment_stats(
                            session,
                            event.user_id,
                            conversions=1,
                            value=goal.value or 0.0,
                        )

                    logger.info(f"Goal conversion: {goal.name} for user {event.user_id}")

        except Exception as e:
            logger.error(f"Error checking goal conversions: {e}")

    def _check_goal_conditions(
        self,
        conditions: Dict[str, Any],
        event: EventORM,
    ) -> bool:
        """
        Check if event meets goal conditions.

        Args:
            conditions: Goal conditions
            event: Event

        Returns:
            True if conditions met
        """
        if not conditions:
            return True

        try:
            for key, expected_value in conditions.items():
                # Check event properties
                if key in event.properties:
                    actual_value = event.properties[key]
                    if actual_value != expected_value:
                        return False
                # Check event fields
                elif hasattr(event, key):
                    actual_value = getattr(event, key)
                    if actual_value != expected_value:
                        return False
                else:
                    return False

            return True

        except Exception as e:
            logger.error(f"Error checking goal conditions: {e}")
            return False

    def enrich_event_data(
        self,
        event: EventORM,
        geo_data: Optional[Dict[str, Any]] = None,
        user_agent_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Enrich event with additional data.

        Args:
            event: Event to enrich
            geo_data: Geographic data
            user_agent_data: User agent parsed data
        """
        try:
            # Add geographic data
            if geo_data:
                event.country = geo_data.get("country")
                event.city = geo_data.get("city")

            # Add user agent data
            if user_agent_data:
                event.browser = user_agent_data.get("browser")
                event.os = user_agent_data.get("os")
                event.device_type = user_agent_data.get("device_type")

        except Exception as e:
            logger.error(f"Error enriching event: {e}")

    def process_event_sync(
        self,
        event_id: str,
        geo_data: Optional[Dict[str, Any]] = None,
        user_agent_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Process a single event synchronously.

        Args:
            event_id: Event ID
            geo_data: Geographic data
            user_agent_data: User agent data

        Returns:
            True if successful
        """
        try:
            with self.db.session() as session:
                event = self.event_repo.get_by_id(session, event_id)
                if not event:
                    return False

                # Enrich
                if geo_data or user_agent_data:
                    self.enrich_event_data(event, geo_data, user_agent_data)

                # Process
                self._process_event(session, event)

                # Mark as processed
                event.processed = True
                event.processed_at = get_utc_now()

                session.commit()
                return True

        except Exception as e:
            logger.error(f"Error processing event {event_id}: {e}", exc_info=True)
            return False
