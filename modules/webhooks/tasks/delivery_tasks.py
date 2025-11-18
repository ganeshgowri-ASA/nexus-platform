"""Celery tasks for webhook delivery"""

import httpx
import logging
from typing import Dict, Any
from datetime import datetime
from .celery_app import celery_app
from modules.webhooks.models.base import SessionLocal
from modules.webhooks.models.webhook_delivery import DeliveryStatus
from modules.webhooks.services import DeliveryService, SignatureService
from modules.webhooks.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@celery_app.task(bind=True, max_retries=None)
def send_webhook(self, delivery_id: int):
    """
    Send webhook delivery to endpoint

    Args:
        delivery_id: ID of the webhook delivery
    """
    db = SessionLocal()
    try:
        # Get delivery and webhook
        delivery = DeliveryService.get_delivery(db, delivery_id)
        if not delivery:
            logger.error(f"Delivery {delivery_id} not found")
            return

        webhook = delivery.webhook
        if not webhook or not webhook.is_active:
            logger.warning(f"Webhook {delivery.webhook_id} is inactive or not found")
            DeliveryService.update_delivery_status(
                db, delivery_id, DeliveryStatus.FAILED,
                error_message="Webhook is inactive or not found"
            )
            return

        # Check if max attempts reached
        if delivery.attempt_count >= delivery.max_attempts:
            logger.warning(f"Delivery {delivery_id} exceeded max attempts")
            DeliveryService.update_delivery_status(
                db, delivery_id, DeliveryStatus.FAILED,
                error_message="Max retry attempts exceeded"
            )
            return

        # Generate signature
        signature_headers = SignatureService.create_signature_header(
            delivery.payload,
            webhook.secret
        )

        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "NEXUS-Webhooks/1.0",
            **signature_headers,
            **(webhook.headers or {})
        }

        # Update status to sending
        DeliveryService.update_delivery_status(db, delivery_id, DeliveryStatus.SENDING)

        # Store request details
        delivery.request_url = webhook.url
        delivery.request_headers = headers
        db.commit()

        # Send HTTP request
        try:
            with httpx.Client(timeout=webhook.timeout) as client:
                response = client.post(
                    webhook.url,
                    json=delivery.payload,
                    headers=headers
                )

                # Check if successful (2xx status code)
                if 200 <= response.status_code < 300:
                    DeliveryService.update_delivery_status(
                        db, delivery_id, DeliveryStatus.SUCCESS,
                        status_code=response.status_code,
                        response_body=response.text[:10000],  # Limit response body size
                        response_headers=dict(response.headers)
                    )
                    logger.info(f"Delivery {delivery_id} sent successfully")
                else:
                    # Handle non-2xx status codes
                    handle_delivery_failure(
                        db, delivery_id, delivery.attempt_count,
                        status_code=response.status_code,
                        response_body=response.text[:10000],
                        response_headers=dict(response.headers),
                        error_message=f"HTTP {response.status_code}"
                    )

        except httpx.TimeoutException as e:
            handle_delivery_failure(
                db, delivery_id, delivery.attempt_count,
                error_message=f"Timeout: {str(e)}"
            )
        except httpx.RequestError as e:
            handle_delivery_failure(
                db, delivery_id, delivery.attempt_count,
                error_message=f"Request error: {str(e)}"
            )
        except Exception as e:
            handle_delivery_failure(
                db, delivery_id, delivery.attempt_count,
                error_message=f"Unexpected error: {str(e)}"
            )

    except Exception as e:
        logger.error(f"Error processing delivery {delivery_id}: {str(e)}", exc_info=True)
    finally:
        db.close()


def handle_delivery_failure(
    db,
    delivery_id: int,
    current_attempt: int,
    status_code: int = None,
    response_body: str = None,
    response_headers: Dict[str, Any] = None,
    error_message: str = None
):
    """Handle delivery failure and schedule retry if needed"""
    delivery = DeliveryService.get_delivery(db, delivery_id)
    if not delivery:
        return

    if current_attempt + 1 >= delivery.max_attempts:
        # Max retries reached
        DeliveryService.update_delivery_status(
            db, delivery_id, DeliveryStatus.FAILED,
            status_code=status_code,
            response_body=response_body,
            response_headers=response_headers,
            error_message=error_message or "Max retry attempts exceeded"
        )
        logger.warning(f"Delivery {delivery_id} failed after {current_attempt + 1} attempts")
    else:
        # Schedule retry with exponential backoff
        retry_delay = settings.INITIAL_RETRY_DELAY * (settings.RETRY_BACKOFF_FACTOR ** current_attempt)
        DeliveryService.increment_attempt(db, delivery_id, int(retry_delay))

        # Update error information
        DeliveryService.update_delivery_status(
            db, delivery_id, DeliveryStatus.RETRYING,
            status_code=status_code,
            response_body=response_body,
            response_headers=response_headers,
            error_message=error_message
        )

        logger.info(f"Delivery {delivery_id} scheduled for retry in {retry_delay}s (attempt {current_attempt + 1})")


@celery_app.task
def retry_failed_webhooks():
    """Periodic task to retry failed webhook deliveries"""
    db = SessionLocal()
    try:
        pending_retries = DeliveryService.get_pending_retries(db)
        logger.info(f"Found {len(pending_retries)} webhooks to retry")

        for delivery in pending_retries:
            send_webhook.delay(delivery.id)

    except Exception as e:
        logger.error(f"Error in retry_failed_webhooks: {str(e)}", exc_info=True)
    finally:
        db.close()


@celery_app.task
def cleanup_old_deliveries():
    """Periodic task to cleanup old delivery logs"""
    db = SessionLocal()
    try:
        deleted_count = DeliveryService.cleanup_old_deliveries(
            db,
            days=settings.LOG_RETENTION_DAYS
        )
        logger.info(f"Cleaned up {deleted_count} old delivery logs")
    except Exception as e:
        logger.error(f"Error in cleanup_old_deliveries: {str(e)}", exc_info=True)
    finally:
        db.close()
