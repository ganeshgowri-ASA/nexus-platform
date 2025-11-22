<<<<<<< HEAD
"""
Core module for NEXUS Platform.

This module contains security, authentication, and shared utilities.
"""

from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from app.core.exceptions import (
    NexusException,
    AuthenticationError,
    AuthorizationError,
    ResourceNotFoundError,
    ValidationError,
    CampaignError,
    BudgetExceededError,
)
from app.core.celery_app import celery_app

__all__ = [
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "create_refresh_token",
    "verify_token",
    "NexusException",
    "AuthenticationError",
    "AuthorizationError",
    "ResourceNotFoundError",
    "ValidationError",
    "CampaignError",
    "BudgetExceededError",
    "celery_app",
]
=======
"""Core application configuration and settings"""
>>>>>>> origin/claude/ocr-translation-modules-01Kv1eeHRaW9ea224g8V59NS
