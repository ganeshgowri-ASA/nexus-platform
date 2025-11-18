"""
Repositories

Repository pattern for database operations with full CRUD.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Session

from modules.analytics.storage.database import Base
from modules.analytics.storage.models import (
    ABTestAssignmentORM,
    ABTestORM,
    CohortORM,
    DashboardORM,
    EventORM,
    ExportJobORM,
    FunnelORM,
    FunnelStepORM,
    GoalConversionORM,
    GoalORM,
    MetricORM,
    SessionORM,
    UserORM,
)

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations."""

    def __init__(self, model: Type[T]):
        """
        Initialize repository.

        Args:
            model: SQLAlchemy ORM model class
        """
        self.model = model

    def create(self, session: Session, **kwargs) -> T:
        """
        Create a new record.

        Args:
            session: Database session
            **kwargs: Model fields

        Returns:
            Created model instance

        Raises:
            IntegrityError: If unique constraint violated
        """
        try:
            instance = self.model(**kwargs)
            session.add(instance)
            session.flush()
            logger.debug(f"Created {self.model.__name__}: {instance.id}")
            return instance
        except IntegrityError as e:
            logger.error(f"Integrity error creating {self.model.__name__}: {e}")
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error creating {self.model.__name__}: {e}")
            raise

    async def async_create(self, session: AsyncSession, **kwargs) -> T:
        """
        Asynchronously create a new record.

        Args:
            session: Async database session
            **kwargs: Model fields

        Returns:
            Created model instance
        """
        try:
            instance = self.model(**kwargs)
            session.add(instance)
            await session.flush()
            logger.debug(f"Created {self.model.__name__}: {instance.id}")
            return instance
        except IntegrityError as e:
            logger.error(f"Integrity error creating {self.model.__name__}: {e}")
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error creating {self.model.__name__}: {e}")
            raise

    def get_by_id(self, session: Session, id: str) -> Optional[T]:
        """
        Get record by ID.

        Args:
            session: Database session
            id: Record ID

        Returns:
            Model instance or None
        """
        try:
            instance = session.query(self.model).filter(self.model.id == id).first()
            if instance:
                logger.debug(f"Found {self.model.__name__}: {id}")
            else:
                logger.debug(f"{self.model.__name__} not found: {id}")
            return instance
        except SQLAlchemyError as e:
            logger.error(f"Database error getting {self.model.__name__}: {e}")
            raise

    async def async_get_by_id(self, session: AsyncSession, id: str) -> Optional[T]:
        """
        Asynchronously get record by ID.

        Args:
            session: Async database session
            id: Record ID

        Returns:
            Model instance or None
        """
        try:
            result = await session.execute(
                select(self.model).where(self.model.id == id)
            )
            instance = result.scalar_one_or_none()
            if instance:
                logger.debug(f"Found {self.model.__name__}: {id}")
            else:
                logger.debug(f"{self.model.__name__} not found: {id}")
            return instance
        except SQLAlchemyError as e:
            logger.error(f"Database error getting {self.model.__name__}: {e}")
            raise

    def get_all(
        self,
        session: Session,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
    ) -> List[T]:
        """
        Get all records with pagination.

        Args:
            session: Database session
            skip: Number of records to skip
            limit: Maximum number of records
            order_by: Field to order by

        Returns:
            List of model instances
        """
        try:
            query = session.query(self.model)

            if order_by:
                if order_by.startswith("-"):
                    field = getattr(self.model, order_by[1:])
                    query = query.order_by(desc(field))
                else:
                    field = getattr(self.model, order_by)
                    query = query.order_by(field)

            instances = query.offset(skip).limit(limit).all()
            logger.debug(f"Retrieved {len(instances)} {self.model.__name__} records")
            return instances
        except SQLAlchemyError as e:
            logger.error(f"Database error getting all {self.model.__name__}: {e}")
            raise

    async def async_get_all(
        self,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
    ) -> List[T]:
        """
        Asynchronously get all records with pagination.

        Args:
            session: Async database session
            skip: Number of records to skip
            limit: Maximum number of records
            order_by: Field to order by

        Returns:
            List of model instances
        """
        try:
            query = select(self.model)

            if order_by:
                if order_by.startswith("-"):
                    field = getattr(self.model, order_by[1:])
                    query = query.order_by(desc(field))
                else:
                    field = getattr(self.model, order_by)
                    query = query.order_by(field)

            query = query.offset(skip).limit(limit)
            result = await session.execute(query)
            instances = result.scalars().all()
            logger.debug(f"Retrieved {len(instances)} {self.model.__name__} records")
            return instances
        except SQLAlchemyError as e:
            logger.error(f"Database error getting all {self.model.__name__}: {e}")
            raise

    def update(self, session: Session, id: str, **kwargs) -> Optional[T]:
        """
        Update a record.

        Args:
            session: Database session
            id: Record ID
            **kwargs: Fields to update

        Returns:
            Updated model instance or None
        """
        try:
            instance = self.get_by_id(session, id)
            if not instance:
                return None

            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)

            if hasattr(instance, "updated_at"):
                instance.updated_at = datetime.utcnow()

            session.flush()
            logger.debug(f"Updated {self.model.__name__}: {id}")
            return instance
        except IntegrityError as e:
            logger.error(f"Integrity error updating {self.model.__name__}: {e}")
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error updating {self.model.__name__}: {e}")
            raise

    async def async_update(
        self, session: AsyncSession, id: str, **kwargs
    ) -> Optional[T]:
        """
        Asynchronously update a record.

        Args:
            session: Async database session
            id: Record ID
            **kwargs: Fields to update

        Returns:
            Updated model instance or None
        """
        try:
            instance = await self.async_get_by_id(session, id)
            if not instance:
                return None

            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)

            if hasattr(instance, "updated_at"):
                instance.updated_at = datetime.utcnow()

            await session.flush()
            logger.debug(f"Updated {self.model.__name__}: {id}")
            return instance
        except IntegrityError as e:
            logger.error(f"Integrity error updating {self.model.__name__}: {e}")
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error updating {self.model.__name__}: {e}")
            raise

    def delete(self, session: Session, id: str) -> bool:
        """
        Delete a record.

        Args:
            session: Database session
            id: Record ID

        Returns:
            True if deleted, False if not found
        """
        try:
            instance = self.get_by_id(session, id)
            if not instance:
                return False

            session.delete(instance)
            session.flush()
            logger.debug(f"Deleted {self.model.__name__}: {id}")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Database error deleting {self.model.__name__}: {e}")
            raise

    async def async_delete(self, session: AsyncSession, id: str) -> bool:
        """
        Asynchronously delete a record.

        Args:
            session: Async database session
            id: Record ID

        Returns:
            True if deleted, False if not found
        """
        try:
            instance = await self.async_get_by_id(session, id)
            if not instance:
                return False

            await session.delete(instance)
            await session.flush()
            logger.debug(f"Deleted {self.model.__name__}: {id}")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Database error deleting {self.model.__name__}: {e}")
            raise

    def count(self, session: Session, **filters) -> int:
        """
        Count records matching filters.

        Args:
            session: Database session
            **filters: Filter conditions

        Returns:
            Count of matching records
        """
        try:
            query = session.query(func.count(self.model.id))
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)
            count = query.scalar()
            logger.debug(f"Counted {count} {self.model.__name__} records")
            return count
        except SQLAlchemyError as e:
            logger.error(f"Database error counting {self.model.__name__}: {e}")
            raise

    async def async_count(self, session: AsyncSession, **filters) -> int:
        """
        Asynchronously count records matching filters.

        Args:
            session: Async database session
            **filters: Filter conditions

        Returns:
            Count of matching records
        """
        try:
            query = select(func.count(self.model.id))
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)
            result = await session.execute(query)
            count = result.scalar()
            logger.debug(f"Counted {count} {self.model.__name__} records")
            return count
        except SQLAlchemyError as e:
            logger.error(f"Database error counting {self.model.__name__}: {e}")
            raise

    def bulk_create(self, session: Session, items: List[Dict[str, Any]]) -> List[T]:
        """
        Bulk create records.

        Args:
            session: Database session
            items: List of record data

        Returns:
            List of created instances
        """
        try:
            instances = [self.model(**item) for item in items]
            session.bulk_save_objects(instances, return_defaults=True)
            session.flush()
            logger.debug(f"Bulk created {len(instances)} {self.model.__name__} records")
            return instances
        except SQLAlchemyError as e:
            logger.error(f"Database error bulk creating {self.model.__name__}: {e}")
            raise


