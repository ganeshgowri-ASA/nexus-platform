"""Email tracking system for tracking opens, clicks, and engagement."""

import re
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime
from urllib.parse import urlencode
import logging

from sqlalchemy.orm import Session

from src.modules.email.models import Email, EmailTrackingEvent
from src.core.config import settings

logger = logging.getLogger(__name__)


class EmailTracker:
    """Email tracking system."""

    def __init__(
        self,
        db: Optional[Session] = None,
        tracking_domain: str = "http://localhost:8000"
    ):
        """Initialize email tracker.

        Args:
            db: Database session
            tracking_domain: Domain for tracking URLs
        """
        self.db = db
        self.tracking_domain = tracking_domain.rstrip('/')

    def add_tracking_pixel(
        self,
        email_id: int,
        html_body: str
    ) -> str:
        """Add tracking pixel to HTML email.

        Args:
            email_id: Email ID
            html_body: HTML email body

        Returns:
            Modified HTML with tracking pixel
        """
        if not settings.email_tracking_enabled:
            return html_body

        # Generate tracking URL
        tracking_url = self._generate_tracking_url('open', email_id)

        # Create tracking pixel
        tracking_pixel = (
            f'<img src="{tracking_url}" '
            f'width="1" height="1" border="0" '
            f'style="display:none" />'
        )

        # Try to insert before closing body tag
        if '</body>' in html_body:
            html_body = html_body.replace('</body>', f'{tracking_pixel}</body>')
        else:
            # Append to end if no body tag
            html_body += tracking_pixel

        logger.debug(f"Added tracking pixel to email {email_id}")
        return html_body

    def add_link_tracking(
        self,
        email_id: int,
        html_body: str
    ) -> str:
        """Add tracking to all links in HTML email.

        Args:
            email_id: Email ID
            html_body: HTML email body

        Returns:
            Modified HTML with tracked links
        """
        if not settings.email_tracking_enabled:
            return html_body

        def replace_link(match):
            """Replace link with tracked version."""
            full_tag = match.group(0)
            url = match.group(1)

            # Skip if already tracked or is tracking pixel
            if 'track/click' in url or url.startswith('mailto:'):
                return full_tag

            # Generate tracking URL
            tracking_url = self._generate_tracking_url('click', email_id, url)

            # Replace URL in tag
            return full_tag.replace(f'href="{url}"', f'href="{tracking_url}"')

        # Find and replace all href links
        pattern = r'href="([^"]+)"'
        modified_html = re.sub(pattern, replace_link, html_body)

        logger.debug(f"Added link tracking to email {email_id}")
        return modified_html

    def _generate_tracking_url(
        self,
        event_type: str,
        email_id: int,
        target_url: Optional[str] = None
    ) -> str:
        """Generate tracking URL.

        Args:
            event_type: Type of event (open, click)
            email_id: Email ID
            target_url: Target URL for click tracking

        Returns:
            Tracking URL
        """
        params = {
            'email_id': email_id,
            'event': event_type,
            't': int(datetime.utcnow().timestamp())
        }

        if target_url:
            params['url'] = target_url

        query_string = urlencode(params)
        return f"{self.tracking_domain}/api/email/track?{query_string}"

    def record_event(
        self,
        email_id: int,
        event_type: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        url: Optional[str] = None,
        location: Optional[str] = None
    ) -> Optional[EmailTrackingEvent]:
        """Record a tracking event.

        Args:
            email_id: Email ID
            event_type: Event type (opened, clicked, bounced, etc.)
            ip_address: Client IP address
            user_agent: Client user agent
            url: Clicked URL (for click events)
            location: Geographic location

        Returns:
            Created EmailTrackingEvent or None
        """
        if not self.db:
            logger.warning("Database session not provided")
            return None

        # Create tracking event
        event = EmailTrackingEvent(
            email_id=email_id,
            event_type=event_type,
            ip_address=ip_address,
            user_agent=user_agent,
            url=url,
            location=location
        )

        self.db.add(event)

        # Update email tracking statistics
        email = self.db.query(Email).filter_by(id=email_id).first()
        if email:
            if event_type == 'opened':
                email.opened_count += 1
                email.last_opened_at = datetime.utcnow()
                if not email.is_read:
                    email.is_read = True
            elif event_type == 'clicked':
                email.clicked_count += 1
                email.last_clicked_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(event)

        logger.info(f"Recorded {event_type} event for email {email_id}")
        return event

    def get_email_stats(self, email_id: int) -> Optional[Dict[str, Any]]:
        """Get tracking statistics for an email.

        Args:
            email_id: Email ID

        Returns:
            Dict with tracking statistics
        """
        if not self.db:
            logger.warning("Database session not provided")
            return None

        email = self.db.query(Email).filter_by(id=email_id).first()
        if not email:
            return None

        # Get event counts
        events = self.db.query(EmailTrackingEvent).filter_by(
            email_id=email_id
        ).all()

        open_events = [e for e in events if e.event_type == 'opened']
        click_events = [e for e in events if e.event_type == 'clicked']
        bounce_events = [e for e in events if e.event_type == 'bounced']

        # Get unique opens/clicks
        unique_ips_opened = set(e.ip_address for e in open_events if e.ip_address)
        unique_ips_clicked = set(e.ip_address for e in click_events if e.ip_address)

        return {
            'email_id': email_id,
            'sent_at': email.sent_at,
            'opened_count': email.opened_count,
            'unique_opens': len(unique_ips_opened),
            'first_opened_at': min(
                (e.timestamp for e in open_events),
                default=None
            ),
            'last_opened_at': email.last_opened_at,
            'clicked_count': email.clicked_count,
            'unique_clicks': len(unique_ips_clicked),
            'first_clicked_at': min(
                (e.timestamp for e in click_events),
                default=None
            ),
            'last_clicked_at': email.last_clicked_at,
            'bounced': len(bounce_events) > 0,
            'bounce_count': len(bounce_events),
            'events': [
                {
                    'type': e.event_type,
                    'timestamp': e.timestamp,
                    'ip_address': e.ip_address,
                    'location': e.location,
                    'url': e.url
                }
                for e in events
            ]
        }

    def get_campaign_stats(self, email_ids: List[int]) -> Dict[str, Any]:
        """Get aggregate statistics for multiple emails (campaign).

        Args:
            email_ids: List of email IDs

        Returns:
            Dict with campaign statistics
        """
        if not self.db:
            logger.warning("Database session not provided")
            return {}

        emails = self.db.query(Email).filter(Email.id.in_(email_ids)).all()

        total_sent = len(emails)
        total_opens = sum(e.opened_count for e in emails)
        total_clicks = sum(e.clicked_count for e in emails)
        unique_opens = len([e for e in emails if e.opened_count > 0])
        unique_clicks = len([e for e in emails if e.clicked_count > 0])

        return {
            'total_sent': total_sent,
            'total_opens': total_opens,
            'unique_opens': unique_opens,
            'open_rate': (unique_opens / total_sent * 100) if total_sent > 0 else 0,
            'total_clicks': total_clicks,
            'unique_clicks': unique_clicks,
            'click_rate': (unique_clicks / total_sent * 100) if total_sent > 0 else 0,
            'click_to_open_rate': (
                (unique_clicks / unique_opens * 100) if unique_opens > 0 else 0
            )
        }

    def get_top_clicked_links(
        self,
        email_id: Optional[int] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get most clicked links.

        Args:
            email_id: Specific email ID (optional)
            limit: Number of results

        Returns:
            List of dicts with URL and click count
        """
        if not self.db:
            logger.warning("Database session not provided")
            return []

        query = self.db.query(EmailTrackingEvent).filter_by(event_type='clicked')

        if email_id:
            query = query.filter_by(email_id=email_id)

        events = query.all()

        # Count clicks per URL
        url_clicks = {}
        for event in events:
            if event.url:
                url_clicks[event.url] = url_clicks.get(event.url, 0) + 1

        # Sort by click count
        sorted_urls = sorted(
            url_clicks.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]

        return [
            {'url': url, 'clicks': count}
            for url, count in sorted_urls
        ]

    def get_engagement_timeline(
        self,
        email_id: int,
        interval: str = 'hour'
    ) -> List[Dict[str, Any]]:
        """Get engagement timeline for an email.

        Args:
            email_id: Email ID
            interval: Time interval (hour, day)

        Returns:
            List of engagement data points
        """
        if not self.db:
            logger.warning("Database session not provided")
            return []

        events = self.db.query(EmailTrackingEvent).filter_by(
            email_id=email_id
        ).order_by(EmailTrackingEvent.timestamp).all()

        # Group by interval
        timeline = {}
        for event in events:
            if interval == 'hour':
                key = event.timestamp.replace(minute=0, second=0, microsecond=0)
            else:  # day
                key = event.timestamp.replace(hour=0, minute=0, second=0, microsecond=0)

            if key not in timeline:
                timeline[key] = {'opens': 0, 'clicks': 0}

            if event.event_type == 'opened':
                timeline[key]['opens'] += 1
            elif event.event_type == 'clicked':
                timeline[key]['clicks'] += 1

        # Convert to list
        return [
            {
                'timestamp': timestamp,
                'opens': data['opens'],
                'clicks': data['clicks']
            }
            for timestamp, data in sorted(timeline.items())
        ]

    def cleanup_old_events(self, days: int = 90) -> int:
        """Clean up old tracking events.

        Args:
            days: Number of days to keep

        Returns:
            Number of deleted events
        """
        if not self.db:
            logger.warning("Database session not provided")
            return 0

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        deleted = self.db.query(EmailTrackingEvent).filter(
            EmailTrackingEvent.timestamp < cutoff_date
        ).delete()

        self.db.commit()

        logger.info(f"Cleaned up {deleted} old tracking events")
        return deleted

    def export_events(
        self,
        email_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Export tracking events.

        Args:
            email_id: Filter by email ID
            start_date: Filter by start date
            end_date: Filter by end date

        Returns:
            List of event dicts
        """
        if not self.db:
            logger.warning("Database session not provided")
            return []

        query = self.db.query(EmailTrackingEvent)

        if email_id:
            query = query.filter_by(email_id=email_id)
        if start_date:
            query = query.filter(EmailTrackingEvent.timestamp >= start_date)
        if end_date:
            query = query.filter(EmailTrackingEvent.timestamp <= end_date)

        events = query.all()

        return [
            {
                'email_id': e.email_id,
                'event_type': e.event_type,
                'timestamp': e.timestamp.isoformat(),
                'ip_address': e.ip_address,
                'user_agent': e.user_agent,
                'location': e.location,
                'url': e.url
            }
            for e in events
        ]


# Import timedelta for cleanup
from datetime import timedelta
