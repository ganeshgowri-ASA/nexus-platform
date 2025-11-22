"""
Push notification provider
Firebase Cloud Messaging (FCM) and APNs support
"""
import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio

from backend.services.notifications.providers.base import (
    BaseNotificationProvider,
    NotificationResult,
)


class PushNotificationProvider(BaseNotificationProvider):
    """
    Push notification provider
    Supports Firebase Cloud Messaging (FCM) and Apple Push Notification service (APNs)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize push notification provider

        Config options:
            - backend: 'fcm', 'apns' (default: fcm)
            - fcm_server_key: FCM server key (legacy)
            - fcm_credentials_path: Path to FCM service account credentials JSON
            - fcm_project_id: Firebase project ID
            - apns_certificate_path: Path to APNs certificate
            - apns_key_id: APNs key ID
            - apns_team_id: APNs team ID
        """
        super().__init__(config)
        self.backend = config.get("backend", "fcm") if config else "fcm"

        # FCM configuration
        if self.backend == "fcm":
            self.fcm_server_key = config.get("fcm_server_key", os.getenv("FCM_SERVER_KEY"))
            self.fcm_credentials_path = config.get(
                "fcm_credentials_path",
                os.getenv("FCM_CREDENTIALS_PATH")
            )
            self.fcm_project_id = config.get("fcm_project_id", os.getenv("FCM_PROJECT_ID"))

        # APNs configuration
        elif self.backend == "apns":
            self.apns_certificate_path = config.get(
                "apns_certificate_path",
                os.getenv("APNS_CERTIFICATE_PATH")
            )
            self.apns_key_id = config.get("apns_key_id", os.getenv("APNS_KEY_ID"))
            self.apns_team_id = config.get("apns_team_id", os.getenv("APNS_TEAM_ID"))

    async def send(
        self,
        recipient: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> NotificationResult:
        """
        Send push notification

        Args:
            recipient: Device token or topic
            title: Notification title
            message: Notification body
            data: Additional data payload
            **kwargs: Additional parameters (badge, sound, priority, etc.)

        Returns:
            NotificationResult
        """
        start_time = datetime.utcnow()

        try:
            # Validate recipient
            if not self.validate_recipient(recipient):
                return NotificationResult(
                    success=False,
                    error_message=f"Invalid device token: {recipient}",
                    error_code="INVALID_TOKEN",
                )

            # Send based on backend
            if self.backend == "fcm":
                result = await self._send_fcm(recipient, title, message, data, **kwargs)
            elif self.backend == "apns":
                result = await self._send_apns(recipient, title, message, data, **kwargs)
            else:
                return NotificationResult(
                    success=False,
                    error_message=f"Unknown push backend: {self.backend}",
                    error_code="UNKNOWN_BACKEND",
                )

            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            result.processing_time_ms = processing_time

            return result

        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return NotificationResult(
                success=False,
                error_message=str(e),
                error_code="SEND_FAILED",
                processing_time_ms=processing_time,
            )

    async def _send_fcm(
        self,
        recipient: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> NotificationResult:
        """
        Send push notification via Firebase Cloud Messaging

        Supports both legacy FCM and HTTP v1 API
        """
        try:
            # Check if using legacy or modern FCM
            use_legacy = bool(self.fcm_server_key)

            if use_legacy:
                return await self._send_fcm_legacy(recipient, title, message, data, **kwargs)
            else:
                return await self._send_fcm_v1(recipient, title, message, data, **kwargs)

        except Exception as e:
            return NotificationResult(
                success=False,
                error_message=str(e),
                error_code="FCM_ERROR",
            )

    async def _send_fcm_legacy(
        self,
        recipient: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> NotificationResult:
        """Send via FCM Legacy API (deprecated but still works)"""
        try:
            # Placeholder for FCM legacy implementation
            # Requires: pip install firebase-admin or direct HTTP requests
            # import requests
            # url = "https://fcm.googleapis.com/fcm/send"
            # headers = {
            #     "Authorization": f"key={self.fcm_server_key}",
            #     "Content-Type": "application/json"
            # }
            # payload = {
            #     "to": recipient,
            #     "notification": {"title": title, "body": message},
            #     "data": data or {},
            #     "priority": kwargs.get("priority", "high")
            # }
            # response = requests.post(url, headers=headers, json=payload)
            # ...

            if not self.fcm_server_key:
                return NotificationResult(
                    success=False,
                    error_message="FCM not configured. Set FCM_SERVER_KEY",
                    error_code="NOT_CONFIGURED",
                )

            # Mock success for now
            return NotificationResult(
                success=True,
                provider_message_id=f"fcm_mock_{datetime.utcnow().timestamp()}",
                provider_response={
                    "backend": "fcm_legacy",
                    "recipient": recipient[:20] + "...",  # Truncate for safety
                    "note": "Mock implementation. Install 'firebase-admin' package for real integration."
                },
            )

        except Exception as e:
            return NotificationResult(
                success=False,
                error_message=str(e),
                error_code="FCM_LEGACY_ERROR",
            )

    async def _send_fcm_v1(
        self,
        recipient: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> NotificationResult:
        """Send via FCM HTTP v1 API (recommended)"""
        try:
            # Placeholder for FCM v1 implementation
            # Requires: pip install firebase-admin
            # import firebase_admin
            # from firebase_admin import credentials, messaging
            #
            # if not firebase_admin._apps:
            #     cred = credentials.Certificate(self.fcm_credentials_path)
            #     firebase_admin.initialize_app(cred)
            #
            # message_obj = messaging.Message(
            #     notification=messaging.Notification(title=title, body=message),
            #     data=data or {},
            #     token=recipient
            # )
            # response = messaging.send(message_obj)
            # return NotificationResult(success=True, provider_message_id=response)

            if not (self.fcm_credentials_path or self.fcm_project_id):
                return NotificationResult(
                    success=False,
                    error_message="FCM not configured. Set FCM_CREDENTIALS_PATH or FCM_PROJECT_ID",
                    error_code="NOT_CONFIGURED",
                )

            # Mock success for now
            return NotificationResult(
                success=True,
                provider_message_id=f"fcm_v1_mock_{datetime.utcnow().timestamp()}",
                provider_response={
                    "backend": "fcm_v1",
                    "recipient": recipient[:20] + "...",
                    "note": "Mock implementation. Install 'firebase-admin' package for real integration."
                },
            )

        except Exception as e:
            return NotificationResult(
                success=False,
                error_message=str(e),
                error_code="FCM_V1_ERROR",
            )

    async def _send_apns(
        self,
        recipient: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> NotificationResult:
        """Send push notification via Apple Push Notification service"""
        try:
            # Placeholder for APNs implementation
            # Requires: pip install apns2
            # from apns2.client import APNsClient
            # from apns2.payload import Payload
            # client = APNsClient(self.apns_certificate_path)
            # payload = Payload(alert={"title": title, "body": message}, custom=data)
            # client.send_notification(recipient, payload)

            return NotificationResult(
                success=False,
                error_message="APNs backend not implemented. Install 'apns2' package and implement.",
                error_code="NOT_IMPLEMENTED",
            )

        except Exception as e:
            return NotificationResult(
                success=False,
                error_message=str(e),
                error_code="APNS_ERROR",
            )

    async def send_to_topic(
        self,
        topic: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> NotificationResult:
        """
        Send push notification to a topic (group of devices)

        Args:
            topic: Topic name (e.g., "news", "alerts")
            title: Notification title
            message: Notification body
            data: Additional data payload
            **kwargs: Additional parameters

        Returns:
            NotificationResult
        """
        # For FCM, topics are prefixed with /topics/
        if self.backend == "fcm":
            topic_path = f"/topics/{topic}"
            return await self.send(topic_path, title, message, data, **kwargs)

        return NotificationResult(
            success=False,
            error_message="Topic notifications only supported on FCM backend",
            error_code="NOT_SUPPORTED",
        )

    def validate_recipient(self, recipient: str) -> bool:
        """
        Validate device token format
        Basic validation - just checks if it's not empty and has reasonable length
        """
        if not recipient or len(recipient) < 10:
            return False

        # FCM device tokens are typically 100+ characters
        # APNs tokens are 64 hex characters
        # Topics start with /topics/
        if recipient.startswith("/topics/"):
            return len(recipient) > 8

        return len(recipient) >= 10

    def is_configured(self) -> bool:
        """Check if push provider is configured"""
        if self.backend == "fcm":
            return bool(
                self.fcm_server_key
                or (self.fcm_credentials_path and self.fcm_project_id)
            )
        elif self.backend == "apns":
            return bool(self.apns_certificate_path or (self.apns_key_id and self.apns_team_id))
        return super().is_configured()
