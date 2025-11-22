"""
Social Media Module - Visual Calendar.

This module provides calendar views, drag-and-drop scheduling,
and content planning visualization.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from .scheduling import PostScheduler
from .social_types import Post

logger = logging.getLogger(__name__)


class SocialCalendar:
    """Visual social media content calendar."""

    def __init__(self, scheduler: PostScheduler):
        """Initialize calendar."""
        self.scheduler = scheduler

    def get_month_view(
        self, year: int, month: int
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get calendar view for a specific month."""
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)

        queue = self.scheduler.get_queue(start_date=start_date, end_date=end_date)

        calendar_data: Dict[str, List[Dict[str, Any]]] = {}
        for scheduled_time, post in queue:
            date_key = scheduled_time.strftime("%Y-%m-%d")
            if date_key not in calendar_data:
                calendar_data[date_key] = []

            calendar_data[date_key].append({
                "time": scheduled_time.strftime("%H:%M"),
                "title": post.title,
                "post_id": str(post.id),
                "platforms": [p.value for p in post.platforms],
                "status": post.status.value,
            })

        return calendar_data

    def get_week_view(self, start_date: datetime) -> Dict[str, List[Dict[str, Any]]]:
        """Get week view starting from a specific date."""
        end_date = start_date + timedelta(days=7)
        queue = self.scheduler.get_queue(start_date=start_date, end_date=end_date)

        week_data: Dict[str, List[Dict[str, Any]]] = {}
        for scheduled_time, post in queue:
            date_key = scheduled_time.strftime("%Y-%m-%d")
            if date_key not in week_data:
                week_data[date_key] = []

            week_data[date_key].append({
                "time": scheduled_time.strftime("%H:%M"),
                "title": post.title,
                "post_id": str(post.id),
                "platforms": [p.value for p in post.platforms],
            })

        return week_data
