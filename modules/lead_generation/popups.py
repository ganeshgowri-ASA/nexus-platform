"""
Popup management for lead generation.

This module provides exit-intent, timed, scroll-triggered popups
with smart targeting capabilities.
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from .lead_types import Popup, PopupCreate
from .models import Popup as PopupModel
from shared.utils import generate_uuid, sanitize_input
from shared.exceptions import ValidationError, NotFoundError, DatabaseError
from config.logging_config import get_logger

logger = get_logger(__name__)


class PopupManager:
    """Popup management service."""

    def __init__(self, db: Session):
        """
        Initialize popup manager.

        Args:
            db: Database session.
        """
        self.db = db

    async def create_popup(self, popup_data: PopupCreate) -> Popup:
        """
        Create a new popup.

        Args:
            popup_data: Popup creation data.

        Returns:
            Created popup object.

        Raises:
            ValidationError: If popup data is invalid.
            DatabaseError: If database operation fails.
        """
        try:
            # Validate trigger type and value
            self._validate_trigger(popup_data.trigger_type, popup_data.trigger_value)

            # Create popup
            popup = PopupModel(
                id=generate_uuid(),
                name=popup_data.name,
                title=sanitize_input(popup_data.title),
                content=sanitize_input(popup_data.content, allow_tags=["b", "i", "br", "p"]),
                form_id=popup_data.form_id,
                trigger_type=popup_data.trigger_type,
                trigger_value=popup_data.trigger_value,
                is_active=popup_data.is_active,
            )

            self.db.add(popup)
            self.db.commit()
            self.db.refresh(popup)

            logger.info(f"Popup created: {popup.name} (ID: {popup.id})")

            return Popup.model_validate(popup)

        except IntegrityError:
            self.db.rollback()
            raise ValidationError(f"Popup with name '{popup_data.name}' already exists")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating popup: {e}")
            raise DatabaseError(f"Failed to create popup: {str(e)}")

    async def get_popup(self, popup_id: str) -> Popup:
        """
        Get popup by ID.

        Args:
            popup_id: Popup ID.

        Returns:
            Popup object.

        Raises:
            NotFoundError: If popup not found.
        """
        popup = self.db.query(PopupModel).filter(PopupModel.id == popup_id).first()
        if not popup:
            raise NotFoundError(f"Popup not found: {popup_id}")

        return Popup.model_validate(popup)

    async def list_popups(
        self,
        skip: int = 0,
        limit: int = 20,
        active_only: bool = False,
    ) -> List[Popup]:
        """
        List all popups.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            active_only: Only return active popups.

        Returns:
            List of popup objects.
        """
        query = self.db.query(PopupModel)

        if active_only:
            query = query.filter(PopupModel.is_active == True)

        popups = query.offset(skip).limit(limit).all()

        return [Popup.model_validate(popup) for popup in popups]

    async def update_popup(self, popup_id: str, updates: dict) -> Popup:
        """
        Update popup.

        Args:
            popup_id: Popup ID.
            updates: Update data.

        Returns:
            Updated popup object.

        Raises:
            NotFoundError: If popup not found.
        """
        popup = self.db.query(PopupModel).filter(PopupModel.id == popup_id).first()
        if not popup:
            raise NotFoundError(f"Popup not found: {popup_id}")

        # Update fields
        for key, value in updates.items():
            if hasattr(popup, key):
                setattr(popup, key, value)

        self.db.commit()
        self.db.refresh(popup)

        logger.info(f"Popup updated: {popup.name} (ID: {popup.id})")

        return Popup.model_validate(popup)

    async def delete_popup(self, popup_id: str) -> None:
        """
        Delete popup.

        Args:
            popup_id: Popup ID.

        Raises:
            NotFoundError: If popup not found.
        """
        popup = self.db.query(PopupModel).filter(PopupModel.id == popup_id).first()
        if not popup:
            raise NotFoundError(f"Popup not found: {popup_id}")

        self.db.delete(popup)
        self.db.commit()

        logger.info(f"Popup deleted: {popup.name} (ID: {popup.id})")

    async def track_view(self, popup_id: str) -> None:
        """
        Track popup view.

        Args:
            popup_id: Popup ID.
        """
        popup = self.db.query(PopupModel).filter(PopupModel.id == popup_id).first()
        if popup:
            popup.views += 1
            self._update_conversion_rate(popup)
            self.db.commit()

    async def track_submission(self, popup_id: str) -> None:
        """
        Track popup submission.

        Args:
            popup_id: Popup ID.
        """
        popup = self.db.query(PopupModel).filter(PopupModel.id == popup_id).first()
        if popup:
            popup.submissions += 1
            self._update_conversion_rate(popup)
            self.db.commit()

    def _validate_trigger(self, trigger_type: str, trigger_value: Optional[str]) -> None:
        """
        Validate trigger configuration.

        Args:
            trigger_type: Trigger type.
            trigger_value: Trigger value.

        Raises:
            ValidationError: If trigger is invalid.
        """
        valid_triggers = ["exit_intent", "scroll", "time", "click"]
        if trigger_type not in valid_triggers:
            raise ValidationError(f"Invalid trigger type. Must be one of: {valid_triggers}")

        if trigger_type in ["scroll", "time"] and not trigger_value:
            raise ValidationError(f"Trigger value required for {trigger_type} trigger")

    def _update_conversion_rate(self, popup: PopupModel) -> None:
        """
        Update conversion rate for popup.

        Args:
            popup: Popup model.
        """
        if popup.views > 0:
            popup.conversion_rate = (popup.submissions / popup.views) * 100


class ExitIntentPopup:
    """Exit-intent popup handler."""

    @staticmethod
    def generate_config(popup: Popup) -> dict:
        """
        Generate exit-intent popup configuration.

        Args:
            popup: Popup object.

        Returns:
            Configuration dictionary.
        """
        return {
            "id": popup.id,
            "trigger": "exit_intent",
            "sensitivity": 20,  # Mouse movement sensitivity
            "delay": 0,  # Show immediately on exit intent
            "title": popup.title,
            "content": popup.content,
            "form_id": popup.form_id,
        }


class ScrollTriggeredPopup:
    """Scroll-triggered popup handler."""

    @staticmethod
    def generate_config(popup: Popup) -> dict:
        """
        Generate scroll-triggered popup configuration.

        Args:
            popup: Popup object.

        Returns:
            Configuration dictionary.
        """
        scroll_percentage = int(popup.trigger_value.rstrip("%")) if popup.trigger_value else 50

        return {
            "id": popup.id,
            "trigger": "scroll",
            "scroll_percentage": scroll_percentage,
            "title": popup.title,
            "content": popup.content,
            "form_id": popup.form_id,
        }


class TimedPopup:
    """Timed popup handler."""

    @staticmethod
    def generate_config(popup: Popup) -> dict:
        """
        Generate timed popup configuration.

        Args:
            popup: Popup object.

        Returns:
            Configuration dictionary.
        """
        delay_seconds = int(popup.trigger_value.rstrip("s")) if popup.trigger_value else 10

        return {
            "id": popup.id,
            "trigger": "time",
            "delay_seconds": delay_seconds,
            "title": popup.title,
            "content": popup.content,
            "form_id": popup.form_id,
        }


class SmartPopupTargeting:
    """Smart popup targeting based on user behavior."""

    @staticmethod
    def should_show_popup(
        popup: Popup,
        user_context: dict,
    ) -> bool:
        """
        Determine if popup should be shown to user.

        Args:
            popup: Popup object.
            user_context: User context data (visits, source, etc.).

        Returns:
            True if popup should be shown.
        """
        # Check if popup is active
        if not popup.is_active:
            return False

        # Check visit count (don't annoy returning visitors)
        visit_count = user_context.get("visit_count", 0)
        if visit_count > 3:
            return False

        # Check if user has already seen this popup
        seen_popups = user_context.get("seen_popups", [])
        if popup.id in seen_popups:
            return False

        # Check traffic source targeting
        source = user_context.get("source", "direct")
        # Add more sophisticated targeting logic here

        return True
