"""
Unit Tests for Funnel Analysis Engine

Tests for funnel analysis and conversion tracking.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from modules.analytics.processing.funnel import FunnelEngine
from modules.analytics.models.funnel import FunnelAnalysis, FunnelStepStats
from modules.analytics.storage.models import EventORM, FunnelORM, FunnelStepORM
from shared.utils import get_utc_now, generate_uuid


class TestFunnelEngine:
    """Test suite for FunnelEngine class."""

    def test_funnel_engine_initialization(self, funnel_engine):
        """Test funnel engine initializes correctly."""
        assert funnel_engine.db is not None
        assert funnel_engine.repository is not None

    def test_analyze_funnel_basic(self, funnel_engine, db_session):
        """Test basic funnel analysis."""
        now = get_utc_now()

        # Create funnel
        funnel = FunnelORM(
            id=generate_uuid(),
            name="Test Funnel",
            description="Test funnel"
        )
        db_session.add(funnel)

        # Create funnel steps
        steps = [
            FunnelStepORM(
                id=generate_uuid(),
                funnel_id=funnel.id,
                name="Step 1",
                event_type="page_view",
                order=0
            ),
            FunnelStepORM(
                id=generate_uuid(),
                funnel_id=funnel.id,
                name="Step 2",
                event_type="click",
                order=1
            )
        ]
        funnel.steps = steps
        db_session.commit()

        # Create events
        for i in range(10):
            # All users complete step 1
            db_session.add(EventORM(
                name="page_view",
                event_type="page_view",
                user_id=f"user_{i}",
                timestamp=now
            ))
            # Half complete step 2
            if i < 5:
                db_session.add(EventORM(
                    name="click",
                    event_type="click",
                    user_id=f"user_{i}",
                    timestamp=now + timedelta(seconds=30)
                ))
        db_session.commit()

        # Analyze funnel
        analysis = funnel_engine.analyze_funnel(
            funnel.id,
            now - timedelta(hours=1),
            now + timedelta(hours=1)
        )

        assert analysis is not None
        assert analysis.funnel_id == funnel.id
        assert analysis.total_entered == 10
        assert analysis.total_completed == 5
        assert analysis.overall_conversion_rate == 50.0

    def test_analyze_funnel_not_found(self, funnel_engine, db_session):
        """Test analysis with non-existent funnel."""
        result = funnel_engine.analyze_funnel(
            "nonexistent_id",
            get_utc_now(),
            get_utc_now() + timedelta(days=1)
        )

        assert result is None

    def test_analyze_funnel_no_users(self, funnel_engine, db_session):
        """Test analysis with no users entering funnel."""
        funnel = FunnelORM(
            id=generate_uuid(),
            name="Empty Funnel",
            description="No users"
        )
        funnel.steps = [
            FunnelStepORM(
                id=generate_uuid(),
                funnel_id=funnel.id,
                name="Step 1",
                event_type="rare_event",
                order=0
            )
        ]
        db_session.add(funnel)
        db_session.commit()

        analysis = funnel_engine.analyze_funnel(
            funnel.id,
            get_utc_now(),
            get_utc_now() + timedelta(days=1)
        )

        assert analysis.total_entered == 0
        assert analysis.total_completed == 0

    def test_analyze_funnel_multi_step(self, funnel_engine, db_session):
        """Test multi-step funnel analysis."""
        now = get_utc_now()

        funnel = FunnelORM(
            id=generate_uuid(),
            name="Checkout Funnel"
        )
        funnel.steps = [
            FunnelStepORM(id=generate_uuid(), funnel_id=funnel.id,
                         name="View", event_type="product_view", order=0),
            FunnelStepORM(id=generate_uuid(), funnel_id=funnel.id,
                         name="Cart", event_type="add_to_cart", order=1),
            FunnelStepORM(id=generate_uuid(), funnel_id=funnel.id,
                         name="Checkout", event_type="checkout", order=2),
            FunnelStepORM(id=generate_uuid(), funnel_id=funnel.id,
                         name="Purchase", event_type="purchase", order=3)
        ]
        db_session.add(funnel)
        db_session.commit()

        # Create funnel flow
        users = 100
        for i in range(users):
            db_session.add(EventORM(
                name="view", event_type="product_view",
                user_id=f"user_{i}", timestamp=now
            ))
            if i < 80:  # 80% add to cart
                db_session.add(EventORM(
                    name="cart", event_type="add_to_cart",
                    user_id=f"user_{i}", timestamp=now + timedelta(seconds=10)
                ))
            if i < 50:  # 50% checkout
                db_session.add(EventORM(
                    name="checkout", event_type="checkout",
                    user_id=f"user_{i}", timestamp=now + timedelta(seconds=20)
                ))
            if i < 30:  # 30% purchase
                db_session.add(EventORM(
                    name="purchase", event_type="purchase",
                    user_id=f"user_{i}", timestamp=now + timedelta(seconds=30)
                ))
        db_session.commit()

        analysis = funnel_engine.analyze_funnel(
            funnel.id,
            now - timedelta(hours=1),
            now + timedelta(hours=1)
        )

        assert analysis.total_entered == 100
        assert len(analysis.steps) == 4
        assert analysis.overall_conversion_rate == 30.0

    def test_get_step_users(self, funnel_engine, db_session):
        """Test getting users for a funnel step."""
        now = get_utc_now()

        # Create events
        for i in range(5):
            db_session.add(EventORM(
                name="page_view",
                event_type="page_view",
                user_id=f"user_{i}",
                timestamp=now
            ))
        db_session.commit()

        users = funnel_engine._get_step_users(
            db_session,
            "page_view",
            now - timedelta(hours=1),
            now + timedelta(hours=1)
        )

        assert len(users) == 5

    def test_get_step_users_no_matches(self, funnel_engine, db_session):
        """Test getting step users with no matches."""
        users = funnel_engine._get_step_users(
            db_session,
            "nonexistent_event",
            get_utc_now(),
            get_utc_now() + timedelta(days=1)
        )

        assert len(users) == 0

    def test_get_step_completers(self, funnel_engine, db_session):
        """Test getting users who completed a step."""
        now = get_utc_now()

        # Create events
        entered_users = {f"user_{i}" for i in range(10)}

        for i in range(5):  # Only half complete
            db_session.add(EventORM(
                name="click",
                event_type="click",
                user_id=f"user_{i}",
                timestamp=now
            ))
        db_session.commit()

        completers = funnel_engine._get_step_completers(
            db_session,
            "click",
            entered_users,
            now - timedelta(hours=1),
            now + timedelta(hours=1)
        )

        assert len(completers) == 5

    def test_get_step_completers_empty_users(self, funnel_engine, db_session):
        """Test getting completers with empty user set."""
        completers = funnel_engine._get_step_completers(
            db_session,
            "click",
            set(),
            get_utc_now(),
            get_utc_now() + timedelta(days=1)
        )

        assert len(completers) == 0

    def test_analyze_step(self, funnel_engine, db_session):
        """Test analyzing a single funnel step."""
        now = get_utc_now()

        step = FunnelStepORM(
            id=generate_uuid(),
            funnel_id=generate_uuid(),
            name="Test Step",
            event_type="click",
            order=0
        )

        # 10 users entered
        entered_users = {f"user_{i}" for i in range(10)}

        # 6 completed
        for i in range(6):
            db_session.add(EventORM(
                name="click",
                event_type="click",
                user_id=f"user_{i}",
                timestamp=now
            ))
        db_session.commit()

        stats = funnel_engine._analyze_step(
            db_session,
            step,
            entered_users,
            now - timedelta(hours=1),
            now + timedelta(hours=1)
        )

        assert isinstance(stats, FunnelStepStats)
        assert stats.entered == 10
        assert stats.completed == 6
        assert stats.dropped == 4
        assert stats.completion_rate == 60.0
        assert stats.drop_off_rate == 40.0

    def test_funnel_step_stats_zero_entered(self, funnel_engine, db_session):
        """Test step stats with zero users entered."""
        step = FunnelStepORM(
            id=generate_uuid(),
            funnel_id=generate_uuid(),
            name="Empty Step",
            event_type="click",
            order=0
        )

        stats = funnel_engine._analyze_step(
            db_session,
            step,
            set(),  # No users
            get_utc_now(),
            get_utc_now() + timedelta(days=1)
        )

        assert stats.entered == 0
        assert stats.completed == 0
        assert stats.completion_rate == 0.0

    def test_funnel_with_duplicate_events(self, funnel_engine, db_session):
        """Test funnel handles duplicate events correctly."""
        now = get_utc_now()

        funnel = FunnelORM(id=generate_uuid(), name="Test Funnel")
        funnel.steps = [
            FunnelStepORM(
                id=generate_uuid(),
                funnel_id=funnel.id,
                name="Step 1",
                event_type="page_view",
                order=0
            )
        ]
        db_session.add(funnel)
        db_session.commit()

        # Same user, multiple events
        for i in range(5):
            db_session.add(EventORM(
                name="page_view",
                event_type="page_view",
                user_id="user_1",  # Same user
                timestamp=now + timedelta(seconds=i)
            ))
        db_session.commit()

        analysis = funnel_engine.analyze_funnel(
            funnel.id,
            now - timedelta(hours=1),
            now + timedelta(hours=1)
        )

        # Should count unique users
        assert analysis.total_entered == 1

    def test_funnel_time_window(self, funnel_engine, db_session):
        """Test funnel respects time window."""
        base_time = get_utc_now()

        funnel = FunnelORM(id=generate_uuid(), name="Time Test")
        funnel.steps = [
            FunnelStepORM(
                id=generate_uuid(),
                funnel_id=funnel.id,
                name="Step 1",
                event_type="page_view",
                order=0
            )
        ]
        db_session.add(funnel)
        db_session.commit()

        # Events outside window
        db_session.add(EventORM(
            name="old", event_type="page_view",
            user_id="user_1",
            timestamp=base_time - timedelta(days=10)
        ))

        # Events inside window
        db_session.add(EventORM(
            name="new", event_type="page_view",
            user_id="user_2",
            timestamp=base_time
        ))
        db_session.commit()

        analysis = funnel_engine.analyze_funnel(
            funnel.id,
            base_time - timedelta(hours=1),
            base_time + timedelta(hours=1)
        )

        # Should only count user_2
        assert analysis.total_entered == 1

    @pytest.mark.parametrize("completion_rate", [0, 25, 50, 75, 100])
    def test_funnel_various_completion_rates(self, funnel_engine, db_session, completion_rate):
        """Test funnel with various completion rates."""
        now = get_utc_now()
        total_users = 100

        funnel = FunnelORM(id=generate_uuid(), name="Rate Test")
        funnel.steps = [
            FunnelStepORM(id=generate_uuid(), funnel_id=funnel.id,
                         name="Start", event_type="start", order=0),
            FunnelStepORM(id=generate_uuid(), funnel_id=funnel.id,
                         name="End", event_type="end", order=1)
        ]
        db_session.add(funnel)
        db_session.commit()

        # All users start
        for i in range(total_users):
            db_session.add(EventORM(
                name="start", event_type="start",
                user_id=f"user_{i}", timestamp=now
            ))

        # completion_rate% complete
        completers = int(total_users * completion_rate / 100)
        for i in range(completers):
            db_session.add(EventORM(
                name="end", event_type="end",
                user_id=f"user_{i}", timestamp=now + timedelta(seconds=10)
            ))
        db_session.commit()

        analysis = funnel_engine.analyze_funnel(
            funnel.id,
            now - timedelta(hours=1),
            now + timedelta(hours=1)
        )

        assert analysis.overall_conversion_rate == pytest.approx(completion_rate, abs=1)


# Test count: 20 tests
