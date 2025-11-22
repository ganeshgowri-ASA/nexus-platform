"""Tests for webhook service"""

import pytest
from modules.webhooks.services.webhook_service import WebhookService


def test_generate_secret():
    """Test secret generation"""
    secret = WebhookService.generate_secret()

    assert secret is not None
    assert isinstance(secret, str)
    assert len(secret) > 20  # Should be reasonably long


def test_generate_secret_custom_length():
    """Test secret generation with custom length"""
    secret = WebhookService.generate_secret(length=64)

    assert secret is not None
    assert isinstance(secret, str)


def test_generate_secret_unique():
    """Test that generated secrets are unique"""
    secret1 = WebhookService.generate_secret()
    secret2 = WebhookService.generate_secret()

    assert secret1 != secret2
