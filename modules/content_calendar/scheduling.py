"""
Content scheduling module for auto-scheduling and optimal timing.

This module provides:
- Auto-scheduling based on optimal times
- Recurring content management
- Campaign scheduling
- Schedule optimization
- Timezone handling
"""
from datetime import datetime, timedelta, time
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from loguru import logger
import pytz
from collections import defaultdict

from database import ContentItem, Analytics, Channel as DBChannel, ContentStatus
from .calendar_types import (
    CalendarEvent,
    ScheduleConfig,
    RecurringPattern,
    RecurrenceType,
    DayOfWeek,
    OptimalTime,
)


class ContentScheduler:
    """Content scheduler for automated and optimal scheduling."""

    def __init__(self, db: Session):
        """
        Initialize content scheduler.

        Args:
            db: Database session
        """
        self.db = db
        logger.info("ContentScheduler initialized")

    def schedule_content(
        self,
        content_id: int,
        schedule_config: ScheduleConfig,
    ) -> CalendarEvent:
        """
        Schedule content for publication.

        Args:
            content_id: Content ID to schedule
            schedule_config: Schedule configuration

        Returns:
            Updated calendar event
        """
        try:
            content_item = (
                self.db.query(ContentItem)
                .filter(ContentItem.id == content_id)
                .first()
            )

            if not content_item:
                raise ValueError(f"Content {content_id} not found")

            # Convert to target timezone
            scheduled_time = self._convert_timezone(
                schedule_config.scheduled_time,
                schedule_config.timezone,
            )

            content_item.scheduled_at = scheduled_time
            content_item.timezone = schedule_config.timezone
            content_item.status = ContentStatus.SCHEDULED

            # Store schedule config in metadata
            metadata = content_item.metadata or {}
            metadata["schedule_config"] = schedule_config.model_dump()
            content_item.metadata = metadata

            content_item.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(content_item)

            logger.info(
                f"Scheduled content {content_id} for {scheduled_time} {schedule_config.timezone}"
            )
            return self._content_item_to_event(content_item)

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error scheduling content {content_id}: {e}")
            raise

    def auto_schedule(
        self,
        content_id: int,
        channel: str,
        timezone: str = "UTC",
        days_ahead: int = 7,
    ) -> CalendarEvent:
        """
        Auto-schedule content at optimal time.

        Args:
            content_id: Content ID to schedule
            channel: Publishing channel
            timezone: Timezone for scheduling
            days_ahead: Look ahead this many days for optimal slot

        Returns:
            Updated calendar event
        """
        try:
            # Get optimal time for channel
            optimal_times = self.get_optimal_posting_times(
                channel=channel,
                days_ahead=days_ahead,
            )

            if not optimal_times:
                logger.warning(f"No optimal times found for {channel}, using defaults")
                # Default to next day at 9 AM
                scheduled_time = datetime.now(pytz.timezone(timezone)).replace(
                    hour=9, minute=0, second=0, microsecond=0
                ) + timedelta(days=1)
            else:
                # Use the best optimal time
                best_time = optimal_times[0]
                scheduled_time = self._get_next_occurrence(
                    best_time.day_of_week,
                    best_time.time,
                    timezone,
                )

            # Schedule the content
            schedule_config = ScheduleConfig(
                scheduled_time=scheduled_time,
                timezone=timezone,
                auto_schedule=True,
            )

            return self.schedule_content(content_id, schedule_config)

        except Exception as e:
            logger.error(f"Error auto-scheduling content {content_id}: {e}")
            raise

    def create_recurring_content(
        self,
        content_id: int,
        recurring_pattern: RecurringPattern,
        timezone: str = "UTC",
    ) -> list[CalendarEvent]:
        """
        Create recurring content instances.

        Args:
            content_id: Content ID to recur
            recurring_pattern: Recurrence pattern
            timezone: Timezone for scheduling

        Returns:
            List of created recurring events
        """
        try:
            original = (
                self.db.query(ContentItem)
                .filter(ContentItem.id == content_id)
                .first()
            )

            if not original:
                raise ValueError(f"Content {content_id} not found")

            # Generate occurrence dates
            occurrence_dates = self._generate_occurrence_dates(
                recurring_pattern,
                timezone,
            )

            # Create content instances
            created_events = []
            for date in occurrence_dates:
                # Duplicate content
                duplicate = ContentItem(
                    title=original.title,
                    content=original.content,
                    content_type=original.content_type,
                    status=ContentStatus.SCHEDULED,
                    creator_id=original.creator_id,
                    campaign_id=original.campaign_id,
                    scheduled_at=date,
                    timezone=timezone,
                    channels=original.channels,
                    media_urls=original.media_urls,
                    tags=original.tags,
                    metadata={
                        **(original.metadata or {}),
                        "is_recurring": True,
                        "parent_content_id": original.id,
                        "recurring_pattern": recurring_pattern.model_dump(),
                    },
                )

                self.db.add(duplicate)
                self.db.commit()
                self.db.refresh(duplicate)

                created_events.append(self._content_item_to_event(duplicate))

            logger.info(
                f"Created {len(created_events)} recurring instances for content {content_id}"
            )
            return created_events

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating recurring content for {content_id}: {e}")
            raise

    def get_optimal_posting_times(
        self,
        channel: str,
        days_ahead: int = 7,
        top_n: int = 5,
    ) -> list[OptimalTime]:
        """
        Get optimal posting times for a channel based on historical data.

        Args:
            channel: Publishing channel
            days_ahead: Number of days to consider
            top_n: Number of top times to return

        Returns:
            List of optimal posting times
        """
        try:
            # Get historical analytics data
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)

            # Query analytics for the channel
            analytics = (
                self.db.query(Analytics)
                .filter(
                    and_(
                        Analytics.channel == self._map_channel(channel),
                        Analytics.recorded_at >= start_date,
                        Analytics.recorded_at <= end_date,
                        Analytics.metric_name == "engagement_rate",
                    )
                )
                .all()
            )

            if not analytics:
                return self._get_default_optimal_times(channel)

            # Analyze by day of week and hour
            engagement_by_time: dict[tuple[str, int], list[float]] = defaultdict(list)

            for metric in analytics:
                day_of_week = metric.recorded_at.strftime("%A").lower()
                hour = metric.recorded_at.hour
                engagement_by_time[(day_of_week, hour)].append(metric.metric_value)

            # Calculate average engagement for each time slot
            optimal_times = []
            for (day, hour), engagements in engagement_by_time.items():
                avg_engagement = sum(engagements) / len(engagements)
                confidence = min(len(engagements) / 10.0, 1.0)  # More data = higher confidence

                optimal_time = OptimalTime(
                    channel=channel,
                    day_of_week=DayOfWeek(day),
                    time=time(hour=hour, minute=0),
                    expected_engagement=avg_engagement,
                    confidence=confidence,
                )
                optimal_times.append(optimal_time)

            # Sort by engagement rate and return top N
            optimal_times.sort(key=lambda x: x.expected_engagement, reverse=True)

            logger.info(f"Found {len(optimal_times)} optimal times for {channel}")
            return optimal_times[:top_n]

        except Exception as e:
            logger.error(f"Error getting optimal posting times: {e}")
            return self._get_default_optimal_times(channel)

    def get_schedule_conflicts(
        self,
        scheduled_time: datetime,
        channel: str,
        buffer_minutes: int = 30,
    ) -> list[CalendarEvent]:
        """
        Check for scheduling conflicts.

        Args:
            scheduled_time: Proposed schedule time
            channel: Publishing channel
            buffer_minutes: Buffer time around scheduled slot

        Returns:
            List of conflicting events
        """
        try:
            start_buffer = scheduled_time - timedelta(minutes=buffer_minutes)
            end_buffer = scheduled_time + timedelta(minutes=buffer_minutes)

            conflicts = (
                self.db.query(ContentItem)
                .filter(
                    and_(
                        ContentItem.scheduled_at >= start_buffer,
                        ContentItem.scheduled_at <= end_buffer,
                        ContentItem.channels.contains([channel]),
                        ContentItem.status == ContentStatus.SCHEDULED,
                    )
                )
                .all()
            )

            conflict_events = [
                self._content_item_to_event(item) for item in conflicts
            ]

            logger.info(f"Found {len(conflict_events)} scheduling conflicts")
            return conflict_events

        except Exception as e:
            logger.error(f"Error checking schedule conflicts: {e}")
            raise

    def reschedule_content(
        self,
        content_id: int,
        new_datetime: datetime,
        timezone: Optional[str] = None,
    ) -> CalendarEvent:
        """
        Reschedule content to a new time.

        Args:
            content_id: Content ID to reschedule
            new_datetime: New scheduled datetime
            timezone: New timezone (optional)

        Returns:
            Updated calendar event
        """
        try:
            content_item = (
                self.db.query(ContentItem)
                .filter(ContentItem.id == content_id)
                .first()
            )

            if not content_item:
                raise ValueError(f"Content {content_id} not found")

            content_item.scheduled_at = new_datetime
            if timezone:
                content_item.timezone = timezone

            content_item.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(content_item)

            logger.info(f"Rescheduled content {content_id} to {new_datetime}")
            return self._content_item_to_event(content_item)

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error rescheduling content {content_id}: {e}")
            raise

    def cancel_scheduled_content(self, content_id: int) -> bool:
        """
        Cancel scheduled content.

        Args:
            content_id: Content ID to cancel

        Returns:
            True if cancelled successfully
        """
        try:
            content_item = (
                self.db.query(ContentItem)
                .filter(ContentItem.id == content_id)
                .first()
            )

            if not content_item:
                raise ValueError(f"Content {content_id} not found")

            content_item.status = ContentStatus.DRAFT
            content_item.scheduled_at = None
            content_item.updated_at = datetime.utcnow()

            self.db.commit()

            logger.info(f"Cancelled scheduled content: {content_id}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error cancelling content {content_id}: {e}")
            raise

    # Helper Methods
    def _generate_occurrence_dates(
        self,
        pattern: RecurringPattern,
        timezone: str,
    ) -> list[datetime]:
        """Generate occurrence dates based on recurrence pattern."""
        dates = []
        tz = pytz.timezone(timezone)
        current_date = datetime.now(tz)

        if pattern.type == RecurrenceType.DAILY:
            for i in range(pattern.occurrences or 30):
                next_date = current_date + timedelta(days=i * pattern.interval)
                dates.append(next_date)
                if pattern.end_date and next_date >= pattern.end_date:
                    break

        elif pattern.type == RecurrenceType.WEEKLY:
            if pattern.days_of_week:
                week_offset = 0
                count = 0
                while count < (pattern.occurrences or 52):
                    for day in pattern.days_of_week:
                        next_date = self._get_next_occurrence(
                            day,
                            current_date.time(),
                            timezone,
                            week_offset,
                        )
                        if pattern.end_date and next_date >= pattern.end_date:
                            return dates
                        dates.append(next_date)
                        count += 1
                        if count >= (pattern.occurrences or 52):
                            break
                    week_offset += pattern.interval

        elif pattern.type == RecurrenceType.MONTHLY:
            for i in range(pattern.occurrences or 12):
                next_date = current_date + timedelta(days=30 * i * pattern.interval)
                if pattern.day_of_month:
                    next_date = next_date.replace(day=pattern.day_of_month)
                dates.append(next_date)
                if pattern.end_date and next_date >= pattern.end_date:
                    break

        return dates

    def _get_next_occurrence(
        self,
        day_of_week: DayOfWeek,
        target_time: time,
        timezone: str,
        weeks_ahead: int = 0,
    ) -> datetime:
        """Get next occurrence of a day/time."""
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)

        # Map day names to weekday numbers (0=Monday)
        day_map = {
            DayOfWeek.MONDAY: 0,
            DayOfWeek.TUESDAY: 1,
            DayOfWeek.WEDNESDAY: 2,
            DayOfWeek.THURSDAY: 3,
            DayOfWeek.FRIDAY: 4,
            DayOfWeek.SATURDAY: 5,
            DayOfWeek.SUNDAY: 6,
        }

        target_weekday = day_map[day_of_week]
        current_weekday = now.weekday()

        # Calculate days until target weekday
        days_ahead = (target_weekday - current_weekday) % 7
        if days_ahead == 0 and now.time() >= target_time:
            days_ahead = 7  # Next week if time has passed today

        # Add weeks offset
        days_ahead += weeks_ahead * 7

        next_date = now + timedelta(days=days_ahead)
        next_datetime = next_date.replace(
            hour=target_time.hour,
            minute=target_time.minute,
            second=0,
            microsecond=0,
        )

        return next_datetime

    def _convert_timezone(
        self,
        dt: datetime,
        target_timezone: str,
    ) -> datetime:
        """Convert datetime to target timezone."""
        if dt.tzinfo is None:
            dt = pytz.UTC.localize(dt)

        target_tz = pytz.timezone(target_timezone)
        return dt.astimezone(target_tz)

    def _get_default_optimal_times(self, channel: str) -> list[OptimalTime]:
        """Get default optimal times when no data available."""
        # Default times based on general social media best practices
        defaults = {
            "twitter": [(DayOfWeek.WEDNESDAY, 9), (DayOfWeek.FRIDAY, 12)],
            "facebook": [(DayOfWeek.THURSDAY, 13), (DayOfWeek.FRIDAY, 9)],
            "instagram": [(DayOfWeek.WEDNESDAY, 11), (DayOfWeek.FRIDAY, 14)],
            "linkedin": [(DayOfWeek.TUESDAY, 10), (DayOfWeek.THURSDAY, 9)],
        }

        channel_defaults = defaults.get(channel.lower(), [(DayOfWeek.WEDNESDAY, 10)])

        return [
            OptimalTime(
                channel=channel,
                day_of_week=day,
                time=time(hour=hour, minute=0),
                expected_engagement=0.05,
                confidence=0.3,
            )
            for day, hour in channel_defaults
        ]

    def _map_channel(self, channel: str) -> DBChannel:
        """Map channel name to database enum."""
        mapping = {
            "twitter": DBChannel.TWITTER,
            "facebook": DBChannel.FACEBOOK,
            "instagram": DBChannel.INSTAGRAM,
            "linkedin": DBChannel.LINKEDIN,
            "blog": DBChannel.BLOG,
            "email": DBChannel.EMAIL,
        }
        return mapping.get(channel.lower(), DBChannel.BLOG)

    def _content_item_to_event(self, item: ContentItem) -> CalendarEvent:
        """Convert ContentItem to CalendarEvent."""
        from .calendar_types import (
            ContentFormat,
            PublishingChannel,
            MediaAsset,
            ContentMetadata,
            Priority,
            ApprovalStatus,
        )

        schedule = ScheduleConfig(
            scheduled_time=item.scheduled_at or datetime.utcnow(),
            timezone=item.timezone or "UTC",
        )

        channels = [
            PublishingChannel(name=ch, platform=ch, is_active=True)
            for ch in (item.channels or [])
        ]

        media = [
            MediaAsset(url=url, type="image", filename=url.split("/")[-1], size=0)
            for url in (item.media_urls or [])
        ]

        metadata = ContentMetadata(tags=item.tags or [])

        return CalendarEvent(
            id=item.id,
            title=item.title,
            content=item.content,
            content_type=ContentFormat.TEXT,
            status=ApprovalStatus.SCHEDULED,
            priority=Priority.MEDIUM,
            schedule=schedule,
            channels=channels,
            media=media,
            metadata=metadata,
            creator_id=item.creator_id,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
