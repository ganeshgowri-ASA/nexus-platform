"""
Webhook management system with signature validation and retry logic.

This module handles both incoming webhooks (from third-party services)
and outgoing webhooks (to notify external systems) with comprehensive
error handling and retry mechanisms.
"""

from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
import logging
import hashlib
import hmac
import base64
import json
from enum import Enum
import httpx
from sqlalchemy.orm import Session
from sqlalchemy import and_

from .models import (
    Webhook, WebhookDelivery, WebhookStatus, Connection
)

logger = logging.getLogger(__name__)


class SignatureAlgorithm(str, Enum):
    """Supported signature algorithms."""
    SHA256 = "sha256"
    SHA1 = "sha1"
    SHA512 = "sha512"
    MD5 = "md5"


class WebhookError(Exception):
    """Base exception for webhook errors."""
    pass


class SignatureValidationError(WebhookError):
    """Raised when webhook signature validation fails."""
    pass


class WebhookReceiver:
    """
    Handles incoming webhooks from third-party services.

    Validates signatures, processes payloads, and triggers
    appropriate handlers.
    """

    def __init__(self, db: Session):
        """
        Initialize webhook receiver.

        Args:
            db: Database session
        """
        self.db = db
        self._handlers: Dict[str, Callable] = {}

    def register_handler(self, event_type: str, handler: Callable) -> None:
        """
        Register a handler for a specific event type.

        Args:
            event_type: Type of event (e.g., 'user.created')
            handler: Async function to handle the event
        """
        self._handlers[event_type] = handler
        logger.info(f"Registered webhook handler for event: {event_type}")

    async def process_webhook(
        self,
        webhook_id: int,
        payload: Dict[str, Any],
        headers: Dict[str, str],
        raw_body: bytes
    ) -> Dict[str, Any]:
        """
        Process an incoming webhook.

        Args:
            webhook_id: Database ID of the webhook
            payload: Parsed JSON payload
            headers: Request headers
            raw_body: Raw request body for signature validation

        Returns:
            Processing result

        Raises:
            SignatureValidationError: If signature is invalid
            WebhookError: If processing fails
        """
        # Get webhook config
        webhook = self.db.query(Webhook).filter(
            Webhook.id == webhook_id,
            Webhook.is_incoming == True,
            Webhook.is_active == True
        ).first()

        if not webhook:
            raise WebhookError(f"Webhook {webhook_id} not found or inactive")

        # Validate signature
        if webhook.secret:
            self._validate_signature(
                webhook=webhook,
                payload=raw_body,
                headers=headers
            )

        # Determine event type
        event_type = self._extract_event_type(payload, webhook)

        # Check if event is in allowed events
        if webhook.events and event_type not in webhook.events:
            logger.warning(f"Event {event_type} not in webhook allowed events")
            return {
                'status': 'ignored',
                'reason': 'Event type not subscribed'
            }

        # Update webhook stats
        webhook.last_triggered_at = datetime.now()
        webhook.total_deliveries += 1

        # Process event
        try:
            result = await self._process_event(
                event_type=event_type,
                payload=payload,
                webhook=webhook
            )

            webhook.last_success_at = datetime.now()
            webhook.successful_deliveries += 1
            webhook.consecutive_failures = 0

            self.db.commit()

            logger.info(f"Successfully processed webhook {webhook_id}, event: {event_type}")

            return {
                'status': 'success',
                'event_type': event_type,
                'result': result
            }

        except Exception as e:
            logger.error(f"Webhook processing failed: {str(e)}")

            webhook.last_failure_at = datetime.now()
            webhook.last_error_message = str(e)
            webhook.failed_deliveries += 1
            webhook.consecutive_failures += 1

            self.db.commit()

            raise WebhookError(f"Webhook processing failed: {str(e)}")

    def _validate_signature(
        self,
        webhook: Webhook,
        payload: bytes,
        headers: Dict[str, str]
    ) -> None:
        """
        Validate webhook signature.

        Args:
            webhook: Webhook configuration
            payload: Raw payload bytes
            headers: Request headers

        Raises:
            SignatureValidationError: If signature is invalid
        """
        if not webhook.secret:
            return

        # Get signature from headers
        signature_header = webhook.signature_header or 'X-Webhook-Signature'
        received_signature = headers.get(signature_header)

        if not received_signature:
            raise SignatureValidationError(
                f"Signature header {signature_header} not found"
            )

        # Calculate expected signature
        algorithm = webhook.signature_algorithm or 'sha256'
        expected_signature = self._calculate_signature(
            secret=webhook.secret,
            payload=payload,
            algorithm=algorithm
        )

        # Compare signatures (timing-safe comparison)
        if not hmac.compare_digest(received_signature, expected_signature):
            raise SignatureValidationError("Signature validation failed")

    def _calculate_signature(
        self,
        secret: str,
        payload: bytes,
        algorithm: str
    ) -> str:
        """
        Calculate HMAC signature.

        Args:
            secret: Webhook secret
            payload: Payload bytes
            algorithm: Hash algorithm

        Returns:
            Signature string
        """
        # Map algorithm to hashlib function
        hash_func = {
            'sha256': hashlib.sha256,
            'sha1': hashlib.sha1,
            'sha512': hashlib.sha512,
            'md5': hashlib.md5
        }.get(algorithm.lower(), hashlib.sha256)

        # Calculate HMAC
        signature = hmac.new(
            key=secret.encode(),
            msg=payload,
            digestmod=hash_func
        ).hexdigest()

        return signature

    def _extract_event_type(
        self,
        payload: Dict[str, Any],
        webhook: Webhook
    ) -> str:
        """
        Extract event type from payload.

        Args:
            payload: Webhook payload
            webhook: Webhook configuration

        Returns:
            Event type string
        """
        # Try common event type fields
        for field in ['event', 'event_type', 'type', 'action']:
            if field in payload:
                return str(payload[field])

        # Check webhook config for event type path
        if 'event_type_field' in webhook.connection.config:
            field = webhook.connection.config['event_type_field']
            if field in payload:
                return str(payload[field])

        return 'unknown'

    async def _process_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        webhook: Webhook
    ) -> Any:
        """
        Process webhook event.

        Args:
            event_type: Type of event
            payload: Event payload
            webhook: Webhook configuration

        Returns:
            Processing result
        """
        # Call registered handler
        if event_type in self._handlers:
            handler = self._handlers[event_type]
            return await handler(payload, webhook)

        # Default: log and store
        logger.info(f"No handler for event type: {event_type}")
        return {'processed': True}