class EventRepository(BaseRepository[EventORM]):
    """Repository for event operations."""

    def __init__(self):
        super().__init__(EventORM)

    def get_by_filters(
        self,
        session: Session,
        event_types: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        module: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[EventORM]:
        """Get events by filters."""
        query = session.query(EventORM)

        if event_types:
            query = query.filter(EventORM.event_type.in_(event_types))
        if user_id:
            query = query.filter(EventORM.user_id == user_id)
        if session_id:
            query = query.filter(EventORM.session_id == session_id)
        if module:
            query = query.filter(EventORM.module == module)
        if start_date:
            query = query.filter(EventORM.timestamp >= start_date)
        if end_date:
            query = query.filter(EventORM.timestamp <= end_date)

        return query.order_by(desc(EventORM.timestamp)).offset(skip).limit(limit).all()

    def get_unprocessed(self, session: Session, limit: int = 1000) -> List[EventORM]:
        """Get unprocessed events."""
        return (
            session.query(EventORM)
            .filter(EventORM.processed == False)
            .order_by(EventORM.timestamp)
            .limit(limit)
            .all()
        )

    def mark_processed(self, session: Session, event_ids: List[str]) -> int:
        """Mark events as processed."""
        count = (
            session.query(EventORM)
            .filter(EventORM.id.in_(event_ids))
            .update(
                {
                    EventORM.processed: True,
                    EventORM.processed_at: datetime.utcnow(),
                },
                synchronize_session=False,
            )
        )
        session.flush()
        logger.info(f"Marked {count} events as processed")
        return count


class MetricRepository(BaseRepository[MetricORM]):
    """Repository for metric operations."""

    def __init__(self):
        super().__init__(MetricORM)

    def get_by_filters(
        self,
        session: Session,
        names: Optional[List[str]] = None,
        metric_types: Optional[List[str]] = None,
        module: Optional[str] = None,
        period: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[MetricORM]:
        """Get metrics by filters."""
        query = session.query(MetricORM)

        if names:
            query = query.filter(MetricORM.name.in_(names))
        if metric_types:
            query = query.filter(MetricORM.metric_type.in_(metric_types))
        if module:
            query = query.filter(MetricORM.module == module)
        if period:
            query = query.filter(MetricORM.period == period)
        if start_date:
            query = query.filter(MetricORM.timestamp >= start_date)
        if end_date:
            query = query.filter(MetricORM.timestamp <= end_date)

        return query.order_by(desc(MetricORM.timestamp)).offset(skip).limit(limit).all()

    def get_time_series(
        self,
        session: Session,
        name: str,
        start_date: datetime,
        end_date: datetime,
        period: Optional[str] = None,
    ) -> List[MetricORM]:
        """Get metric time series data."""
        query = session.query(MetricORM).filter(
            and_(
                MetricORM.name == name,
                MetricORM.timestamp >= start_date,
                MetricORM.timestamp <= end_date,
            )
        )

        if period:
            query = query.filter(MetricORM.period == period)

        return query.order_by(MetricORM.timestamp).all()


class UserRepository(BaseRepository[UserORM]):
    """Repository for user operations."""

    def __init__(self):
        super().__init__(UserORM)

    def get_by_external_id(
        self, session: Session, external_id: str
    ) -> Optional[UserORM]:
        """Get user by external ID."""
        return (
            session.query(UserORM)
            .filter(UserORM.external_id == external_id)
            .first()
        )

    def get_by_email(self, session: Session, email: str) -> Optional[UserORM]:
        """Get user by email."""
        return session.query(UserORM).filter(UserORM.email == email).first()

    def increment_stats(
        self,
        session: Session,
        user_id: str,
        sessions: int = 0,
        events: int = 0,
        conversions: int = 0,
        value: float = 0.0,
    ) -> Optional[UserORM]:
        """Increment user statistics."""
        user = self.get_by_id(session, user_id)
        if not user:
            return None

        user.total_sessions += sessions
        user.total_events += events
        user.total_conversions += conversions
        user.lifetime_value += value
        user.last_seen_at = datetime.utcnow()
        user.updated_at = datetime.utcnow()

        session.flush()
        return user


class SessionRepository(BaseRepository[SessionORM]):
    """Repository for session operations."""

    def __init__(self):
        super().__init__(SessionORM)

    def get_by_user(
        self, session: Session, user_id: str, skip: int = 0, limit: int = 100
    ) -> List[SessionORM]:
        """Get sessions for a user."""
        return (
            session.query(SessionORM)
            .filter(SessionORM.user_id == user_id)
            .order_by(desc(SessionORM.started_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_active_sessions(
        self, session: Session, timeout_minutes: int = 30
    ) -> List[SessionORM]:
        """Get active sessions (not ended and recent activity)."""
        timeout = datetime.utcnow().timestamp() - (timeout_minutes * 60)
        cutoff = datetime.fromtimestamp(timeout)

        return (
            session.query(SessionORM)
            .filter(
                and_(
                    SessionORM.ended_at.is_(None),
                    SessionORM.last_activity_at >= cutoff,
                )
            )
            .all()
        )


class FunnelRepository(BaseRepository[FunnelORM]):
    """Repository for funnel operations."""

    def __init__(self):
        super().__init__(FunnelORM)

    def get_by_name(self, session: Session, name: str) -> Optional[FunnelORM]:
        """Get funnel by name."""
        return session.query(FunnelORM).filter(FunnelORM.name == name).first()

    def get_enabled(self, session: Session) -> List[FunnelORM]:
        """Get all enabled funnels."""
        return session.query(FunnelORM).filter(FunnelORM.enabled == True).all()


class CohortRepository(BaseRepository[CohortORM]):
    """Repository for cohort operations."""

    def __init__(self):
        super().__init__(CohortORM)

    def get_by_name(self, session: Session, name: str) -> Optional[CohortORM]:
        """Get cohort by name."""
        return session.query(CohortORM).filter(CohortORM.name == name).first()

    def get_by_type(self, session: Session, cohort_type: str) -> List[CohortORM]:
        """Get cohorts by type."""
        return session.query(CohortORM).filter(CohortORM.cohort_type == cohort_type).all()


class GoalRepository(BaseRepository[GoalORM]):
    """Repository for goal operations."""

    def __init__(self):
        super().__init__(GoalORM)

    def get_by_name(self, session: Session, name: str) -> Optional[GoalORM]:
        """Get goal by name."""
        return session.query(GoalORM).filter(GoalORM.name == name).first()

    def get_enabled(self, session: Session) -> List[GoalORM]:
        """Get all enabled goals."""
        return session.query(GoalORM).filter(GoalORM.enabled == True).all()

    def increment_conversions(
        self, session: Session, goal_id: str, value: float = 0.0
    ) -> Optional[GoalORM]:
        """Increment goal conversion statistics."""
        goal = self.get_by_id(session, goal_id)
        if not goal:
            return None

        goal.total_conversions += 1
        goal.total_value += value
        goal.updated_at = datetime.utcnow()

        session.flush()
        return goal


class GoalConversionRepository(BaseRepository[GoalConversionORM]):
    """Repository for goal conversion operations."""

    def __init__(self):
        super().__init__(GoalConversionORM)

    def get_by_goal(
        self,
        session: Session,
        goal_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[GoalConversionORM]:
        """Get conversions for a goal."""
        query = session.query(GoalConversionORM).filter(
            GoalConversionORM.goal_id == goal_id
        )

        if start_date:
            query = query.filter(GoalConversionORM.converted_at >= start_date)
        if end_date:
            query = query.filter(GoalConversionORM.converted_at <= end_date)

        return (
            query.order_by(desc(GoalConversionORM.converted_at))
            .offset(skip)
            .limit(limit)
            .all()
        )


class ABTestRepository(BaseRepository[ABTestORM]):
    """Repository for A/B test operations."""

    def __init__(self):
        super().__init__(ABTestORM)

    def get_by_name(self, session: Session, name: str) -> Optional[ABTestORM]:
        """Get A/B test by name."""
        return session.query(ABTestORM).filter(ABTestORM.name == name).first()

    def get_active(self, session: Session) -> List[ABTestORM]:
        """Get active A/B tests."""
        now = datetime.utcnow()
        return (
            session.query(ABTestORM)
            .filter(
                and_(
                    ABTestORM.status == "running",
                    ABTestORM.start_date <= now,
                    or_(ABTestORM.end_date.is_(None), ABTestORM.end_date >= now),
                )
            )
            .all()
        )


class ABTestAssignmentRepository(BaseRepository[ABTestAssignmentORM]):
    """Repository for A/B test assignment operations."""

    def __init__(self):
        super().__init__(ABTestAssignmentORM)

    def get_user_assignment(
        self, session: Session, test_id: str, user_id: str
    ) -> Optional[ABTestAssignmentORM]:
        """Get user's assignment for a test."""
        return (
            session.query(ABTestAssignmentORM)
            .filter(
                and_(
                    ABTestAssignmentORM.test_id == test_id,
                    ABTestAssignmentORM.user_id == user_id,
                )
            )
            .first()
        )


class DashboardRepository(BaseRepository[DashboardORM]):
    """Repository for dashboard operations."""

    def __init__(self):
        super().__init__(DashboardORM)

    def get_by_owner(
        self, session: Session, owner_id: str, skip: int = 0, limit: int = 100
    ) -> List[DashboardORM]:
        """Get dashboards by owner."""
        return (
            session.query(DashboardORM)
            .filter(DashboardORM.owner_id == owner_id)
            .order_by(desc(DashboardORM.updated_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_public(self, session: Session, skip: int = 0, limit: int = 100) -> List[DashboardORM]:
        """Get public dashboards."""
        return (
            session.query(DashboardORM)
            .filter(DashboardORM.is_public == True)
            .order_by(desc(DashboardORM.updated_at))
            .offset(skip)
            .limit(limit)
            .all()
        )


class ExportJobRepository(BaseRepository[ExportJobORM]):
    """Repository for export job operations."""

    def __init__(self):
        super().__init__(ExportJobORM)

    def get_by_user(
        self, session: Session, user_id: str, skip: int = 0, limit: int = 100
    ) -> List[ExportJobORM]:
        """Get export jobs for a user."""
        return (
            session.query(ExportJobORM)
            .filter(ExportJobORM.user_id == user_id)
            .order_by(desc(ExportJobORM.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_expired(self, session: Session) -> List[ExportJobORM]:
        """Get expired export jobs."""
        now = datetime.utcnow()
        return (
            session.query(ExportJobORM)
            .filter(
                and_(
                    ExportJobORM.expires_at.isnot(None),
                    ExportJobORM.expires_at <= now,
                    ExportJobORM.status == "completed",
                )
            )
            .all()
        )
