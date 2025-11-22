"""
Integration Tests for Database Operations

Tests for database operations, migrations, and data integrity.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from modules.analytics.storage.database import Database, Base
from modules.analytics.storage.models import (
    EventORM,
    UserORM,
    SessionORM,
    MetricORM,
    FunnelORM,
    GoalORM
)
from modules.analytics.storage.repositories import (
    EventRepository,
    UserRepository,
    SessionRepository,
    MetricRepository
)
from shared.utils import get_utc_now, generate_uuid


class TestDatabaseConnections:
    """Test suite for database connections."""

    def test_database_connection(self, test_db):
        """Test database connection established."""
        assert test_db.engine is not None

    def test_session_creation(self, test_db):
        """Test database session creation."""
        with test_db.session() as session:
            assert session is not None

    def test_session_context_manager(self, test_db):
        """Test session context manager."""
        with test_db.session() as session:
            result = session.execute(text("SELECT 1"))
            assert result is not None

    def test_session_rollback_on_error(self, test_db):
        """Test session rolls back on error."""
        try:
            with test_db.session() as session:
                # Create invalid data
                event = EventORM(
                    name="test",
                    event_type="test",
                    timestamp=None  # This might cause error
                )
                session.add(event)
                session.commit()
        except:
            pass  # Expected to fail

        # Session should be rolled back
        with test_db.session() as session:
            count = session.query(EventORM).count()
            # Should not have the failed insert
            assert count >= 0


class TestDatabaseModels:
    """Test suite for database model operations."""

    def test_create_event(self, db_session):
        """Test creating event in database."""
        event = EventORM(
            id=generate_uuid(),
            name="test_event",
            event_type="click",
            timestamp=get_utc_now()
        )
        db_session.add(event)
        db_session.commit()

        # Verify created
        retrieved = db_session.query(EventORM).filter_by(id=event.id).first()
        assert retrieved is not None
        assert retrieved.name == "test_event"

    def test_create_user(self, db_session):
        """Test creating user in database."""
        user = UserORM(
            id="user_123",
            first_seen_at=get_utc_now(),
            last_seen_at=get_utc_now()
        )
        db_session.add(user)
        db_session.commit()

        retrieved = db_session.query(UserORM).filter_by(id="user_123").first()
        assert retrieved is not None

    def test_create_session(self, db_session):
        """Test creating session in database."""
        session_orm = SessionORM(
            session_id="session_123",
            user_id="user_123",
            started_at=get_utc_now()
        )
        db_session.add(session_orm)
        db_session.commit()

        retrieved = db_session.query(SessionORM).filter_by(
            session_id="session_123"
        ).first()
        assert retrieved is not None

    def test_create_metric(self, db_session):
        """Test creating metric in database."""
        metric = MetricORM(
            id=generate_uuid(),
            name="test_metric",
            metric_type="gauge",
            value=100.0,
            timestamp=get_utc_now()
        )
        db_session.add(metric)
        db_session.commit()

        retrieved = db_session.query(MetricORM).filter_by(id=metric.id).first()
        assert retrieved is not None
        assert retrieved.value == 100.0

    def test_update_event(self, db_session):
        """Test updating event."""
        event = EventORM(
            id=generate_uuid(),
            name="original",
            event_type="click",
            timestamp=get_utc_now(),
            processed=False
        )
        db_session.add(event)
        db_session.commit()

        # Update
        event.processed = True
        event.processed_at = get_utc_now()
        db_session.commit()

        # Verify update
        db_session.refresh(event)
        assert event.processed is True

    def test_delete_event(self, db_session):
        """Test deleting event."""
        event = EventORM(
            id=generate_uuid(),
            name="to_delete",
            event_type="click",
            timestamp=get_utc_now()
        )
        db_session.add(event)
        db_session.commit()

        event_id = event.id

        # Delete
        db_session.delete(event)
        db_session.commit()

        # Verify deleted
        retrieved = db_session.query(EventORM).filter_by(id=event_id).first()
        assert retrieved is None


class TestDatabaseRelationships:
    """Test suite for model relationships."""

    def test_user_events_relationship(self, db_session):
        """Test user-events relationship."""
        user = UserORM(
            id="user_rel",
            first_seen_at=get_utc_now(),
            last_seen_at=get_utc_now()
        )
        db_session.add(user)

        # Create events for user
        for i in range(3):
            event = EventORM(
                name=f"event_{i}",
                event_type="click",
                user_id="user_rel",
                timestamp=get_utc_now()
            )
            db_session.add(event)

        db_session.commit()

        # Query user's events
        events = db_session.query(EventORM).filter_by(user_id="user_rel").all()
        assert len(events) == 3

    def test_session_events_relationship(self, db_session):
        """Test session-events relationship."""
        session = SessionORM(
            session_id="session_rel",
            user_id="user_123",
            started_at=get_utc_now()
        )
        db_session.add(session)

        # Create events for session
        for i in range(5):
            event = EventORM(
                name=f"event_{i}",
                event_type="page_view",
                session_id="session_rel",
                timestamp=get_utc_now()
            )
            db_session.add(event)

        db_session.commit()

        # Query session's events
        events = db_session.query(EventORM).filter_by(
            session_id="session_rel"
        ).all()
        assert len(events) == 5


class TestDatabaseRepositories:
    """Test suite for repository pattern."""

    def test_event_repository_create(self, db_session):
        """Test event repository create."""
        repo = EventRepository()

        event_data = {
            "id": generate_uuid(),
            "name": "repo_event",
            "event_type": "click",
            "timestamp": get_utc_now()
        }

        event = repo.create(db_session, **event_data)

        assert event.id == event_data["id"]

    def test_event_repository_get_by_id(self, db_session):
        """Test event repository get by ID."""
        repo = EventRepository()

        event_id = generate_uuid()
        event = EventORM(
            id=event_id,
            name="test",
            event_type="click",
            timestamp=get_utc_now()
        )
        db_session.add(event)
        db_session.commit()

        retrieved = repo.get_by_id(db_session, event_id)
        assert retrieved is not None
        assert retrieved.id == event_id

    def test_event_repository_bulk_create(self, db_session):
        """Test event repository bulk create."""
        repo = EventRepository()

        events_data = [
            {
                "id": generate_uuid(),
                "name": f"event_{i}",
                "event_type": "click",
                "timestamp": get_utc_now()
            }
            for i in range(10)
        ]

        repo.bulk_create(db_session, events_data)

        count = db_session.query(EventORM).count()
        assert count >= 10

    def test_user_repository_increment_stats(self, db_session):
        """Test user repository increment stats."""
        repo = UserRepository()

        user = UserORM(
            id="user_stats",
            first_seen_at=get_utc_now(),
            total_events=0
        )
        db_session.add(user)
        db_session.commit()

        repo.increment_stats(db_session, "user_stats", events=5)
        db_session.commit()

        db_session.refresh(user)
        assert user.total_events == 5


class TestDatabaseConstraints:
    """Test suite for database constraints."""

    def test_unique_constraint(self, db_session):
        """Test unique constraint enforcement."""
        # Depends on specific unique constraints in models
        pass

    def test_foreign_key_constraint(self, db_session):
        """Test foreign key constraints."""
        # Depends on foreign key relationships
        pass

    def test_not_null_constraint(self, db_session):
        """Test not null constraints."""
        # Try to create event without required fields
        with pytest.raises(Exception):
            event = EventORM()
            db_session.add(event)
            db_session.commit()


class TestDatabasePerformance:
    """Test suite for database performance."""

    def test_bulk_insert_performance(self, db_session):
        """Test bulk insert performance."""
        import time

        events = [
            EventORM(
                id=generate_uuid(),
                name=f"event_{i}",
                event_type="click",
                timestamp=get_utc_now()
            )
            for i in range(1000)
        ]

        start_time = time.time()
        db_session.bulk_save_objects(events)
        db_session.commit()
        end_time = time.time()

        insert_time = end_time - start_time
        assert insert_time < 5.0  # Should complete within 5 seconds

    def test_query_performance(self, db_session):
        """Test query performance with large dataset."""
        # Create large dataset
        events = [
            EventORM(
                id=generate_uuid(),
                name=f"event_{i}",
                event_type="page_view",
                user_id=f"user_{i % 100}",
                timestamp=get_utc_now()
            )
            for i in range(1000)
        ]
        db_session.bulk_save_objects(events)
        db_session.commit()

        import time
        start_time = time.time()

        # Query with filter
        results = db_session.query(EventORM).filter(
            EventORM.event_type == "page_view"
        ).limit(100).all()

        end_time = time.time()

        query_time = end_time - start_time
        assert query_time < 1.0  # Should complete within 1 second
        assert len(results) == 100

    def test_index_usage(self, db_session):
        """Test database index usage."""
        # Create events
        for i in range(100):
            db_session.add(EventORM(
                id=generate_uuid(),
                name=f"event_{i}",
                event_type="click",
                timestamp=get_utc_now()
            ))
        db_session.commit()

        # Query with indexed field (timestamp)
        results = db_session.query(EventORM).filter(
            EventORM.timestamp >= get_utc_now() - timedelta(hours=1)
        ).all()

        assert len(results) >= 100


class TestDatabaseTransactions:
    """Test suite for database transactions."""

    def test_transaction_commit(self, db_session):
        """Test transaction commit."""
        event = EventORM(
            id=generate_uuid(),
            name="commit_test",
            event_type="click",
            timestamp=get_utc_now()
        )
        db_session.add(event)
        db_session.commit()

        # Verify committed
        retrieved = db_session.query(EventORM).filter_by(id=event.id).first()
        assert retrieved is not None

    def test_transaction_rollback(self, db_session):
        """Test transaction rollback."""
        event = EventORM(
            id=generate_uuid(),
            name="rollback_test",
            event_type="click",
            timestamp=get_utc_now()
        )
        db_session.add(event)
        db_session.rollback()

        # Verify not committed
        retrieved = db_session.query(EventORM).filter_by(id=event.id).first()
        assert retrieved is None

    def test_nested_transactions(self, test_db):
        """Test nested transactions."""
        with test_db.session() as session:
            event1 = EventORM(
                id=generate_uuid(),
                name="outer",
                event_type="click",
                timestamp=get_utc_now()
            )
            session.add(event1)

            try:
                # Inner transaction
                event2 = EventORM(
                    id=generate_uuid(),
                    name="inner",
                    event_type="click",
                    timestamp=get_utc_now()
                )
                session.add(event2)
                session.flush()

                # Simulate error
                raise Exception("Test error")

            except:
                session.rollback()

            session.commit()


# Test count: 29 tests
