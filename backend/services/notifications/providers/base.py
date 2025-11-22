"""
Base notification provider interface
All channel providers must implement this interface
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime


class NotificationResult:
    """Result of a notification send operation"""

    def __init__(
        self,
        success: bool,
        provider_message_id: Optional[str] = None,
        error_message: Optional[str] = None,
        error_code: Optional[str] = None,
        provider_response: Optional[Dict[str, Any]] = None,
        processing_time_ms: Optional[float] = None,
    ):
        self.success = success
        self.provider_message_id = provider_message_id
        self.error_message = error_message
        self.error_code = error_code
        self.provider_response = provider_response or {}
        self.processing_time_ms = processing_time_ms
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "success": self.success,
            "provider_message_id": self.provider_message_id,
            "error_message": self.error_message,
            "error_code": self.error_code,
            "provider_response": self.provider_response,
            "processing_time_ms": self.processing_time_ms,
            "timestamp": self.timestamp.isoformat(),
        }


class BaseNotificationProvider(ABC):
    """
    Abstract base class for notification providers
    Each channel (email, SMS, push, in-app) implements this interface
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize provider with configuration

        Args:
            config: Provider-specific configuration
        """
        self.config = config or {}
        self.provider_name = self.__class__.__name__

    @abstractmethod
    async def send(
        self,
        recipient: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> NotificationResult:
        """
        Send notification through this channel

        Args:
            recipient: Recipient identifier (email, phone, device token, user_id)
            title: Notification title
            message: Notification message body
            data: Additional structured data
            **kwargs: Channel-specific parameters

        Returns:
            NotificationResult with delivery details
        """
        pass

    @abstractmethod
    def validate_recipient(self, recipient: str) -> bool:
        """
        Validate recipient format for this channel

        Args:
            recipient: Recipient identifier to validate

        Returns:
            True if valid, False otherwise
        """
        pass

    def get_provider_name(self) -> str:
        """Get provider name"""
        return self.provider_name

    def is_configured(self) -> bool:
        """
        Check if provider is properly configured

        Returns:
            True if configured, False otherwise
        """
        return bool(self.config)