class WebhookSender:
    """
    Sends webhooks to external systems with retry logic.

    Handles outgoing webhook delivery, retry management,
    and dead letter queuing.
    """

    def __init__(self, db: Session):
        """
        Initialize webhook sender.

        Args:
            db: Database session
        """
        self.db = db

    async def send_webhook(
        self,
        webhook_id: int,
        event_type: str,
        payload: Dict[str, Any],
        retry: bool = True
    ) -> WebhookDelivery:
        """
        Send a webhook to external system.

        Args:
            webhook_id: Database ID of the webhook
            event_type: Type of event
            payload: Event data
            retry: Whether to retry on failure

        Returns:
            WebhookDelivery record

        Raises:
            WebhookError: If webhook not found
        """
        # Get webhook config
        webhook = self.db.query(Webhook).filter(
            Webhook.id == webhook_id,
            Webhook.is_incoming == False,
            Webhook.is_active == True
        ).first()

        if not webhook:
            raise WebhookError(f"Outgoing webhook {webhook_id} not found or inactive")

        # Create delivery record
        delivery = WebhookDelivery(
            webhook_id=webhook_id,
            event_type=event_type,
            payload=payload,
            status=WebhookStatus.PENDING
        )
        self.db.add(delivery)
        self.db.commit()
        self.db.refresh(delivery)

        # Attempt delivery
        try:
            await self._attempt_delivery(webhook, delivery)
        except Exception as e:
            logger.error(f"Webhook delivery failed: {str(e)}")
            if retry and delivery.retry_count < webhook.max_retries:
                # Schedule retry
                delivery.next_retry_at = self._calculate_retry_time(
                    delivery.retry_count,
                    webhook.retry_delay_seconds
                )
                self.db.commit()

        return delivery

    async def _attempt_delivery(
        self,
        webhook: Webhook,
        delivery: WebhookDelivery
    ) -> None:
        """
        Attempt webhook delivery.

        Args:
            webhook: Webhook configuration
            delivery: Delivery record
        """
        delivery.status = WebhookStatus.PENDING
        delivery.attempted_at = datetime.now()

        # Build request
        url = webhook.url
        method = webhook.method or 'POST'
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'NEXUS-Integration-Hub/1.0'
        }

        # Add custom headers
        if webhook.custom_headers:
            headers.update(webhook.custom_headers)

        # Add signature
        payload_bytes = json.dumps(delivery.payload).encode()
        if webhook.secret:
            signature = self._generate_signature(
                secret=webhook.secret,
                payload=payload_bytes,
                algorithm=webhook.signature_algorithm or 'sha256'
            )
            signature_header = webhook.signature_header or 'X-Webhook-Signature'
            headers[signature_header] = signature

        delivery.headers = headers

        # Send request
        start_time = datetime.now()
        timeout = webhook.timeout_seconds or 30

        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method,
                    url=url,
                    json=delivery.payload,
                    headers=headers,
                    timeout=timeout
                )

                # Record response
                delivery.response_status_code = response.status_code
                delivery.response_headers = dict(response.headers)
                delivery.response_body = response.text[:10000]  # Limit size

                end_time = datetime.now()
                delivery.duration_ms = int((end_time - start_time).total_seconds() * 1000)
                delivery.completed_at = end_time

                # Check if successful (2xx status)
                if 200 <= response.status_code < 300:
                    delivery.status = WebhookStatus.DELIVERED

                    # Update webhook stats
                    webhook.last_triggered_at = datetime.now()
                    webhook.last_success_at = datetime.now()
                    webhook.total_deliveries += 1
                    webhook.successful_deliveries += 1
                    webhook.consecutive_failures = 0

                    logger.info(f"Webhook delivered successfully: {webhook.name}")

                else:
                    # Failed delivery
                    delivery.status = WebhookStatus.FAILED
                    delivery.error_message = f"HTTP {response.status_code}: {response.text[:500]}"

                    # Update webhook stats
                    webhook.last_triggered_at = datetime.now()
                    webhook.last_failure_at = datetime.now()
                    webhook.last_error_message = delivery.error_message
                    webhook.total_deliveries += 1
                    webhook.failed_deliveries += 1
                    webhook.consecutive_failures += 1

                self.db.commit()

        except httpx.TimeoutException as e:
            delivery.status = WebhookStatus.FAILED
            delivery.error_message = f"Timeout after {timeout}s"
            delivery.completed_at = datetime.now()

            webhook.last_failure_at = datetime.now()
            webhook.last_error_message = delivery.error_message
            webhook.failed_deliveries += 1
            webhook.consecutive_failures += 1

            self.db.commit()

            raise WebhookError(f"Webhook timeout: {str(e)}")

        except Exception as e:
            delivery.status = WebhookStatus.FAILED
            delivery.error_message = str(e)
            delivery.completed_at = datetime.now()

            webhook.last_failure_at = datetime.now()
            webhook.last_error_message = delivery.error_message
            webhook.failed_deliveries += 1
            webhook.consecutive_failures += 1

            self.db.commit()

            raise WebhookError(f"Webhook delivery error: {str(e)}")

    def _generate_signature(
        self,
        secret: str,
        payload: bytes,
        algorithm: str
    ) -> str:
        """
        Generate webhook signature.

        Args:
            secret: Webhook secret
            payload: Payload bytes
            algorithm: Hash algorithm

        Returns:
            Signature string
        """
        hash_func = {
            'sha256': hashlib.sha256,
            'sha1': hashlib.sha1,
            'sha512': hashlib.sha512,
            'md5': hashlib.md5
        }.get(algorithm.lower(), hashlib.sha256)

        signature = hmac.new(
            key=secret.encode(),
            msg=payload,
            digestmod=hash_func
        ).hexdigest()

        return f"{algorithm}={signature}"

    def _calculate_retry_time(
        self,
        retry_count: int,
        base_delay: int
    ) -> datetime:
        """
        Calculate next retry time with exponential backoff.

        Args:
            retry_count: Number of retries so far
            base_delay: Base delay in seconds

        Returns:
            Next retry datetime
        """
        # Exponential backoff: base_delay * 2^retry_count
        delay = base_delay * (2 ** retry_count)

        # Cap at 1 hour
        delay = min(delay, 3600)

        return datetime.now() + timedelta(seconds=delay)

    async def retry_failed_deliveries(self, max_retries: int = 100) -> int:
        """
        Retry failed webhook deliveries that are due.

        Args:
            max_retries: Maximum number of deliveries to retry

        Returns:
            Number of deliveries retried
        """
        # Find deliveries ready for retry
        now = datetime.now()
        deliveries = self.db.query(WebhookDelivery).join(Webhook).filter(
            and_(
                WebhookDelivery.status.in_([WebhookStatus.FAILED, WebhookStatus.RETRYING]),
                WebhookDelivery.next_retry_at <= now,
                WebhookDelivery.next_retry_at.isnot(None),
                Webhook.is_active == True
            )
        ).limit(max_retries).all()

        retried = 0
        for delivery in deliveries:
            webhook = delivery.webhook

            # Check if max retries exceeded
            if delivery.retry_count >= webhook.max_retries:
                delivery.status = WebhookStatus.FAILED
                delivery.error_message = "Max retries exceeded"
                continue

            # Increment retry count
            delivery.retry_count += 1
            delivery.status = WebhookStatus.RETRYING
            delivery.next_retry_at = None

            self.db.commit()

            # Attempt delivery
            try:
                await self._attempt_delivery(webhook, delivery)
                retried += 1
            except Exception as e:
                logger.error(f"Retry delivery failed: {str(e)}")

                # Schedule next retry if not at max
                if delivery.retry_count < webhook.max_retries:
                    delivery.next_retry_at = self._calculate_retry_time(
                        delivery.retry_count,
                        webhook.retry_delay_seconds
                    )
                else:
                    delivery.status = WebhookStatus.FAILED
                    delivery.error_message = f"Max retries exceeded. Last error: {str(e)}"

                self.db.commit()

        logger.info(f"Retried {retried} failed webhook deliveries")
        return retried

    async def send_batch_webhooks(
        self,
        webhook_id: int,
        events: list[tuple[str, Dict[str, Any]]]
    ) -> list[WebhookDelivery]:
        """
        Send multiple webhook events in batch.

        Args:
            webhook_id: Database ID of the webhook
            events: List of (event_type, payload) tuples

        Returns:
            List of delivery records
        """
        deliveries = []

        for event_type, payload in events:
            try:
                delivery = await self.send_webhook(
                    webhook_id=webhook_id,
                    event_type=event_type,
                    payload=payload,
                    retry=True
                )
                deliveries.append(delivery)
            except Exception as e:
                logger.error(f"Batch webhook failed for event {event_type}: {str(e)}")

        return deliveries


