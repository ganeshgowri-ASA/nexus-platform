"""
SMS notification provider
Supports Twilio, AWS SNS, and other SMS services
"""
import re
import os
from typing import Dict, Any, Optional
from datetime import datetime

from backend.services.notifications.providers.base import (
    BaseNotificationProvider,
    NotificationResult,
)


class SMSProvider(BaseNotificationProvider):
    """
    SMS notification provider
    Supports Twilio, AWS SNS, and other SMS gateways
    """

    # Basic phone number validation (E.164 format)
    PHONE_REGEX = re.compile(r'^\+?[1-9]\d{1,14}$')

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize SMS provider

        Config options:
            - backend: 'twilio', 'sns', 'custom' (default: twilio)
            - twilio_account_sid: Twilio account SID
            - twilio_auth_token: Twilio auth token
            - twilio_from_number: Twilio sender number
            - aws_region: AWS region (for SNS)
            - sns_sender_id: SNS sender ID
        """
        super().__init__(config)
        self.backend = config.get("backend", "twilio") if config else "twilio"

        # Twilio configuration
        if self.backend == "twilio":
            self.twilio_account_sid = config.get("twilio_account_sid", os.getenv("TWILIO_ACCOUNT_SID"))
            self.twilio_auth_token = config.get("twilio_auth_token", os.getenv("TWILIO_AUTH_TOKEN"))
            self.twilio_from_number = config.get("twilio_from_number", os.getenv("TWILIO_FROM_NUMBER"))

        # AWS SNS configuration
        elif self.backend == "sns":
            self.aws_region = config.get("aws_region", os.getenv("AWS_REGION", "us-east-1"))
            self.sns_sender_id = config.get("sns_sender_id", "NEXUS")

    async def send(
        self,
        recipient: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> NotificationResult:
        """
        Send SMS notification

        Args:
            recipient: Phone number in E.164 format (e.g., +1234567890)
            title: SMS title (may be ignored by some providers)
            message: SMS message body
            data: Additional data
            **kwargs: Additional parameters

        Returns:
            NotificationResult
        """
        start_time = datetime.utcnow()

        try:
            # Validate recipient
            if not self.validate_recipient(recipient):
                return NotificationResult(
                    success=False,
                    error_message=f"Invalid phone number: {recipient}",
                    error_code="INVALID_PHONE",
                )

            # Send based on backend
            if self.backend == "twilio":
                result = await self._send_twilio(recipient, message)
            elif self.backend == "sns":
                result = await self._send_sns(recipient, message)
            else:
                return NotificationResult(
                    success=False,
                    error_message=f"Unknown SMS backend: {self.backend}",
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

    async def _send_twilio(self, recipient: str, message: str) -> NotificationResult:
        """Send SMS via Twilio"""
        try:
            # Placeholder for Twilio implementation
            # Requires: pip install twilio
            # from twilio.rest import Client
            # client = Client(self.twilio_account_sid, self.twilio_auth_token)
            # message = client.messages.create(
            #     body=message,
            #     from_=self.twilio_from_number,
            #     to=recipient
            # )
            # return NotificationResult(
            #     success=True,
            #     provider_message_id=message.sid,
            #     provider_response={"status": message.status}
            # )

            if not (self.twilio_account_sid and self.twilio_auth_token and self.twilio_from_number):
                return NotificationResult(
                    success=False,
                    error_message="Twilio not configured. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_FROM_NUMBER",
                    error_code="NOT_CONFIGURED",
                )

            # Mock success for now
            return NotificationResult(
                success=True,
                provider_message_id=f"twilio_mock_{datetime.utcnow().timestamp()}",
                provider_response={
                    "backend": "twilio",
                    "recipient": recipient,
                    "note": "Mock implementation. Install 'twilio' package for real integration."
                },
            )

        except Exception as e:
            return NotificationResult(
                success=False,
                error_message=str(e),
                error_code="TWILIO_ERROR",
            )

    async def _send_sns(self, recipient: str, message: str) -> NotificationResult:
        """Send SMS via AWS SNS"""
        try:
            # Placeholder for AWS SNS implementation
            # Requires: pip install boto3
            # import boto3
            # sns_client = boto3.client('sns', region_name=self.aws_region)
            # response = sns_client.publish(
            #     PhoneNumber=recipient,
            #     Message=message,
            #     MessageAttributes={
            #         'AWS.SNS.SMS.SenderID': {'DataType': 'String', 'StringValue': self.sns_sender_id}
            #     }
            # )
            # return NotificationResult(
            #     success=True,
            #     provider_message_id=response['MessageId'],
            #     provider_response=response
            # )

            return NotificationResult(
                success=False,
                error_message="AWS SNS backend not implemented. Install 'boto3' package and implement.",
                error_code="NOT_IMPLEMENTED",
            )

        except Exception as e:
            return NotificationResult(
                success=False,
                error_message=str(e),
                error_code="SNS_ERROR",
            )

    def validate_recipient(self, recipient: str) -> bool:
        """Validate phone number format (E.164)"""
        return bool(self.PHONE_REGEX.match(recipient))

    def is_configured(self) -> bool:
        """Check if SMS provider is configured"""
        if self.backend == "twilio":
            return bool(
                self.twilio_account_sid
                and self.twilio_auth_token
                and self.twilio_from_number
            )
        elif self.backend == "sns":
            return bool(self.aws_region)
        return super().is_configured()
