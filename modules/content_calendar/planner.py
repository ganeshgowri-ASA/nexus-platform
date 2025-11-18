"""
Content planner module for visual calendar and drag-drop planning.

This module provides comprehensive content planning capabilities including:
- Visual calendar views (month, week, day)
- Drag-and-drop event scheduling
- Multi-channel content planning
- Bulk operations
- Calendar filtering and search
"""
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from loguru import logger

from database import ContentItem, Campaign, User, ContentStatus
from .calendar_types import (
    CalendarEvent,
    ContentPlan,
    ScheduleConfig,
    Priority,
    ApprovalStatus,
    PublishingChannel,
)


class ContentPlanner:
    """Content planner for visual calendar management."""

    def __init__(self, db: Session):
        """
        Initialize content planner.

        Args:
            db: Database session
        """
        self.db = db
        logger.info("ContentPlanner initialized")

    def get_calendar_view(
        self,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[int] = None,
        channels: Optional[list[str]] = None,
        status: Optional[list[ApprovalStatus]] = None,
        campaign_id: Optional[int] = None,
    ) -> list[CalendarEvent]:
        """
        Get calendar events for a date range.

        Args:
            start_date: Start date for calendar view
            end_date: End date for calendar view
            user_id: Filter by user (creator or assignee)
            channels: Filter by publishing channels
            status: Filter by approval status
            campaign_id: Filter by campaign

        Returns:
            List of calendar events in the date range
        """
        try:
            query = self.db.query(ContentItem).filter(
                and_(
                    ContentItem.scheduled_at >= start_date,
                    ContentItem.scheduled_at <= end_date,
                )
            )

            # Apply filters
            if user_id:
                query = query.filter(ContentItem.creator_id == user_id)

            if status:
                db_statuses = [self._map_approval_to_content_status(s) for s in status]
                query = query.filter(ContentItem.status.in_(db_statuses))

            if campaign_id:
                query = query.filter(ContentItem.campaign_id == campaign_id)

            if channels:
                # Filter by channels (stored as JSON array)
                query = query.filter(
                    or_(
                        *[
                            ContentItem.channels.contains([channel])
                            for channel in channels
                        ]
                    )
                )

            items = query.order_by(ContentItem.scheduled_at).all()

            # Convert to CalendarEvent objects
            events = [self._content_item_to_event(item) for item in items]

            logger.info(
                f"Retrieved {len(events)} events from {start_date} to {end_date}"
            )
            return events

        except Exception as e:
            logger.error(f"Error getting calendar view: {e}")
            raise

    def create_event(
        self,
        event: CalendarEvent,
        user_id: int,
    ) -> CalendarEvent:
        """
        Create a new calendar event.

        Args:
            event: Calendar event to create
            user_id: User creating the event

        Returns:
            Created calendar event with ID
        """
        try:
            # Create content item
            content_item = ContentItem(
                title=event.title,
                content=event.content,
                content_type=self._map_content_format(event.content_type),
                status=self._map_approval_to_content_status(event.status),
                creator_id=user_id,
                campaign_id=event.campaign_id,
                scheduled_at=event.schedule.scheduled_time,
                timezone=event.schedule.timezone,
                channels=[ch.name for ch in event.channels],
                media_urls=[media.url for media in event.media],
                tags=event.metadata.tags,
                metadata={
                    "categories": event.metadata.categories,
                    "keywords": event.metadata.keywords,
                    "target_audience": event.metadata.target_audience,
                    "language": event.metadata.language,
                    "location": event.metadata.location,
                    "custom_fields": event.metadata.custom_fields,
                    "priority": event.priority,
                    "schedule_config": event.schedule.model_dump(),
                },
            )

            self.db.add(content_item)
            self.db.commit()
            self.db.refresh(content_item)

            # Convert back to event
            created_event = self._content_item_to_event(content_item)

            logger.info(f"Created event: {created_event.id} - {created_event.title}")
            return created_event

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating event: {e}")
            raise

    def update_event(
        self,
        event_id: int,
        event_data: dict,
        user_id: int,
    ) -> CalendarEvent:
        """
        Update an existing calendar event.

        Args:
            event_id: Event ID to update
            event_data: Updated event data
            user_id: User performing the update

        Returns:
            Updated calendar event
        """
        try:
            content_item = (
                self.db.query(ContentItem)
                .filter(ContentItem.id == event_id)
                .first()
            )

            if not content_item:
                raise ValueError(f"Event {event_id} not found")

            # Update fields
            for key, value in event_data.items():
                if hasattr(content_item, key):
                    setattr(content_item, key, value)

            content_item.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(content_item)

            updated_event = self._content_item_to_event(content_item)

            logger.info(f"Updated event: {event_id}")
            return updated_event

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating event {event_id}: {e}")
            raise

    def move_event(
        self,
        event_id: int,
        new_datetime: datetime,
        new_timezone: Optional[str] = None,
    ) -> CalendarEvent:
        """
        Move event to a new date/time (drag-and-drop).

        Args:
            event_id: Event ID to move
            new_datetime: New scheduled datetime
            new_timezone: New timezone (optional)

        Returns:
            Updated calendar event
        """
        try:
            content_item = (
                self.db.query(ContentItem)
                .filter(ContentItem.id == event_id)
                .first()
            )

            if not content_item:
                raise ValueError(f"Event {event_id} not found")

            content_item.scheduled_at = new_datetime
            if new_timezone:
                content_item.timezone = new_timezone

            content_item.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(content_item)

            moved_event = self._content_item_to_event(content_item)

            logger.info(f"Moved event {event_id} to {new_datetime}")
            return moved_event

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error moving event {event_id}: {e}")
            raise

    def duplicate_event(
        self,
        event_id: int,
        new_datetime: Optional[datetime] = None,
    ) -> CalendarEvent:
        """
        Duplicate an existing event.

        Args:
            event_id: Event ID to duplicate
            new_datetime: Scheduled time for duplicate (optional)

        Returns:
            Newly created duplicate event
        """
        try:
            original = (
                self.db.query(ContentItem)
                .filter(ContentItem.id == event_id)
                .first()
            )

            if not original:
                raise ValueError(f"Event {event_id} not found")

            # Create duplicate
            duplicate = ContentItem(
                title=f"{original.title} (Copy)",
                content=original.content,
                content_type=original.content_type,
                status=ContentStatus.DRAFT,
                creator_id=original.creator_id,
                campaign_id=original.campaign_id,
                scheduled_at=new_datetime or original.scheduled_at,
                timezone=original.timezone,
                channels=original.channels,
                media_urls=original.media_urls,
                tags=original.tags,
                metadata=original.metadata,
            )

            self.db.add(duplicate)
            self.db.commit()
            self.db.refresh(duplicate)

            duplicated_event = self._content_item_to_event(duplicate)

            logger.info(f"Duplicated event {event_id} to {duplicate.id}")
            return duplicated_event

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error duplicating event {event_id}: {e}")
            raise

    def delete_event(self, event_id: int) -> bool:
        """
        Delete a calendar event.

        Args:
            event_id: Event ID to delete

        Returns:
            True if deleted successfully
        """
        try:
            content_item = (
                self.db.query(ContentItem)
                .filter(ContentItem.id == event_id)
                .first()
            )

            if not content_item:
                raise ValueError(f"Event {event_id} not found")

            self.db.delete(content_item)
            self.db.commit()

            logger.info(f"Deleted event: {event_id}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting event {event_id}: {e}")
            raise

    def bulk_update_events(
        self,
        event_ids: list[int],
        updates: dict,
    ) -> list[CalendarEvent]:
        """
        Update multiple events at once.

        Args:
            event_ids: List of event IDs to update
            updates: Dictionary of fields to update

        Returns:
            List of updated events
        """
        try:
            content_items = (
                self.db.query(ContentItem)
                .filter(ContentItem.id.in_(event_ids))
                .all()
            )

            for item in content_items:
                for key, value in updates.items():
                    if hasattr(item, key):
                        setattr(item, key, value)
                item.updated_at = datetime.utcnow()

            self.db.commit()

            updated_events = [
                self._content_item_to_event(item) for item in content_items
            ]

            logger.info(f"Bulk updated {len(updated_events)} events")
            return updated_events

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error bulk updating events: {e}")
            raise

    def create_content_plan(
        self,
        plan: ContentPlan,
        user_id: int,
    ) -> ContentPlan:
        """
        Create a comprehensive content plan.

        Args:
            plan: Content plan to create
            user_id: User creating the plan

        Returns:
            Created content plan with ID
        """
        try:
            # Create campaign
            campaign = Campaign(
                name=plan.name,
                description=plan.description,
                start_date=plan.start_date,
                end_date=plan.end_date,
                status="active",
                budget=plan.budget,
                goals=plan.goals,
            )

            self.db.add(campaign)
            self.db.commit()
            self.db.refresh(campaign)

            # Create events
            created_events = []
            for event in plan.events:
                event.campaign_id = campaign.id
                created_event = self.create_event(event, user_id)
                created_events.append(created_event)

            plan.id = campaign.id
            plan.events = created_events

            logger.info(
                f"Created content plan: {plan.id} with {len(created_events)} events"
            )
            return plan

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating content plan: {e}")
            raise

    def get_content_plan(self, plan_id: int) -> Optional[ContentPlan]:
        """
        Get a content plan by ID.

        Args:
            plan_id: Plan ID (campaign ID)

        Returns:
            Content plan or None if not found
        """
        try:
            campaign = (
                self.db.query(Campaign).filter(Campaign.id == plan_id).first()
            )

            if not campaign:
                return None

            # Get associated events
            events = self.get_calendar_view(
                start_date=campaign.start_date,
                end_date=campaign.end_date,
                campaign_id=campaign.id,
            )

            plan = ContentPlan(
                id=campaign.id,
                name=campaign.name,
                description=campaign.description,
                start_date=campaign.start_date,
                end_date=campaign.end_date,
                events=events,
                goals=campaign.goals,
                budget=campaign.budget,
                created_at=campaign.created_at,
                updated_at=campaign.updated_at,
            )

            return plan

        except Exception as e:
            logger.error(f"Error getting content plan {plan_id}: {e}")
            raise

    def _content_item_to_event(self, item: ContentItem) -> CalendarEvent:
        """Convert ContentItem to CalendarEvent."""
        from .calendar_types import (
            ContentFormat,
            MediaAsset,
            ContentMetadata,
        )

        # Extract metadata
        metadata_dict = item.metadata or {}
        priority = Priority(metadata_dict.get("priority", "medium"))

        # Build schedule config
        schedule_data = metadata_dict.get("schedule_config", {})
        schedule = ScheduleConfig(
            scheduled_time=item.scheduled_at or datetime.utcnow(),
            timezone=item.timezone,
            auto_schedule=schedule_data.get("auto_schedule", False),
            send_notification=schedule_data.get("send_notification", True),
            retry_on_failure=schedule_data.get("retry_on_failure", True),
            max_retries=schedule_data.get("max_retries", 3),
        )

        # Build channels
        channels = [
            PublishingChannel(name=ch, platform=ch, is_active=True)
            for ch in (item.channels or [])
        ]

        # Build media assets
        media = [
            MediaAsset(
                url=url,
                type="image",
                filename=url.split("/")[-1],
                size=0,
            )
            for url in (item.media_urls or [])
        ]

        # Build metadata
        metadata = ContentMetadata(
            tags=item.tags or [],
            categories=metadata_dict.get("categories", []),
            keywords=metadata_dict.get("keywords", []),
            target_audience=metadata_dict.get("target_audience"),
            language=metadata_dict.get("language", "en"),
            location=metadata_dict.get("location"),
            custom_fields=metadata_dict.get("custom_fields", {}),
        )

        return CalendarEvent(
            id=item.id,
            title=item.title,
            content=item.content,
            content_type=ContentFormat.TEXT,
            status=self._map_content_to_approval_status(item.status),
            priority=priority,
            schedule=schedule,
            channels=channels,
            media=media,
            metadata=metadata,
            campaign_id=item.campaign_id,
            creator_id=item.creator_id,
            assignees=[],
            views=item.views,
            likes=item.likes,
            shares=item.shares,
            comments=item.comments_count,
            engagement_rate=item.engagement_rate,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    def _map_approval_to_content_status(
        self, status: ApprovalStatus
    ) -> ContentStatus:
        """Map ApprovalStatus to ContentStatus."""
        mapping = {
            ApprovalStatus.DRAFT: ContentStatus.DRAFT,
            ApprovalStatus.PENDING_REVIEW: ContentStatus.IN_REVIEW,
            ApprovalStatus.IN_REVIEW: ContentStatus.IN_REVIEW,
            ApprovalStatus.APPROVED: ContentStatus.APPROVED,
            ApprovalStatus.SCHEDULED: ContentStatus.SCHEDULED,
            ApprovalStatus.PUBLISHED: ContentStatus.PUBLISHED,
            ApprovalStatus.FAILED: ContentStatus.FAILED,
        }
        return mapping.get(status, ContentStatus.DRAFT)

    def _map_content_to_approval_status(
        self, status: ContentStatus
    ) -> ApprovalStatus:
        """Map ContentStatus to ApprovalStatus."""
        mapping = {
            ContentStatus.DRAFT: ApprovalStatus.DRAFT,
            ContentStatus.IN_REVIEW: ApprovalStatus.IN_REVIEW,
            ContentStatus.APPROVED: ApprovalStatus.APPROVED,
            ContentStatus.SCHEDULED: ApprovalStatus.SCHEDULED,
            ContentStatus.PUBLISHED: ApprovalStatus.PUBLISHED,
            ContentStatus.FAILED: ApprovalStatus.FAILED,
        }
        return mapping.get(status, ApprovalStatus.DRAFT)

    def _map_content_format(self, format: str) -> str:
        """Map ContentFormat to database content type."""
        from database import ContentType

        mapping = {
            "text": ContentType.SOCIAL_POST,
            "image": ContentType.IMAGE,
            "video": ContentType.VIDEO,
            "article": ContentType.ARTICLE,
        }
        return mapping.get(format, ContentType.SOCIAL_POST)