class WebhookManager:
    """
    High-level webhook management.

    Combines receiver and sender functionality with
    additional management features.
    """

    def __init__(self, db: Session):
        """
        Initialize webhook manager.

        Args:
            db: Database session
        """
        self.db = db
        self.receiver = WebhookReceiver(db)
        self.sender = WebhookSender(db)

    def create_webhook(
        self,
        connection_id: int,
        name: str,
        url: str,
        events: list[str],
        is_incoming: bool = False,
        secret: Optional[str] = None,
        **kwargs
    ) -> Webhook:
        """
        Create a new webhook.

        Args:
            connection_id: Connection ID
            name: Webhook name
            url: Webhook URL
            events: List of event types
            is_incoming: True for receiving, False for sending
            secret: Webhook secret for signatures
            **kwargs: Additional webhook configuration

        Returns:
            Created Webhook object
        """
        webhook = Webhook(
            connection_id=connection_id,
            name=name,
            url=url,
            events=events,
            is_incoming=is_incoming,
            secret=secret,
            **kwargs
        )

        self.db.add(webhook)
        self.db.commit()
        self.db.refresh(webhook)

        logger.info(f"Created webhook: {name} ({'incoming' if is_incoming else 'outgoing'})")

        return webhook

    def get_webhook_stats(self, webhook_id: int) -> Dict[str, Any]:
        """
        Get webhook statistics.

        Args:
            webhook_id: Webhook ID

        Returns:
            Statistics dictionary
        """
        webhook = self.db.query(Webhook).filter(
            Webhook.id == webhook_id
        ).first()

        if not webhook:
            return {}

        success_rate = 0.0
        if webhook.total_deliveries > 0:
            success_rate = (webhook.successful_deliveries / webhook.total_deliveries) * 100

        # Get recent deliveries
        recent_deliveries = self.db.query(WebhookDelivery).filter(
            WebhookDelivery.webhook_id == webhook_id
        ).order_by(WebhookDelivery.created_at.desc()).limit(10).all()

        avg_duration = 0
        if recent_deliveries:
            durations = [d.duration_ms for d in recent_deliveries if d.duration_ms]
            if durations:
                avg_duration = sum(durations) / len(durations)

        return {
            'webhook_id': webhook_id,
            'name': webhook.name,
            'is_active': webhook.is_active,
            'total_deliveries': webhook.total_deliveries,
            'successful_deliveries': webhook.successful_deliveries,
            'failed_deliveries': webhook.failed_deliveries,
            'success_rate': success_rate,
            'consecutive_failures': webhook.consecutive_failures,
            'average_duration_ms': avg_duration,
            'last_triggered_at': webhook.last_triggered_at,
            'last_success_at': webhook.last_success_at,
            'last_failure_at': webhook.last_failure_at,
            'last_error_message': webhook.last_error_message
        }

    def delete_webhook(self, webhook_id: int) -> bool:
        """
        Delete a webhook.

        Args:
            webhook_id: Webhook ID

        Returns:
            True if deleted
        """
        webhook = self.db.query(Webhook).filter(
            Webhook.id == webhook_id
        ).first()

        if not webhook:
            return False

        self.db.delete(webhook)
        self.db.commit()

        logger.info(f"Deleted webhook {webhook_id}")
        return True
