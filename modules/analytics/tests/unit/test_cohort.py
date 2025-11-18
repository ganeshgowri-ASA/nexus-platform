"""
Unit Tests for Cohort Analysis Engine

Tests for cohort analysis and retention tracking.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from modules.analytics.processing.cohort import CohortEngine
from modules.analytics.models.cohort import CohortAnalysis, CohortRetention
from modules.analytics.storage.models import UserORM, SessionORM
from shared.constants import AggregationPeriod
from shared.utils import get_utc_now, generate_uuid


class TestCohortEngine:
    """Test suite for CohortEngine class."""

    def test_cohort_engine_initialization(self, cohort_engine):
        """Test cohort engine initializes correctly."""
        assert cohort_engine.db is not None
        assert cohort_engine.repository is not None

    def test_analyze_retention_cohort_basic(self, cohort_engine, db_session):
        """Test basic retention cohort analysis."""
        cohort_date = get_utc_now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Create cohort users
        for i in range(100):
            user = UserORM(
                id=f"user_{i}",
                first_seen_at=cohort_date + timedelta(hours=i % 24),
                last_seen_at=cohort_date
            )
            db_session.add(user)
        db_session.commit()

        # Analyze cohort
        analysis = cohort_engine.analyze_retention_cohort(
            cohort_date,
            periods=4,
            period_type=AggregationPeriod.WEEK
        )

        assert analysis is not None
        assert analysis.initial_users == 100
        assert len(analysis.retention_data) == 4

    def test_analyze_retention_cohort_empty(self, cohort_engine, db_session):
        """Test retention analysis with empty cohort."""
        future_date = get_utc_now() + timedelta(days=365)

        analysis = cohort_engine.analyze_retention_cohort(
            future_date,
            periods=4
        )

        assert analysis is None

    def test_analyze_retention_cohort_with_sessions(self, cohort_engine, db_session):
        """Test retention with user sessions."""
        cohort_date = get_utc_now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Create cohort users
        for i in range(50):
            user = UserORM(
                id=f"user_{i}",
                first_seen_at=cohort_date,
                last_seen_at=cohort_date
            )
            db_session.add(user)

            # Initial session
            db_session.add(SessionORM(
                session_id=f"initial_{i}",
                user_id=f"user_{i}",
                started_at=cohort_date
            ))

        # Create return sessions for some users
        # Week 1: 40 users return (80%)
        for i in range(40):
            db_session.add(SessionORM(
                session_id=f"week1_{i}",
                user_id=f"user_{i}",
                started_at=cohort_date + timedelta(weeks=1)
            ))

        # Week 2: 30 users return (60%)
        for i in range(30):
            db_session.add(SessionORM(
                session_id=f"week2_{i}",
                user_id=f"user_{i}",
                started_at=cohort_date + timedelta(weeks=2)
            ))

        db_session.commit()

        analysis = cohort_engine.analyze_retention_cohort(
            cohort_date,
            periods=3,
            period_type=AggregationPeriod.WEEK
        )

        assert analysis.initial_users == 50
        assert analysis.retention_data[1].users_active == 40
        assert analysis.retention_data[2].users_active == 30

    def test_get_cohort_users(self, cohort_engine, db_session):
        """Test getting users in a cohort."""
        cohort_date = get_utc_now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Users in cohort
        for i in range(10):
            db_session.add(UserORM(
                id=f"cohort_user_{i}",
                first_seen_at=cohort_date + timedelta(hours=i)
            ))

        # Users outside cohort
        db_session.add(UserORM(
            id="old_user",
            first_seen_at=cohort_date - timedelta(days=2)
        ))
        db_session.add(UserORM(
            id="future_user",
            first_seen_at=cohort_date + timedelta(days=8)
        ))

        db_session.commit()

        users = cohort_engine._get_cohort_users(
            db_session,
            cohort_date,
            AggregationPeriod.WEEK
        )

        assert len(users) == 10

    def test_get_active_users(self, cohort_engine, db_session):
        """Test getting active users in a period."""
        cohort_date = get_utc_now()
        cohort_users = {f"user_{i}" for i in range(10)}

        # Create sessions for some users
        for i in range(6):
            db_session.add(SessionORM(
                session_id=f"session_{i}",
                user_id=f"user_{i}",
                started_at=cohort_date
            ))
        db_session.commit()

        active = cohort_engine._get_active_users(
            db_session,
            cohort_users,
            cohort_date - timedelta(hours=1),
            cohort_date + timedelta(hours=1)
        )

        assert active == 6

    def test_get_active_users_empty_cohort(self, cohort_engine, db_session):
        """Test active users with empty cohort."""
        active = cohort_engine._get_active_users(
            db_session,
            set(),
            get_utc_now(),
            get_utc_now() + timedelta(days=1)
        )

        assert active == 0

    def test_get_period_range_day(self, cohort_engine):
        """Test period range calculation for day."""
        base_date = datetime(2024, 1, 1, 0, 0, 0)

        start, end = cohort_engine._get_period_range(
            base_date,
            0,
            AggregationPeriod.DAY
        )

        assert start == base_date
        assert end == base_date + timedelta(days=1)

    def test_get_period_range_week(self, cohort_engine):
        """Test period range calculation for week."""
        base_date = datetime(2024, 1, 1, 0, 0, 0)

        start, end = cohort_engine._get_period_range(
            base_date,
            2,
            AggregationPeriod.WEEK
        )

        assert start == base_date + timedelta(weeks=2)
        assert end == base_date + timedelta(weeks=3)

    def test_get_period_range_month(self, cohort_engine):
        """Test period range calculation for month."""
        base_date = datetime(2024, 1, 1, 0, 0, 0)

        start, end = cohort_engine._get_period_range(
            base_date,
            1,
            AggregationPeriod.MONTH
        )

        assert start == base_date + timedelta(days=30)
        assert end == base_date + timedelta(days=60)

    @pytest.mark.parametrize("period_type", [
        AggregationPeriod.DAY,
        AggregationPeriod.WEEK,
        AggregationPeriod.MONTH
    ])
    def test_analyze_different_period_types(self, cohort_engine, db_session, period_type):
        """Test analysis with different period types."""
        cohort_date = get_utc_now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Create cohort
        for i in range(20):
            db_session.add(UserORM(
                id=f"user_{i}",
                first_seen_at=cohort_date
            ))
        db_session.commit()

        analysis = cohort_engine.analyze_retention_cohort(
            cohort_date,
            periods=3,
            period_type=period_type
        )

        assert analysis is not None
        assert analysis.initial_users == 20

    def test_retention_rate_calculation(self, cohort_engine, db_session):
        """Test retention rate calculation accuracy."""
        cohort_date = get_utc_now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Create 100 users
        for i in range(100):
            db_session.add(UserORM(
                id=f"user_{i}",
                first_seen_at=cohort_date
            ))

        # 50% return in week 1
        for i in range(50):
            db_session.add(SessionORM(
                session_id=f"week1_{i}",
                user_id=f"user_{i}",
                started_at=cohort_date + timedelta(weeks=1)
            ))

        db_session.commit()

        analysis = cohort_engine.analyze_retention_cohort(
            cohort_date,
            periods=2,
            period_type=AggregationPeriod.WEEK
        )

        assert analysis.retention_data[1].retention_rate == 50.0

    def test_churn_rate_calculation(self, cohort_engine, db_session):
        """Test churn rate calculation."""
        cohort_date = get_utc_now().replace(hour=0, minute=0, second=0, microsecond=0)

        for i in range(50):
            db_session.add(UserORM(
                id=f"user_{i}",
                first_seen_at=cohort_date
            ))
        db_session.commit()

        analysis = cohort_engine.analyze_retention_cohort(
            cohort_date,
            periods=4
        )

        # Churn rate should be 100 - avg_retention
        expected_churn = 100 - analysis.avg_retention_rate
        assert analysis.churn_rate == pytest.approx(expected_churn, abs=0.1)

    def test_cohort_with_multiple_sessions_per_user(self, cohort_engine, db_session):
        """Test that multiple sessions from same user count as one active user."""
        cohort_date = get_utc_now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Create cohort
        for i in range(10):
            db_session.add(UserORM(
                id=f"user_{i}",
                first_seen_at=cohort_date
            ))

        # User 0 has multiple sessions in week 1
        for i in range(5):
            db_session.add(SessionORM(
                session_id=f"session_{i}",
                user_id="user_0",
                started_at=cohort_date + timedelta(weeks=1, hours=i)
            ))

        db_session.commit()

        analysis = cohort_engine.analyze_retention_cohort(
            cohort_date,
            periods=2,
            period_type=AggregationPeriod.WEEK
        )

        # Should count user_0 only once
        assert analysis.retention_data[1].users_active == 1

    def test_cumulative_retention(self, cohort_engine, db_session):
        """Test cumulative retention calculation."""
        cohort_date = get_utc_now().replace(hour=0, minute=0, second=0, microsecond=0)

        for i in range(100):
            db_session.add(UserORM(
                id=f"user_{i}",
                first_seen_at=cohort_date
            ))
        db_session.commit()

        analysis = cohort_engine.analyze_retention_cohort(
            cohort_date,
            periods=3
        )

        # Period 0 should have 100% cumulative retention
        assert analysis.retention_data[0].cumulative_retention == 100.0

    def test_analyze_retention_error_handling(self, cohort_engine, db_session):
        """Test error handling in retention analysis."""
        with patch.object(cohort_engine, '_get_cohort_users', side_effect=Exception("DB Error")):
            analysis = cohort_engine.analyze_retention_cohort(
                get_utc_now(),
                periods=4
            )
            assert analysis is None

    @pytest.mark.parametrize("user_count", [10, 50, 100, 500])
    def test_different_cohort_sizes(self, cohort_engine, db_session, user_count):
        """Test cohorts of different sizes."""
        cohort_date = get_utc_now().replace(hour=0, minute=0, second=0, microsecond=0)

        for i in range(user_count):
            db_session.add(UserORM(
                id=f"user_{i}",
                first_seen_at=cohort_date
            ))
        db_session.commit()

        analysis = cohort_engine.analyze_retention_cohort(
            cohort_date,
            periods=3
        )

        assert analysis.initial_users == user_count


# Test count: 19 tests
