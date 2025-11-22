"""
Social Media Module - Link Management and Tracking.

This module provides URL shortening, UTM parameter management,
click tracking, and bio link page functionality.
"""

import hashlib
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from .social_types import ShortLink

logger = logging.getLogger(__name__)


class LinkError(Exception):
    """Base exception for link management errors."""

    pass


class LinkManager:
    """URL shortening and tracking manager."""

    def __init__(self, base_domain: str = "short.link"):
        """
        Initialize link manager.

        Args:
            base_domain: Base domain for short URLs
        """
        self.base_domain = base_domain
        self._links: Dict[UUID, ShortLink] = {}
        self._short_code_map: Dict[str, UUID] = {}  # short_code -> link_id

    def create_short_link(
        self,
        original_url: str,
        post_id: Optional[UUID] = None,
        campaign_id: Optional[UUID] = None,
        utm_source: Optional[str] = None,
        utm_medium: Optional[str] = None,
        utm_campaign: Optional[str] = None,
        utm_term: Optional[str] = None,
        utm_content: Optional[str] = None,
        custom_code: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ) -> ShortLink:
        """
        Create a shortened URL with tracking.

        Args:
            original_url: Original long URL
            post_id: Optional associated post UUID
            campaign_id: Optional associated campaign UUID
            utm_source: UTM source parameter
            utm_medium: UTM medium parameter
            utm_campaign: UTM campaign parameter
            utm_term: UTM term parameter
            utm_content: UTM content parameter
            custom_code: Optional custom short code
            expires_at: Optional expiration date

        Returns:
            ShortLink object

        Raises:
            LinkError: If link creation fails
        """
        try:
            # Build full URL with UTM parameters
            full_url = self._build_url_with_utm(
                original_url,
                utm_source=utm_source,
                utm_medium=utm_medium,
                utm_campaign=utm_campaign,
                utm_term=utm_term,
                utm_content=utm_content,
            )

            # Generate short code
            if custom_code:
                if custom_code in self._short_code_map:
                    raise LinkError(f"Custom code '{custom_code}' already in use")
                short_code = custom_code
            else:
                short_code = self._generate_short_code(original_url)

            # Create short URL
            short_url = f"https://{self.base_domain}/{short_code}"

            # Create link object
            link = ShortLink(
                id=uuid4(),
                original_url=full_url,
                short_code=short_code,
                short_url=short_url,
                post_id=post_id,
                campaign_id=campaign_id,
                utm_source=utm_source,
                utm_medium=utm_medium,
                utm_campaign=utm_campaign,
                utm_term=utm_term,
                utm_content=utm_content,
                clicks=0,
                unique_clicks=0,
                click_details=[],
                created_at=datetime.utcnow(),
                expires_at=expires_at,
                is_active=True,
            )

            self._links[link.id] = link
            self._short_code_map[short_code] = link.id

            logger.info(f"Created short link: {short_url} -> {original_url}")
            return link

        except Exception as e:
            logger.error(f"Failed to create short link: {e}")
            raise LinkError(f"Link creation failed: {e}")

    def _build_url_with_utm(
        self,
        url: str,
        utm_source: Optional[str] = None,
        utm_medium: Optional[str] = None,
        utm_campaign: Optional[str] = None,
        utm_term: Optional[str] = None,
        utm_content: Optional[str] = None,
    ) -> str:
        """Build URL with UTM parameters."""
        params = []

        if utm_source:
            params.append(f"utm_source={utm_source}")
        if utm_medium:
            params.append(f"utm_medium={utm_medium}")
        if utm_campaign:
            params.append(f"utm_campaign={utm_campaign}")
        if utm_term:
            params.append(f"utm_term={utm_term}")
        if utm_content:
            params.append(f"utm_content={utm_content}")

        if params:
            separator = "&" if "?" in url else "?"
            return f"{url}{separator}{'&'.join(params)}"

        return url

    def _generate_short_code(self, url: str, length: int = 6) -> str:
        """
        Generate a short code for a URL.

        Args:
            url: URL to generate code for
            length: Length of short code

        Returns:
            Short code string
        """
        # Use hash for consistency
        hash_object = hashlib.md5(url.encode())
        hash_hex = hash_object.hexdigest()

        # Convert to base62-like string
        code = hash_hex[:length]

        # Ensure uniqueness
        counter = 0
        while code in self._short_code_map:
            counter += 1
            code = f"{hash_hex[:length-1]}{counter}"

        return code

    def track_click(
        self,
        short_code: str,
        visitor_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Track a click on a short link.

        Args:
            short_code: Short code of the link
            visitor_data: Optional visitor information (IP, user-agent, etc.)

        Returns:
            True if tracked, False if link not found
        """
        if short_code not in self._short_code_map:
            return False

        link_id = self._short_code_map[short_code]
        link = self._links[link_id]

        # Check if active and not expired
        if not link.is_active:
            return False
        if link.expires_at and link.expires_at < datetime.utcnow():
            link.is_active = False
            return False

        # Increment clicks
        link.clicks += 1

        # Track unique clicks (simple implementation - in production use more sophisticated tracking)
        visitor_id = visitor_data.get("visitor_id") if visitor_data else None
        is_unique = not any(
            c.get("visitor_id") == visitor_id for c in link.click_details
        )

        if is_unique:
            link.unique_clicks += 1

        # Store click details
        click_detail = {
            "timestamp": datetime.utcnow().isoformat(),
            "visitor_id": visitor_id,
            "ip_address": visitor_data.get("ip_address") if visitor_data else None,
            "user_agent": visitor_data.get("user_agent") if visitor_data else None,
            "referrer": visitor_data.get("referrer") if visitor_data else None,
            "country": visitor_data.get("country") if visitor_data else None,
            "device": visitor_data.get("device") if visitor_data else None,
        }

        link.click_details.append(click_detail)

        logger.info(f"Tracked click on {short_code} (total: {link.clicks})")
        return True

    def get_link_by_code(self, short_code: str) -> Optional[ShortLink]:
        """
        Get a link by its short code.

        Args:
            short_code: Short code

        Returns:
            ShortLink object or None
        """
        link_id = self._short_code_map.get(short_code)
        if link_id:
            return self._links.get(link_id)
        return None

    def get_link(self, link_id: UUID) -> Optional[ShortLink]:
        """
        Get a link by ID.

        Args:
            link_id: Link UUID

        Returns:
            ShortLink object or None
        """
        return self._links.get(link_id)

    def get_campaign_links(self, campaign_id: UUID) -> List[ShortLink]:
        """
        Get all links for a campaign.

        Args:
            campaign_id: Campaign UUID

        Returns:
            List of ShortLink objects
        """
        return [
            link
            for link in self._links.values()
            if link.campaign_id == campaign_id
        ]

    def get_post_links(self, post_id: UUID) -> List[ShortLink]:
        """
        Get all links for a post.

        Args:
            post_id: Post UUID

        Returns:
            List of ShortLink objects
        """
        return [link for link in self._links.values() if link.post_id == post_id]

    def get_link_analytics(self, link_id: UUID) -> Dict[str, Any]:
        """
        Get analytics for a link.

        Args:
            link_id: Link UUID

        Returns:
            Analytics dictionary

        Raises:
            ValueError: If link not found
        """
        if link_id not in self._links:
            raise ValueError(f"Link {link_id} not found")

        link = self._links[link_id]

        # Analyze click data
        total_clicks = link.clicks
        unique_clicks = link.unique_clicks
        click_through_rate = (
            (unique_clicks / total_clicks * 100) if total_clicks > 0 else 0.0
        )

        # Analyze devices
        device_breakdown = {}
        country_breakdown = {}
        referrer_breakdown = {}

        for click in link.click_details:
            # Devices
            device = click.get("device", "unknown")
            device_breakdown[device] = device_breakdown.get(device, 0) + 1

            # Countries
            country = click.get("country", "unknown")
            country_breakdown[country] = country_breakdown.get(country, 0) + 1

            # Referrers
            referrer = click.get("referrer", "direct")
            referrer_breakdown[referrer] = referrer_breakdown.get(referrer, 0) + 1

        # Calculate click timeline
        clicks_by_hour = {}
        for click in link.click_details:
            timestamp = datetime.fromisoformat(click["timestamp"])
            hour_key = timestamp.strftime("%Y-%m-%d %H:00")
            clicks_by_hour[hour_key] = clicks_by_hour.get(hour_key, 0) + 1

        return {
            "link_id": str(link_id),
            "short_url": link.short_url,
            "original_url": link.original_url,
            "created_at": link.created_at.isoformat(),
            "total_clicks": total_clicks,
            "unique_clicks": unique_clicks,
            "click_through_rate": round(click_through_rate, 2),
            "is_active": link.is_active,
            "expires_at": link.expires_at.isoformat() if link.expires_at else None,
            "utm_parameters": {
                "source": link.utm_source,
                "medium": link.utm_medium,
                "campaign": link.utm_campaign,
                "term": link.utm_term,
                "content": link.utm_content,
            },
            "breakdown": {
                "by_device": device_breakdown,
                "by_country": country_breakdown,
                "by_referrer": referrer_breakdown,
            },
            "timeline": clicks_by_hour,
        }

    def update_link(
        self,
        link_id: UUID,
        is_active: Optional[bool] = None,
        expires_at: Optional[datetime] = None,
    ) -> ShortLink:
        """
        Update a link's settings.

        Args:
            link_id: Link UUID
            is_active: New active status
            expires_at: New expiration date

        Returns:
            Updated ShortLink object

        Raises:
            ValueError: If link not found
        """
        if link_id not in self._links:
            raise ValueError(f"Link {link_id} not found")

        link = self._links[link_id]

        if is_active is not None:
            link.is_active = is_active
        if expires_at is not None:
            link.expires_at = expires_at

        logger.info(f"Updated link {link_id}")
        return link

    def delete_link(self, link_id: UUID) -> bool:
        """
        Delete a link.

        Args:
            link_id: Link UUID

        Returns:
            True if deleted, False if not found
        """
        if link_id in self._links:
            link = self._links[link_id]
            del self._short_code_map[link.short_code]
            del self._links[link_id]
            logger.info(f"Deleted link {link_id}")
            return True
        return False

    def get_top_performing_links(
        self,
        campaign_id: Optional[UUID] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get top performing links.

        Args:
            campaign_id: Optional filter by campaign
            limit: Maximum links to return

        Returns:
            List of link performance data
        """
        links = list(self._links.values())

        if campaign_id:
            links = [l for l in links if l.campaign_id == campaign_id]

        # Sort by clicks
        links.sort(key=lambda l: l.clicks, reverse=True)

        return [
            {
                "link_id": str(link.id),
                "short_url": link.short_url,
                "clicks": link.clicks,
                "unique_clicks": link.unique_clicks,
                "campaign_id": str(link.campaign_id) if link.campaign_id else None,
            }
            for link in links[:limit]
        ]

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get link tracking statistics.

        Returns:
            Statistics dictionary
        """
        total_links = len(self._links)
        active_links = sum(1 for l in self._links.values() if l.is_active)
        total_clicks = sum(l.clicks for l in self._links.values())
        total_unique = sum(l.unique_clicks for l in self._links.values())

        return {
            "total_links": total_links,
            "active_links": active_links,
            "total_clicks": total_clicks,
            "total_unique_clicks": total_unique,
            "avg_clicks_per_link": round(total_clicks / total_links, 2)
            if total_links > 0
            else 0,
        }
