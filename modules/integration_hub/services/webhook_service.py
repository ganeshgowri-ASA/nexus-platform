"""Webhook service for triggering and managing webhooks."""
from typing import Dict, Any, Optional
import httpx
import hashlib
import hmac
from shared.utils.logger import get_logger
from modules.integration_hub.models import Webhook
from sqlalchemy.orm import Session
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential

logger = get_logger(__name__)


class WebhookService:
    """Service for managing and triggering webhooks."""

    def __init__(self, db: Session):
        self.db = db
        self.logger = logger

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def trigger_webhook(self, webhook_id: str, event: str, payload: Dict[str, Any]) -> bool:
        """
        Trigger a webhook with the given event and payload.

        Returns:
            Success status
        """
        try:
            webhook = self.db.query(Webhook).filter(Webhook.id == webhook_id).first()
            if not webhook or not webhook.is_active:
                self.logger.warning(f"Webhook not found or inactive: {webhook_id}")
                return False

            # Check if webhook listens to this event
            if event not in webhook.events:
                self.logger.debug(f"Webhook {webhook.name} does not listen to event: {event}")
                return False

            # Prepare payload
            final_payload = self._prepare_payload(webhook, event, payload)

            # Prepare headers
            headers = webhook.headers.copy() if webhook.headers else {}
            headers["Content-Type"] = "application/json"
            headers["X-Webhook-Event"] = event
            headers["X-Webhook-ID"] = webhook_id

            # Add signature if secret is configured
            if webhook.secret:
                signature = self._generate_signature(final_payload, webhook.secret)
                headers["X-Webhook-Signature"] = signature

            # Send webhook
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(webhook.url, json=final_payload, headers=headers)
                response.raise_for_status()

            # Update webhook stats
            webhook.last_triggered = datetime.utcnow()
            webhook.trigger_count += 1
            self.db.commit()

            self.logger.info(f"Webhook triggered successfully: {webhook.name} (event: {event})")
            return True

        except Exception as e:
            self.logger.error(f"Error triggering webhook {webhook_id}: {e}")

            # Update failure count
            if webhook:
                webhook.failure_count += 1
                self.db.commit()

            raise

    def _prepare_payload(self, webhook: Webhook, event: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare webhook payload using template or default format."""
        if webhook.payload_template:
            # Apply template (simple variable substitution)
            import json

            template_str = json.dumps(webhook.payload_template)
            for key, value in data.items():
                template_str = template_str.replace(f"{{{key}}}", str(value))
            return json.loads(template_str)
        else:
            # Default payload format
            return {"event": event, "timestamp": datetime.utcnow().isoformat(), "data": data}

    def _generate_signature(self, payload: Dict[str, Any], secret: str) -> str:
        """Generate HMAC signature for webhook verification."""
        import json

        payload_bytes = json.dumps(payload, sort_keys=True).encode()
        signature = hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()
        return signature

    def test_webhook(self, webhook_id: str) -> bool:
        """Send a test webhook."""
        test_payload = {"test": True, "message": "This is a test webhook"}
        return self.trigger_webhook(webhook_id, "test", test_payload)
