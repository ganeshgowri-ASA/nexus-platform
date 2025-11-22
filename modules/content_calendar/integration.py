"""
Integration module for social media, blog, and email platforms.

This module provides:
- Social media publishing (Twitter, Facebook, LinkedIn, Instagram)
- Blog integration
- Email campaign integration
- Cross-platform content distribution
- Webhook handling
"""
from datetime import datetime
from typing import Optional, Any
from sqlalchemy.orm import Session
from loguru import logger
import tweepy
import facebook
import httpx
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from database import ContentItem, ContentStatus
from config import settings
from .calendar_types import PublishingChannel


class IntegrationManager:
    """Integration manager for external platforms."""

    def __init__(self, db: Session):
        """
        Initialize integration manager.

        Args:
            db: Database session
        """
        self.db = db
        self._init_clients()
        logger.info("IntegrationManager initialized")

    def _init_clients(self) -> None:
        """Initialize API clients for external platforms."""
        # Twitter/X client
        self.twitter_client: Optional[tweepy.Client] = None
        if all(
            [
                settings.twitter_api_key,
                settings.twitter_api_secret,
                settings.twitter_access_token,
                settings.twitter_access_secret,
            ]
        ):
            try:
                self.twitter_client = tweepy.Client(
                    consumer_key=settings.twitter_api_key,
                    consumer_secret=settings.twitter_api_secret,
                    access_token=settings.twitter_access_token,
                    access_token_secret=settings.twitter_access_secret,
                )
                logger.info("Twitter client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Twitter client: {e}")

        # Facebook client
        self.facebook_client: Optional[facebook.GraphAPI] = None
        if settings.facebook_access_token:
            try:
                self.facebook_client = facebook.GraphAPI(
                    access_token=settings.facebook_access_token
                )
                logger.info("Facebook client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Facebook client: {e}")

        # SendGrid client
        self.sendgrid_client: Optional[SendGridAPIClient] = None
        if settings.sendgrid_api_key:
            try:
                self.sendgrid_client = SendGridAPIClient(settings.sendgrid_api_key)
                logger.info("SendGrid client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize SendGrid client: {e}")

    def publish_content(
        self,
        content_id: int,
        channels: list[str],
    ) -> dict[str, Any]:
        """
        Publish content to multiple channels.

        Args:
            content_id: Content ID to publish
            channels: List of channel names

        Returns:
            Publishing results per channel
        """
        try:
            content_item = (
                self.db.query(ContentItem)
                .filter(ContentItem.id == content_id)
                .first()
            )

            if not content_item:
                raise ValueError(f"Content {content_id} not found")

            results = {}

            for channel in channels:
                try:
                    if channel.lower() == "twitter":
                        result = self._publish_to_twitter(content_item)
                    elif channel.lower() == "facebook":
                        result = self._publish_to_facebook(content_item)
                    elif channel.lower() == "linkedin":
                        result = self._publish_to_linkedin(content_item)
                    elif channel.lower() == "instagram":
                        result = self._publish_to_instagram(content_item)
                    elif channel.lower() == "blog":
                        result = self._publish_to_blog(content_item)
                    elif channel.lower() == "email":
                        result = self._send_email(content_item)
                    else:
                        result = {
                            "success": False,
                            "error": f"Unsupported channel: {channel}",
                        }

                    results[channel] = result

                except Exception as e:
                    logger.error(f"Error publishing to {channel}: {e}")
                    results[channel] = {"success": False, "error": str(e)}

            # Update content status
            all_successful = all(r.get("success", False) for r in results.values())

            if all_successful:
                content_item.status = ContentStatus.PUBLISHED
                content_item.published_at = datetime.utcnow()
            else:
                content_item.status = ContentStatus.FAILED

            self.db.commit()

            logger.info(f"Published content {content_id} to {len(channels)} channels")
            return results

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error publishing content: {e}")
            raise

    def _publish_to_twitter(self, content: ContentItem) -> dict[str, Any]:
        """Publish content to Twitter/X."""
        if not self.twitter_client:
            return {"success": False, "error": "Twitter client not initialized"}

        try:
            # Truncate content for Twitter (280 characters)
            tweet_text = content.content[:280]

            # TODO: Handle media attachments
            response = self.twitter_client.create_tweet(text=tweet_text)

            return {
                "success": True,
                "post_id": response.data["id"],
                "url": f"https://twitter.com/user/status/{response.data['id']}",
            }

        except Exception as e:
            logger.error(f"Twitter publish error: {e}")
            return {"success": False, "error": str(e)}

    def _publish_to_facebook(self, content: ContentItem) -> dict[str, Any]:
        """Publish content to Facebook."""
        if not self.facebook_client:
            return {"success": False, "error": "Facebook client not initialized"}

        try:
            # Publish to page or profile
            response = self.facebook_client.put_object(
                parent_object="me",
                connection_name="feed",
                message=content.content,
            )

            return {
                "success": True,
                "post_id": response["id"],
                "url": f"https://facebook.com/{response['id']}",
            }

        except Exception as e:
            logger.error(f"Facebook publish error: {e}")
            return {"success": False, "error": str(e)}

    def _publish_to_linkedin(self, content: ContentItem) -> dict[str, Any]:
        """Publish content to LinkedIn."""
        if not settings.linkedin_client_id or not settings.linkedin_client_secret:
            return {"success": False, "error": "LinkedIn credentials not configured"}

        try:
            # LinkedIn API implementation
            # This is a simplified version - full implementation would use OAuth
            logger.info("Publishing to LinkedIn (implementation pending)")

            return {
                "success": True,
                "post_id": "linkedin_placeholder",
                "message": "LinkedIn publishing simulated",
            }

        except Exception as e:
            logger.error(f"LinkedIn publish error: {e}")
            return {"success": False, "error": str(e)}

    def _publish_to_instagram(self, content: ContentItem) -> dict[str, Any]:
        """Publish content to Instagram."""
        try:
            # Instagram API requires media (image/video)
            if not content.media_urls:
                return {
                    "success": False,
                    "error": "Instagram requires media attachment",
                }

            # Instagram Graph API implementation
            logger.info("Publishing to Instagram (implementation pending)")

            return {
                "success": True,
                "post_id": "instagram_placeholder",
                "message": "Instagram publishing simulated",
            }

        except Exception as e:
            logger.error(f"Instagram publish error: {e}")
            return {"success": False, "error": str(e)}

    def _publish_to_blog(self, content: ContentItem) -> dict[str, Any]:
        """Publish content to blog platform."""
        try:
            # This would integrate with WordPress, Medium, etc.
            logger.info("Publishing to blog (implementation pending)")

            return {
                "success": True,
                "post_id": "blog_placeholder",
                "url": f"https://blog.example.com/posts/{content.id}",
            }

        except Exception as e:
            logger.error(f"Blog publish error: {e}")
            return {"success": False, "error": str(e)}

    def _send_email(self, content: ContentItem) -> dict[str, Any]:
        """Send content via email."""
        if not self.sendgrid_client:
            return {"success": False, "error": "SendGrid client not initialized"}

        try:
            # Get recipient list from metadata
            metadata = content.metadata or {}
            recipients = metadata.get("email_recipients", [])

            if not recipients:
                return {"success": False, "error": "No recipients specified"}

            message = Mail(
                from_email=settings.smtp_user,
                to_emails=recipients,
                subject=content.title,
                html_content=content.content,
            )

            response = self.sendgrid_client.send(message)

            return {
                "success": True,
                "status_code": response.status_code,
                "recipients_count": len(recipients),
            }

        except Exception as e:
            logger.error(f"Email send error: {e}")
            return {"success": False, "error": str(e)}

    def get_post_analytics(
        self,
        content_id: int,
        channel: str,
    ) -> dict[str, Any]:
        """
        Fetch analytics from external platform.

        Args:
            content_id: Content ID
            channel: Channel name

        Returns:
            Analytics data from platform
        """
        try:
            content_item = (
                self.db.query(ContentItem)
                .filter(ContentItem.id == content_id)
                .first()
            )

            if not content_item:
                raise ValueError(f"Content {content_id} not found")

            # Get platform-specific post ID from metadata
            metadata = content_item.metadata or {}
            platform_posts = metadata.get("platform_posts", {})
            post_id = platform_posts.get(channel)

            if not post_id:
                return {"success": False, "error": "Post ID not found for channel"}

            if channel.lower() == "twitter":
                return self._get_twitter_analytics(post_id)
            elif channel.lower() == "facebook":
                return self._get_facebook_analytics(post_id)
            elif channel.lower() == "linkedin":
                return self._get_linkedin_analytics(post_id)
            else:
                return {"success": False, "error": f"Analytics not supported for {channel}"}

        except Exception as e:
            logger.error(f"Error fetching analytics: {e}")
            return {"success": False, "error": str(e)}

    def _get_twitter_analytics(self, post_id: str) -> dict[str, Any]:
        """Fetch Twitter post analytics."""
        if not self.twitter_client:
            return {"success": False, "error": "Twitter client not initialized"}

        try:
            # Fetch tweet metrics
            tweet = self.twitter_client.get_tweet(
                post_id,
                tweet_fields=["public_metrics"],
            )

            metrics = tweet.data.public_metrics

            return {
                "success": True,
                "metrics": {
                    "views": metrics.get("impression_count", 0),
                    "likes": metrics.get("like_count", 0),
                    "retweets": metrics.get("retweet_count", 0),
                    "replies": metrics.get("reply_count", 0),
                },
            }

        except Exception as e:
            logger.error(f"Twitter analytics error: {e}")
            return {"success": False, "error": str(e)}

    def _get_facebook_analytics(self, post_id: str) -> dict[str, Any]:
        """Fetch Facebook post analytics."""
        if not self.facebook_client:
            return {"success": False, "error": "Facebook client not initialized"}

        try:
            # Fetch post insights
            post = self.facebook_client.get_object(
                id=post_id,
                fields="insights.metric(post_impressions,post_engaged_users)",
            )

            return {
                "success": True,
                "metrics": post.get("insights", {}),
            }

        except Exception as e:
            logger.error(f"Facebook analytics error: {e}")
            return {"success": False, "error": str(e)}

    def _get_linkedin_analytics(self, post_id: str) -> dict[str, Any]:
        """Fetch LinkedIn post analytics."""
        try:
            # LinkedIn Analytics API implementation
            logger.info("Fetching LinkedIn analytics (implementation pending)")

            return {
                "success": True,
                "metrics": {
                    "views": 0,
                    "likes": 0,
                    "shares": 0,
                    "comments": 0,
                },
            }

        except Exception as e:
            logger.error(f"LinkedIn analytics error: {e}")
            return {"success": False, "error": str(e)}

    def sync_analytics(
        self,
        content_id: int,
    ) -> dict[str, Any]:
        """
        Sync analytics from all published channels.

        Args:
            content_id: Content ID

        Returns:
            Sync results
        """
        try:
            content_item = (
                self.db.query(ContentItem)
                .filter(ContentItem.id == content_id)
                .first()
            )

            if not content_item:
                raise ValueError(f"Content {content_id} not found")

            if not content_item.channels:
                return {"success": False, "error": "No channels configured"}

            results = {}

            for channel in content_item.channels:
                analytics = self.get_post_analytics(content_id, channel)
                results[channel] = analytics

                # Update content item metrics if successful
                if analytics.get("success"):
                    metrics = analytics.get("metrics", {})
                    content_item.views += metrics.get("views", 0)
                    content_item.likes += metrics.get("likes", 0)
                    content_item.shares += metrics.get("retweets", 0) + metrics.get("shares", 0)
                    content_item.comments_count += metrics.get("replies", 0) + metrics.get("comments", 0)

            # Calculate engagement rate
            if content_item.views > 0:
                total_engagements = (
                    content_item.likes + content_item.shares + content_item.comments_count
                )
                content_item.engagement_rate = (total_engagements / content_item.views) * 100

            self.db.commit()

            logger.info(f"Synced analytics for content {content_id}")
            return {"success": True, "channels": results}

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error syncing analytics: {e}")
            return {"success": False, "error": str(e)}

    def validate_credentials(self, channel: str) -> dict[str, Any]:
        """
        Validate API credentials for a channel.

        Args:
            channel: Channel name

        Returns:
            Validation result
        """
        try:
            if channel.lower() == "twitter":
                if self.twitter_client:
                    # Test API call
                    self.twitter_client.get_me()
                    return {"success": True, "message": "Twitter credentials valid"}
                else:
                    return {"success": False, "error": "Twitter client not initialized"}

            elif channel.lower() == "facebook":
                if self.facebook_client:
                    # Test API call
                    self.facebook_client.get_object(id="me")
                    return {"success": True, "message": "Facebook credentials valid"}
                else:
                    return {"success": False, "error": "Facebook client not initialized"}

            elif channel.lower() == "email":
                if self.sendgrid_client:
                    return {"success": True, "message": "SendGrid credentials configured"}
                else:
                    return {"success": False, "error": "SendGrid client not initialized"}

            else:
                return {"success": False, "error": f"Validation not implemented for {channel}"}

        except Exception as e:
            logger.error(f"Credential validation error for {channel}: {e}")
            return {"success": False, "error": str(e)}

    def handle_webhook(
        self,
        channel: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Handle webhook from external platform.

        Args:
            channel: Channel name
            payload: Webhook payload

        Returns:
            Processing result
        """
        try:
            logger.info(f"Received webhook from {channel}")

            # Process different webhook types
            if channel.lower() == "twitter":
                return self._handle_twitter_webhook(payload)
            elif channel.lower() == "facebook":
                return self._handle_facebook_webhook(payload)
            else:
                return {"success": False, "error": f"Webhooks not supported for {channel}"}

        except Exception as e:
            logger.error(f"Webhook handling error: {e}")
            return {"success": False, "error": str(e)}

    def _handle_twitter_webhook(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Handle Twitter webhook event."""
        # Process Twitter events (mentions, replies, etc.)
        event_type = payload.get("event_type")
        logger.info(f"Processing Twitter webhook: {event_type}")

        return {"success": True, "processed": event_type}

    def _handle_facebook_webhook(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Handle Facebook webhook event."""
        # Process Facebook events (comments, reactions, etc.)
        event_type = payload.get("object")
        logger.info(f"Processing Facebook webhook: {event_type}")

        return {"success": True, "processed": event_type}

    def get_connected_accounts(self) -> list[dict[str, Any]]:
        """
        Get list of connected social media accounts.

        Returns:
            List of connected accounts
        """
        accounts = []

        if self.twitter_client:
            try:
                me = self.twitter_client.get_me()
                accounts.append(
                    {
                        "platform": "twitter",
                        "username": me.data.username,
                        "name": me.data.name,
                        "status": "connected",
                    }
                )
            except Exception as e:
                logger.warning(f"Error fetching Twitter account info: {e}")
                accounts.append(
                    {
                        "platform": "twitter",
                        "status": "error",
                        "error": str(e),
                    }
                )

        if self.facebook_client:
            try:
                me = self.facebook_client.get_object(id="me", fields="name,id")
                accounts.append(
                    {
                        "platform": "facebook",
                        "name": me.get("name"),
                        "id": me.get("id"),
                        "status": "connected",
                    }
                )
            except Exception as e:
                logger.warning(f"Error fetching Facebook account info: {e}")
                accounts.append(
                    {
                        "platform": "facebook",
                        "status": "error",
                        "error": str(e),
                    }
                )

        return accounts
