"""Signature verification service for webhook security"""

import hmac
import hashlib
import json
from typing import Dict, Any


class SignatureService:
    """Service for HMAC signature generation and verification"""

    @staticmethod
    def generate_signature(payload: Dict[str, Any], secret: str) -> str:
        """
        Generate HMAC-SHA256 signature for webhook payload

        Args:
            payload: The payload to sign
            secret: The webhook secret key

        Returns:
            Hexadecimal signature string
        """
        payload_json = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        signature = hmac.new(
            secret.encode('utf-8'),
            payload_json.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature

    @staticmethod
    def verify_signature(payload: Dict[str, Any], signature: str, secret: str) -> bool:
        """
        Verify HMAC-SHA256 signature

        Args:
            payload: The received payload
            signature: The signature to verify
            secret: The webhook secret key

        Returns:
            True if signature is valid, False otherwise
        """
        expected_signature = SignatureService.generate_signature(payload, secret)
        return hmac.compare_digest(expected_signature, signature)

    @staticmethod
    def create_signature_header(payload: Dict[str, Any], secret: str) -> Dict[str, str]:
        """
        Create signature header for webhook request

        Args:
            payload: The payload to sign
            secret: The webhook secret key

        Returns:
            Dictionary with signature header
        """
        signature = SignatureService.generate_signature(payload, secret)
        return {"X-Webhook-Signature": f"sha256={signature}"}
