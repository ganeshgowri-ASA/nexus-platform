"""
Social Media Module - Multi-Platform Post Composer.

This module provides functionality for creating posts with platform-specific
customization, media handling, and content optimization.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from .platforms import BasePlatform, PlatformFactory
from .social_types import (
    Media,
    MediaType,
    PlatformCredentials,
    PlatformType,
    Post,
    PostContent,
    PostStatus,
)

logger = logging.getLogger(__name__)


class ComposerError(Exception):
    """Base exception for composer errors."""

    pass


class ValidationError(ComposerError):
    """Content validation failed."""

    pass


class PostComposer:
    """Multi-platform post composer with customization and preview."""

    # Platform-specific character limits
    PLATFORM_LIMITS = {
        PlatformType.FACEBOOK: 63206,
        PlatformType.TWITTER: 280,
        PlatformType.LINKEDIN: 3000,
        PlatformType.INSTAGRAM: 2200,
        PlatformType.TIKTOK: 2200,
        PlatformType.YOUTUBE: 5000,  # Description
        PlatformType.PINTEREST: 500,
    }

    # Platform-specific media limits
    PLATFORM_MEDIA_LIMITS = {
        PlatformType.FACEBOOK: {"images": 10, "videos": 1},
        PlatformType.TWITTER: {"images": 4, "videos": 1},
        PlatformType.LINKEDIN: {"images": 9, "videos": 1},
        PlatformType.INSTAGRAM: {"images": 10, "videos": 1},
        PlatformType.TIKTOK: {"images": 0, "videos": 1},
        PlatformType.YOUTUBE: {"images": 0, "videos": 1},
        PlatformType.PINTEREST: {"images": 1, "videos": 1},
    }

    def __init__(self):
        """Initialize post composer."""
        self._drafts: Dict[UUID, Post] = {}

    def create_post(
        self,
        title: str,
        platforms: List[PlatformType],
        author_id: UUID,
        base_content: str = "",
        campaign_id: Optional[UUID] = None,
    ) -> Post:
        """
        Create a new post draft.

        Args:
            title: Post title
            platforms: Target platforms
            author_id: Post author UUID
            base_content: Base text content (can be customized per platform)
            campaign_id: Optional campaign UUID

        Returns:
            New Post object
        """
        post = Post(
            id=uuid4(),
            title=title,
            platforms=platforms,
            author_id=author_id,
            campaign_id=campaign_id,
            status=PostStatus.DRAFT,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Initialize content for each platform
        for platform in platforms:
            post.content_by_platform[platform] = PostContent(
                platform=platform, text=base_content
            )

        self._drafts[post.id] = post
        logger.info(f"Created post draft {post.id} for platforms {platforms}")
        return post

    def update_content(
        self,
        post_id: UUID,
        platform: PlatformType,
        text: Optional[str] = None,
        media: Optional[List[Media]] = None,
        hashtags: Optional[List[str]] = None,
        mentions: Optional[List[str]] = None,
        location: Optional[str] = None,
        link: Optional[str] = None,
        custom_fields: Optional[Dict[str, Any]] = None,
    ) -> Post:
        """
        Update content for a specific platform.

        Args:
            post_id: Post UUID
            platform: Target platform
            text: Post text content
            media: Media attachments
            hashtags: Hashtags to include
            mentions: User mentions
            location: Location tag
            link: URL to include
            custom_fields: Platform-specific fields

        Returns:
            Updated Post object

        Raises:
            ValueError: If post not found or platform not in post
            ValidationError: If content validation fails
        """
        if post_id not in self._drafts:
            raise ValueError(f"Post {post_id} not found")

        post = self._drafts[post_id]
        if platform not in post.platforms:
            raise ValueError(f"Platform {platform} not configured for post {post_id}")

        content = post.content_by_platform[platform]

        # Update fields if provided
        if text is not None:
            content.text = text
        if media is not None:
            content.media = media
        if hashtags is not None:
            content.hashtags = hashtags
        if mentions is not None:
            content.mentions = mentions
        if location is not None:
            content.location = location
        if link is not None:
            content.link = link
        if custom_fields is not None:
            content.custom_fields.update(custom_fields)

        # Validate content
        self._validate_content(platform, content)

        post.updated_at = datetime.utcnow()
        logger.info(f"Updated content for post {post_id} on platform {platform}")
        return post

    def add_media(
        self, post_id: UUID, platform: PlatformType, media: Media
    ) -> Post:
        """
        Add media to a post for a specific platform.

        Args:
            post_id: Post UUID
            platform: Target platform
            media: Media object to add

        Returns:
            Updated Post object

        Raises:
            ValueError: If post not found or media limit exceeded
        """
        if post_id not in self._drafts:
            raise ValueError(f"Post {post_id} not found")

        post = self._drafts[post_id]
        content = post.content_by_platform[platform]

        # Check media limits
        limits = self.PLATFORM_MEDIA_LIMITS.get(platform, {})
        current_images = sum(
            1 for m in content.media if m.media_type == MediaType.IMAGE
        )
        current_videos = sum(
            1 for m in content.media if m.media_type == MediaType.VIDEO
        )

        if media.media_type == MediaType.IMAGE:
            if current_images >= limits.get("images", 10):
                raise ValueError(
                    f"Image limit exceeded for {platform.value} ({limits['images']} max)"
                )
        elif media.media_type == MediaType.VIDEO:
            if current_videos >= limits.get("videos", 1):
                raise ValueError(
                    f"Video limit exceeded for {platform.value} ({limits['videos']} max)"
                )

        content.media.append(media)
        post.updated_at = datetime.utcnow()
        logger.info(
            f"Added {media.media_type.value} to post {post_id} for platform {platform}"
        )
        return post

    def remove_media(
        self, post_id: UUID, platform: PlatformType, media_id: UUID
    ) -> Post:
        """
        Remove media from a post.

        Args:
            post_id: Post UUID
            platform: Target platform
            media_id: Media UUID to remove

        Returns:
            Updated Post object
        """
        if post_id not in self._drafts:
            raise ValueError(f"Post {post_id} not found")

        post = self._drafts[post_id]
        content = post.content_by_platform[platform]
        content.media = [m for m in content.media if m.id != media_id]

        post.updated_at = datetime.utcnow()
        logger.info(f"Removed media {media_id} from post {post_id}")
        return post

    def optimize_hashtags(
        self, post_id: UUID, platform: PlatformType, hashtags: List[str]
    ) -> List[str]:
        """
        Optimize hashtags for a specific platform.

        Args:
            post_id: Post UUID
            platform: Target platform
            hashtags: List of hashtags

        Returns:
            Optimized hashtag list
        """
        # Platform-specific hashtag limits
        max_hashtags = {
            PlatformType.INSTAGRAM: 30,
            PlatformType.TWITTER: 2,  # Recommended
            PlatformType.LINKEDIN: 3,  # Recommended
            PlatformType.TIKTOK: 30,
            PlatformType.FACEBOOK: 10,  # Recommended
        }.get(platform, 10)

        # Remove duplicates and limit count
        optimized = list(dict.fromkeys(hashtags))[:max_hashtags]

        # Ensure hashtags start with #
        optimized = [
            tag if tag.startswith("#") else f"#{tag}" for tag in optimized
        ]

        logger.info(
            f"Optimized hashtags for {platform.value}: {len(hashtags)} -> {len(optimized)}"
        )
        return optimized

    def generate_preview(self, post_id: UUID, platform: PlatformType) -> Dict[str, Any]:
        """
        Generate a preview of how the post will appear on the platform.

        Args:
            post_id: Post UUID
            platform: Target platform

        Returns:
            Dictionary with preview data
        """
        if post_id not in self._drafts:
            raise ValueError(f"Post {post_id} not found")

        post = self._drafts[post_id]
        content = post.content_by_platform[platform]

        # Build preview text
        preview_text = content.text
        if content.hashtags:
            hashtags_text = " ".join(content.hashtags)
            preview_text = f"{preview_text}\n\n{hashtags_text}"

        char_limit = self.PLATFORM_LIMITS.get(platform, 5000)
        is_within_limit = len(preview_text) <= char_limit

        preview = {
            "platform": platform.value,
            "text": preview_text,
            "character_count": len(preview_text),
            "character_limit": char_limit,
            "within_limit": is_within_limit,
            "media_count": len(content.media),
            "media_types": [m.media_type.value for m in content.media],
            "hashtag_count": len(content.hashtags),
            "mention_count": len(content.mentions),
            "has_link": content.link is not None,
            "has_location": content.location is not None,
            "warnings": [],
        }

        # Add warnings
        if not is_within_limit:
            preview["warnings"].append(
                f"Text exceeds {platform.value} character limit by {len(preview_text) - char_limit} characters"
            )

        if platform == PlatformType.TWITTER and len(content.hashtags) > 2:
            preview["warnings"].append(
                "Twitter recommends 1-2 hashtags for optimal engagement"
            )

        if platform in [PlatformType.TIKTOK, PlatformType.YOUTUBE] and not content.media:
            preview["warnings"].append(
                f"{platform.value} requires video content"
            )

        return preview

    def validate_post(self, post_id: UUID) -> Dict[str, Any]:
        """
        Validate post for all platforms.

        Args:
            post_id: Post UUID

        Returns:
            Dictionary with validation results per platform
        """
        if post_id not in self._drafts:
            raise ValueError(f"Post {post_id} not found")

        post = self._drafts[post_id]
        results = {}

        for platform in post.platforms:
            content = post.content_by_platform[platform]
            try:
                self._validate_content(platform, content)
                results[platform.value] = {
                    "valid": True,
                    "errors": [],
                    "warnings": [],
                }
            except ValidationError as e:
                results[platform.value] = {
                    "valid": False,
                    "errors": [str(e)],
                    "warnings": [],
                }

        return results

    def get_post(self, post_id: UUID) -> Optional[Post]:
        """
        Get a post by ID.

        Args:
            post_id: Post UUID

        Returns:
            Post object or None if not found
        """
        return self._drafts.get(post_id)

    def list_drafts(self) -> List[Post]:
        """
        List all draft posts.

        Returns:
            List of draft Post objects
        """
        return list(self._drafts.values())

    def delete_draft(self, post_id: UUID) -> bool:
        """
        Delete a draft post.

        Args:
            post_id: Post UUID

        Returns:
            True if deleted, False if not found
        """
        if post_id in self._drafts:
            del self._drafts[post_id]
            logger.info(f"Deleted draft post {post_id}")
            return True
        return False

    def _validate_content(self, platform: PlatformType, content: PostContent) -> None:
        """
        Validate content for a specific platform.

        Args:
            platform: Platform to validate for
            content: Content to validate

        Raises:
            ValidationError: If validation fails
        """
        # Check character limit
        char_limit = self.PLATFORM_LIMITS.get(platform, 5000)
        full_text = content.text
        if content.hashtags:
            full_text += " " + " ".join(content.hashtags)

        if len(full_text) > char_limit:
            raise ValidationError(
                f"Text exceeds {platform.value} limit: {len(full_text)}/{char_limit}"
            )

        # Check media requirements
        if platform in [PlatformType.TIKTOK, PlatformType.YOUTUBE]:
            if not content.media or not any(
                m.media_type == MediaType.VIDEO for m in content.media
            ):
                raise ValidationError(f"{platform.value} requires video content")

        # Check media limits
        limits = self.PLATFORM_MEDIA_LIMITS.get(platform, {})
        image_count = sum(1 for m in content.media if m.media_type == MediaType.IMAGE)
        video_count = sum(1 for m in content.media if m.media_type == MediaType.VIDEO)

        if image_count > limits.get("images", 10):
            raise ValidationError(
                f"Too many images for {platform.value}: {image_count}/{limits['images']}"
            )
        if video_count > limits.get("videos", 1):
            raise ValidationError(
                f"Too many videos for {platform.value}: {video_count}/{limits['videos']}"
            )

    def duplicate_post(self, post_id: UUID, new_title: str) -> Post:
        """
        Duplicate an existing post.

        Args:
            post_id: Post UUID to duplicate
            new_title: Title for the new post

        Returns:
            New Post object

        Raises:
            ValueError: If post not found
        """
        if post_id not in self._drafts:
            raise ValueError(f"Post {post_id} not found")

        original = self._drafts[post_id]
        new_post = Post(
            id=uuid4(),
            title=new_title,
            platforms=original.platforms.copy(),
            author_id=original.author_id,
            campaign_id=original.campaign_id,
            status=PostStatus.DRAFT,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Copy content for each platform
        for platform, content in original.content_by_platform.items():
            new_post.content_by_platform[platform] = PostContent(
                platform=platform,
                text=content.text,
                media=content.media.copy(),
                hashtags=content.hashtags.copy(),
                mentions=content.mentions.copy(),
                location=content.location,
                link=content.link,
                custom_fields=content.custom_fields.copy(),
            )

        self._drafts[new_post.id] = new_post
        logger.info(f"Duplicated post {post_id} to {new_post.id}")
        return new_post
