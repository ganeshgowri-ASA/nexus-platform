"""
Unsubscribe management service
Handles user preferences and unsubscribe functionality
"""
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from backend.models.preference import NotificationPreference, UnsubscribeToken


class UnsubscribeManager:
    """
    Unsubscribe management service
    Handles notification preferences and one-click unsubscribe
    """

    def __init__(self, token_expiry_days: int = 90):
        """
        Initialize unsubscribe manager

        Args:
            token_expiry_days: Days until unsubscribe tokens expire (default: 90)
        """
        self.token_expiry_days = token_expiry_days

    def create_unsubscribe_token(
        self,
        db: Session,
        user_id: str,
        category: Optional[str] = None,
        channel: Optional[str] = None
    ) -> UnsubscribeToken:
        """
        Create an unsubscribe token

        Args:
            db: Database session
            user_id: User ID
            category: Optional category (None = all categories)
            channel: Optional channel (None = all channels)

        Returns:
            Created UnsubscribeToken
        """
        # Generate secure token
        token = secrets.token_urlsafe(32)

        # Create token record
        unsubscribe_token = UnsubscribeToken(
            token=token,
            user_id=user_id,
            category=category,
            channel=channel,
            expires_at=datetime.utcnow() + timedelta(days=self.token_expiry_days)
        )

        db.add(unsubscribe_token)
        db.commit()
        db.refresh(unsubscribe_token)

        return unsubscribe_token

    def process_unsubscribe(
        self,
        db: Session,
        token: str
    ) -> Dict[str, Any]:
        """
        Process an unsubscribe request using a token

        Args:
            db: Database session
            token: Unsubscribe token

        Returns:
            Dictionary with result
        """
        # Find token
        token_record = db.query(UnsubscribeToken).filter(
            UnsubscribeToken.token == token
        ).first()

        if not token_record:
            return {
                "success": False,
                "error": "Invalid unsubscribe token"
            }

        # Check if already used
        if token_record.used:
            return {
                "success": False,
                "error": "This unsubscribe link has already been used"
            }

        # Check if expired
        if token_record.expires_at and token_record.expires_at < datetime.utcnow():
            return {
                "success": False,
                "error": "This unsubscribe link has expired"
            }

        # Mark token as used
        token_record.used = True
        token_record.used_at = datetime.utcnow()

        # Update preferences
        if token_record.category and token_record.channel:
            # Unsubscribe from specific category and channel
            self.update_preference(
                db,
                token_record.user_id,
                token_record.category,
                token_record.channel,
                enabled=False
            )
        elif token_record.category:
            # Unsubscribe from all channels for this category
            for channel in ["email", "sms", "push", "in_app"]:
                self.update_preference(
                    db,
                    token_record.user_id,
                    token_record.category,
                    channel,
                    enabled=False
                )
        elif token_record.channel:
            # Unsubscribe from this channel for all categories
            # This would need to get all categories and disable them
            pass
        else:
            # Unsubscribe from everything
            db.query(NotificationPreference).filter(
                NotificationPreference.user_id == token_record.user_id
            ).update({"enabled": False})

        db.commit()

        return {
            "success": True,
            "user_id": token_record.user_id,
            "category": token_record.category,
            "channel": token_record.channel,
        }

    def update_preference(
        self,
        db: Session,
        user_id: str,
        category: str,
        channel: str,
        enabled: bool,
        settings: Optional[Dict[str, Any]] = None
    ) -> NotificationPreference:
        """
        Update notification preference

        Args:
            db: Database session
            user_id: User ID
            category: Notification category
            channel: Notification channel
            enabled: Whether to enable this preference
            settings: Additional settings

        Returns:
            NotificationPreference
        """
        # Find or create preference
        preference = db.query(NotificationPreference).filter(
            NotificationPreference.user_id == user_id,
            NotificationPreference.category == category,
            NotificationPreference.channel == channel
        ).first()

        if preference:
            preference.enabled = enabled
            if settings:
                preference.settings = settings
        else:
            preference = NotificationPreference(
                user_id=user_id,
                category=category,
                channel=channel,
                enabled=enabled,
                settings=settings or {}
            )
            db.add(preference)

        db.commit()
        db.refresh(preference)

        return preference

    def get_user_preferences(
        self,
        db: Session,
        user_id: str
    ) -> List[NotificationPreference]:
        """
        Get all preferences for a user

        Args:
            db: Database session
            user_id: User ID

        Returns:
            List of NotificationPreferences
        """
        return db.query(NotificationPreference).filter(
            NotificationPreference.user_id == user_id
        ).all()

    def is_enabled(
        self,
        db: Session,
        user_id: str,
        category: str,
        channel: str
    ) -> bool:
        """
        Check if a user has enabled notifications for a category/channel

        Args:
            db: Database session
            user_id: User ID
            category: Notification category
            channel: Notification channel

        Returns:
            True if enabled, False if disabled or not set (default to True)
        """
        preference = db.query(NotificationPreference).filter(
            NotificationPreference.user_id == user_id,
            NotificationPreference.category == category,
            NotificationPreference.channel == channel
        ).first()

        # If no preference exists, default to enabled
        if not preference:
            return True

        return preference.enabled

    def bulk_update_preferences(
        self,
        db: Session,
        user_id: str,
        preferences: List[Dict[str, Any]]
    ) -> List[NotificationPreference]:
        """
        Update multiple preferences at once

        Args:
            db: Database session
            user_id: User ID
            preferences: List of preference dictionaries with category, channel, enabled

        Returns:
            List of updated preferences
        """
        results = []

        for pref in preferences:
            result = self.update_preference(
                db,
                user_id,
                pref["category"],
                pref["channel"],
                pref["enabled"],
                pref.get("settings")
            )
            results.append(result)

        return results

    def get_unsubscribe_url(
        self,
        db: Session,
        user_id: str,
        category: Optional[str] = None,
        channel: Optional[str] = None,
        base_url: str = "https://nexus.com/unsubscribe"
    ) -> str:
        """
        Generate an unsubscribe URL

        Args:
            db: Database session
            user_id: User ID
            category: Optional category
            channel: Optional channel
            base_url: Base URL for unsubscribe page

        Returns:
            Unsubscribe URL
        """
        token = self.create_unsubscribe_token(db, user_id, category, channel)
        return f"{base_url}?token={token.token}"

    def cleanup_expired_tokens(self, db: Session) -> int:
        """
        Clean up expired unsubscribe tokens

        Args:
            db: Database session

        Returns:
            Number of tokens deleted
        """
        result = db.query(UnsubscribeToken).filter(
            UnsubscribeToken.expires_at < datetime.utcnow()
        ).delete()

        db.commit()
        return result
