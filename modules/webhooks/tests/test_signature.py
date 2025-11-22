"""Tests for signature verification"""

import pytest
from modules.webhooks.services.signature_service import SignatureService


def test_generate_signature():
    """Test signature generation"""
    payload = {"user_id": 123, "action": "created"}
    secret = "test-secret"

    signature = SignatureService.generate_signature(payload, secret)

    assert signature is not None
    assert isinstance(signature, str)
    assert len(signature) == 64  # SHA-256 hex digest length


def test_verify_signature_valid():
    """Test signature verification with valid signature"""
    payload = {"user_id": 123, "action": "created"}
    secret = "test-secret"

    signature = SignatureService.generate_signature(payload, secret)
    is_valid = SignatureService.verify_signature(payload, signature, secret)

    assert is_valid is True


def test_verify_signature_invalid():
    """Test signature verification with invalid signature"""
    payload = {"user_id": 123, "action": "created"}
    secret = "test-secret"
    wrong_signature = "invalid-signature"

    is_valid = SignatureService.verify_signature(payload, wrong_signature, secret)

    assert is_valid is False


def test_verify_signature_wrong_secret():
    """Test signature verification with wrong secret"""
    payload = {"user_id": 123, "action": "created"}
    secret = "test-secret"
    wrong_secret = "wrong-secret"

    signature = SignatureService.generate_signature(payload, secret)
    is_valid = SignatureService.verify_signature(payload, signature, wrong_secret)

    assert is_valid is False


def test_signature_header():
    """Test signature header creation"""
    payload = {"user_id": 123, "action": "created"}
    secret = "test-secret"

    header = SignatureService.create_signature_header(payload, secret)

    assert "X-Webhook-Signature" in header
    assert header["X-Webhook-Signature"].startswith("sha256=")
