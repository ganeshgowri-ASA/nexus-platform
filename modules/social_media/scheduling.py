"""
Social Media Module - Post Scheduling and Queue Management.

This module provides scheduling functionality with optimal time suggestions,
queue management, and recurring post support.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

import pytz
from dateutil.rrule import rrule, rrulestr

from .social_types import (
    Campaign,
    PlatformType,
    Post,
    PostStatus,
    Schedule,
)

logger = logging.getLogger(__name__)


class SchedulingError(Exception):
    """Base exception for scheduling errors."""

    pass


class TimeSlotConflict(SchedulingError):
    """Time slot is already occupied."""

    pass


class PostScheduler:
    """Post scheduling manager with optimal time suggestions."""

    # Optimal posting times by platform (hour of day, 0-23)
    OPTIMAL_TIMES = {
        PlatformType.FACEBOOK: [9, 13, 15],  # 9am, 1pm, 3pm
        PlatformType.TWITTER: [8, 12, 17],  # 8am, 12pm, 5pm
        PlatformType.INSTAGRAM: [11, 14, 19],  # 11am, 2pm, 7pm
        PlatformType.LINKEDIN: [7, 12, 17],  # 7am, 12pm, 5pm
        PlatformType.TIKTOK: [9, 12, 19],  # 9am, 12pm, 7pm
        PlatformType.YOUTUBE: [14, 17, 20],  # 2pm, 5pm, 8pm
        PlatformType.PINTEREST: [20, 21, 14],  # 8pm, 9pm, 2pm
    }

    # Best days of week (0=Monday, 6=Sunday)
    OPTIMAL_DAYS = {
        PlatformType.FACEBOOK: [2, 3, 4],  # Wed, Thu, Fri
        PlatformType.TWITTER: [2, 3, 4],  # Wed, Thu, Fri
        PlatformType.INSTAGRAM: [1, 2, 3],  # Tue, Wed, Thu
        PlatformType.LINKEDIN: [1, 2, 3],  # Tue, Wed, Thu
        PlatformType.TIKTOK: [1, 3, 4],  # Tue, Thu, Fri
        PlatformType.YOUTUBE: [3, 4, 5],  # Thu, Fri, Sat
        PlatformType.PINTEREST: [4, 5, 6],  # Fri, Sat, Sun
    }

    def __init__(self, timezone: str = "UTC"):
        """
        Initialize post scheduler.

        Args:
            timezone: Default timezone for scheduling
        """
        self.timezone = pytz.timezone(timezone)
        self._scheduled_posts: Dict[UUID, Post] = {}
        self._queue: List[Tuple[datetime, UUID]] = []  # (scheduled_time, post_id)
        self._schedules: Dict[UUID, Schedule] = {}

    def schedule_post(
        self,
        post: Post,
        scheduled_time: datetime,
        timezone: Optional[str] = None,
    ) -> Post:
        """
        Schedule a post for publishing.

        Args:
            post: Post to schedule
            scheduled_time: When to publish the post
            timezone: Optional timezone (defaults to scheduler timezone)

        Returns:
            Updated Post object

        Raises:
            SchedulingError: If scheduling fails
        """
        try:
            # Convert to UTC if timezone provided
            if timezone:
                tz = pytz.timezone(timezone)
                if scheduled_time.tzinfo is None:
                    scheduled_time = tz.localize(scheduled_time)
                scheduled_time = scheduled_time.astimezone(pytz.UTC)
            elif scheduled_time.tzinfo is None:
                scheduled_time = self.timezone.localize(scheduled_time)
                scheduled_time = scheduled_time.astimezone(pytz.UTC)

            # Validate time is in future
            if scheduled_time <= datetime.now(pytz.UTC):
                raise SchedulingError("Scheduled time must be in the future")

            # Update post
            post.scheduled_time = scheduled_time
            post.status = PostStatus.SCHEDULED
            post.updated_at = datetime.utcnow()

            # Add to queue
            self._scheduled_posts[post.id] = post
            self._queue.append((scheduled_time, post.id))
            self._queue.sort(key=lambda x: x[0])

            logger.info(f"Scheduled post {post.id} for {scheduled_time}")
            return post

        except Exception as e:
            logger.error(f"Failed to schedule post: {e}")
            raise SchedulingError(f"Scheduling failed: {e}")

    def unschedule_post(self, post_id: UUID) -> bool:
        """
        Remove post from schedule.

        Args:
            post_id: Post UUID to unschedule

        Returns:
            True if unscheduled, False if not found
        """
        if post_id in self._scheduled_posts:
            post = self._scheduled_posts[post_id]
            post.status = PostStatus.DRAFT
            post.scheduled_time = None

            # Remove from queue
            self._queue = [(t, pid) for t, pid in self._queue if pid != post_id]

            del self._scheduled_posts[post_id]
            logger.info(f"Unscheduled post {post_id}")
            return True
        return False

    def reschedule_post(
        self,
        post_id: UUID,
        new_time: datetime,
        timezone: Optional[str] = None,
    ) -> Post:
        """
        Reschedule an existing post.

        Args:
            post_id: Post UUID to reschedule
            new_time: New scheduled time
            timezone: Optional timezone

        Returns:
            Updated Post object

        Raises:
            ValueError: If post not found
            SchedulingError: If rescheduling fails
        """
        if post_id not in self._scheduled_posts:
            raise ValueError(f"Post {post_id} not scheduled")

        post = self._scheduled_posts[post_id]
        self.unschedule_post(post_id)
        return self.schedule_post(post, new_time, timezone)

    def get_optimal_times(
        self,
        platform: PlatformType,
        start_date: datetime,
        days: int = 7,
        timezone: Optional[str] = None,
    ) -> List[datetime]:
        """
        Get optimal posting times for a platform.

        Args:
            platform: Target platform
            start_date: Start date for suggestions
            days: Number of days to suggest times for
            timezone: Timezone for suggestions

        Returns:
            List of optimal datetime suggestions
        """
        tz = pytz.timezone(timezone) if timezone else self.timezone
        optimal_hours = self.OPTIMAL_TIMES.get(platform, [9, 12, 15])
        optimal_days = self.OPTIMAL_DAYS.get(platform, [1, 2, 3, 4])

        suggestions = []
        current_date = start_date.date() if hasattr(start_date, 'date') else start_date

        for day_offset in range(days):
            check_date = current_date + timedelta(days=day_offset)

            # Skip if not an optimal day
            if check_date.weekday() not in optimal_days:
                continue

            # Add suggestions for each optimal hour
            for hour in optimal_hours:
                suggested_time = datetime.combine(
                    check_date, datetime.min.time()
                ).replace(hour=hour, minute=0, second=0)
                suggested_time = tz.localize(suggested_time)

                # Only suggest future times
                if suggested_time > datetime.now(tz):
                    suggestions.append(suggested_time)

        logger.info(
            f"Generated {len(suggestions)} optimal time suggestions for {platform.value}"
        )
        return suggestions[:20]  # Limit to 20 suggestions

    def create_recurring_post(
        self,
        post: Post,
        recurrence_rule: str,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        count: Optional[int] = None,
    ) -> List[Post]:
        """
        Create recurring post instances.

        Args:
            post: Base post to recur
            recurrence_rule: RRULE string (RFC 5545)
            start_date: Start date for recurrence
            end_date: Optional end date
            count: Optional max occurrences

        Returns:
            List of scheduled Post instances

        Example:
            # Weekly on Tuesdays at 2pm for 4 weeks
            "FREQ=WEEKLY;BYDAY=TU;INTERVAL=1"
        """
        try:
            # Parse recurrence rule
            rule = rrulestr(recurrence_rule, dtstart=start_date)

            # Generate occurrences
            occurrences = []
            if count:
                occurrences = list(rule[:count])
            elif end_date:
                occurrences = list(rule.between(start_date, end_date, inc=True))
            else:
                # Default to 10 occurrences if no end specified
                occurrences = list(rule[:10])

            # Create post instances
            recurring_posts = []
            post.is_recurring = True
            post.recurrence_rule = recurrence_rule

            for occurrence_time in occurrences:
                # Create new post instance
                new_post = Post(
                    id=uuid4(),
                    title=f"{post.title} ({occurrence_time.strftime('%Y-%m-%d')})",
                    content_by_platform=post.content_by_platform.copy(),
                    platforms=post.platforms.copy(),
                    status=PostStatus.SCHEDULED,
                    scheduled_time=occurrence_time,
                    campaign_id=post.campaign_id,
                    author_id=post.author_id,
                    parent_post_id=post.id,
                    is_recurring=True,
                    recurrence_rule=recurrence_rule,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )

                # Schedule the post
                self._scheduled_posts[new_post.id] = new_post
                self._queue.append((occurrence_time, new_post.id))
                recurring_posts.append(new_post)

            self._queue.sort(key=lambda x: x[0])
            logger.info(
                f"Created {len(recurring_posts)} recurring post instances for {post.id}"
            )
            return recurring_posts

        except Exception as e:
            logger.error(f"Failed to create recurring posts: {e}")
            raise SchedulingError(f"Recurring post creation failed: {e}")

    def get_queue(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        platform: Optional[PlatformType] = None,
    ) -> List[Tuple[datetime, Post]]:
        """
        Get scheduled posts queue.

        Args:
            start_date: Optional filter by start date
            end_date: Optional filter by end date
            platform: Optional filter by platform

        Returns:
            List of (scheduled_time, Post) tuples
        """
        queue = []
        for scheduled_time, post_id in self._queue:
            # Apply date filters
            if start_date and scheduled_time < start_date:
                continue
            if end_date and scheduled_time > end_date:
                continue

            post = self._scheduled_posts.get(post_id)
            if not post:
                continue

            # Apply platform filter
            if platform and platform not in post.platforms:
                continue

            queue.append((scheduled_time, post))

        return queue

    def get_next_posts(self, limit: int = 10) -> List[Tuple[datetime, Post]]:
        """
        Get next posts to be published.

        Args:
            limit: Maximum number of posts to return

        Returns:
            List of (scheduled_time, Post) tuples
        """
        now = datetime.now(pytz.UTC)
        upcoming = [
            (t, self._scheduled_posts[pid])
            for t, pid in self._queue
            if t > now and pid in self._scheduled_posts
        ]
        return upcoming[:limit]

    def get_due_posts(self) -> List[Post]:
        """
        Get posts that are due for publishing.

        Returns:
            List of Post objects due for publishing
        """
        now = datetime.now(pytz.UTC)
        due_posts = []

        for scheduled_time, post_id in self._queue:
            if scheduled_time <= now and post_id in self._scheduled_posts:
                post = self._scheduled_posts[post_id]
                if post.status == PostStatus.SCHEDULED:
                    due_posts.append(post)

        logger.info(f"Found {len(due_posts)} posts due for publishing")
        return due_posts

    def create_schedule(
        self,
        name: str,
        platforms: List[PlatformType],
        slots: List[Dict[str, Any]],
        timezone: str = "UTC",
        description: Optional[str] = None,
    ) -> Schedule:
        """
        Create a posting schedule template.

        Args:
            name: Schedule name
            platforms: Platforms for this schedule
            slots: Time slots (e.g., [{"day": 1, "hour": 9}, {"day": 3, "hour": 14}])
            timezone: Timezone for schedule
            description: Optional description

        Returns:
            Schedule object

        Example slots:
            [
                {"day": 1, "hour": 9, "minute": 0},  # Tuesday 9am
                {"day": 3, "hour": 14, "minute": 30},  # Thursday 2:30pm
            ]
        """
        schedule = Schedule(
            id=uuid4(),
            name=name,
            description=description,
            timezone=timezone,
            slots=slots,
            platforms=platforms,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        self._schedules[schedule.id] = schedule
        logger.info(f"Created schedule {schedule.id}: {name}")
        return schedule

    def apply_schedule(
        self,
        schedule_id: UUID,
        posts: List[Post],
        start_date: datetime,
        weeks: int = 4,
    ) -> List[Post]:
        """
        Apply a schedule template to posts.

        Args:
            schedule_id: Schedule UUID
            posts: Posts to schedule
            start_date: Start date for scheduling
            weeks: Number of weeks to schedule

        Returns:
            List of scheduled Post objects

        Raises:
            ValueError: If schedule not found
        """
        if schedule_id not in self._schedules:
            raise ValueError(f"Schedule {schedule_id} not found")

        schedule = self._schedules[schedule_id]
        tz = pytz.timezone(schedule.timezone)
        scheduled_posts = []

        post_index = 0
        for week in range(weeks):
            for slot in schedule.slots:
                if post_index >= len(posts):
                    break

                # Calculate scheduled time
                days_offset = week * 7 + slot["day"]
                scheduled_time = start_date + timedelta(days=days_offset)
                scheduled_time = scheduled_time.replace(
                    hour=slot.get("hour", 9),
                    minute=slot.get("minute", 0),
                    second=0,
                    microsecond=0,
                )

                # Localize and schedule
                scheduled_time = tz.localize(scheduled_time)
                post = posts[post_index]
                self.schedule_post(post, scheduled_time)
                scheduled_posts.append(post)

                post_index += 1

        logger.info(
            f"Applied schedule {schedule_id} to {len(scheduled_posts)} posts"
        )
        return scheduled_posts

    def get_schedule_conflicts(
        self, scheduled_time: datetime, platform: PlatformType, window_minutes: int = 15
    ) -> List[Post]:
        """
        Check for scheduling conflicts.

        Args:
            scheduled_time: Proposed time
            platform: Platform to check
            window_minutes: Conflict window in minutes

        Returns:
            List of conflicting Post objects
        """
        conflicts = []
        start_window = scheduled_time - timedelta(minutes=window_minutes)
        end_window = scheduled_time + timedelta(minutes=window_minutes)

        for post_time, post_id in self._queue:
            if start_window <= post_time <= end_window:
                post = self._scheduled_posts.get(post_id)
                if post and platform in post.platforms:
                    conflicts.append(post)

        return conflicts

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get scheduling statistics.

        Returns:
            Dictionary with scheduling stats
        """
        now = datetime.now(pytz.UTC)
        scheduled_count = len(self._queue)
        upcoming_24h = sum(
            1 for t, _ in self._queue if now < t <= now + timedelta(hours=24)
        )
        upcoming_week = sum(
            1 for t, _ in self._queue if now < t <= now + timedelta(days=7)
        )

        platform_breakdown = {}
        for _, post_id in self._queue:
            post = self._scheduled_posts.get(post_id)
            if post:
                for platform in post.platforms:
                    platform_breakdown[platform.value] = (
                        platform_breakdown.get(platform.value, 0) + 1
                    )

        return {
            "total_scheduled": scheduled_count,
            "upcoming_24h": upcoming_24h,
            "upcoming_week": upcoming_week,
            "by_platform": platform_breakdown,
            "active_schedules": len(
                [s for s in self._schedules.values() if s.is_active]
            ),
        }
