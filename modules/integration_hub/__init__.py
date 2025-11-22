<<<<<<< HEAD
"""Integration Hub Module - Third-party integrations, API connectors, OAuth, webhooks."""
=======
"""
NEXUS Integration Hub Module

A comprehensive integration platform for connecting NEXUS with 15+ third-party services.

Features:
- OAuth 2.0, API Key, JWT, and Basic authentication
- Bidirectional data synchronization with conflict resolution
- Webhook management (incoming/outgoing) with retry logic
- Field mapping and data transformation
- Rate limiting and throttling
- Real-time monitoring and metrics
- Message queue and event bus
- 15+ pre-built integrations
- RESTful API and Streamlit UI
"""

__version__ = "1.0.0"
__author__ = "NEXUS Platform Team"

# Core components
from .connectors import (
    BaseConnector,
    OAuthConnector,
    APIKeyConnector,
    JWTConnector,
    BasicAuthConnector,
    CustomConnector,
    ConnectorError,
    AuthenticationError,
    RateLimitError,
    APIError
)

from .models import (
    Integration,
    Connection,
    SyncJob,
    Webhook,
    FieldMapping,
    Credential,
    AuthType,
    IntegrationStatus,
    SyncStatus,
    SyncDirection,
    WebhookStatus
)

from .registry import (
    IntegrationRegistry,
    ConnectorFactory,
    ConfigManager
)

from .oauth import OAuthFlowManager, OAuthError
from .webhooks import WebhookManager, WebhookReceiver, WebhookSender
from .sync import DataSync, BidirectionalSync, ConflictResolution
from .mapping import FieldMapper, DataTransformer, SchemaConverter
from .queue import MessageQueue, EventBus, DeadLetterQueue, get_queue, get_event_bus, get_dlq
from .rate_limiting import RateLimiter, ThrottleManager, BackoffStrategy
from .monitoring import IntegrationMetrics, SyncStatusMonitor, ErrorTracker

# API and UI
from .api import router as api_router
from .tasks import celery_app

__all__ = [
    # Core classes
    'BaseConnector',
    'OAuthConnector',
    'APIKeyConnector',
    'JWTConnector',
    'BasicAuthConnector',
    'CustomConnector',

    # Models
    'Integration',
    'Connection',
    'SyncJob',
    'Webhook',
    'FieldMapping',
    'Credential',

    # Enums
    'AuthType',
    'IntegrationStatus',
    'SyncStatus',
    'SyncDirection',
    'WebhookStatus',

    # Registry
    'IntegrationRegistry',
    'ConnectorFactory',
    'ConfigManager',

    # OAuth
    'OAuthFlowManager',

    # Webhooks
    'WebhookManager',
    'WebhookReceiver',
    'WebhookSender',

    # Sync
    'DataSync',
    'BidirectionalSync',
    'ConflictResolution',

    # Mapping
    'FieldMapper',
    'DataTransformer',
    'SchemaConverter',

    # Queue
    'MessageQueue',
    'EventBus',
    'DeadLetterQueue',
    'get_queue',
    'get_event_bus',
    'get_dlq',

    # Rate Limiting
    'RateLimiter',
    'ThrottleManager',
    'BackoffStrategy',

    # Monitoring
    'IntegrationMetrics',
    'SyncStatusMonitor',
    'ErrorTracker',

    # API
    'api_router',
    'celery_app',

    # Exceptions
    'ConnectorError',
    'AuthenticationError',
    'RateLimitError',
    'APIError',
    'OAuthError',
]


def get_version():
    """Get module version."""
    return __version__


def initialize_integration_hub(db, encryption_key: bytes):
    """
    Initialize Integration Hub with database and encryption.

    Args:
        db: Database session
        encryption_key: Encryption key for credentials

    Returns:
        Dictionary of initialized components
    """
    registry = IntegrationRegistry(db)
    oauth_manager = OAuthFlowManager(db, encryption_key)
    connector_factory = ConnectorFactory(db, encryption_key, oauth_manager)
    webhook_manager = WebhookManager(db)

    return {
        'registry': registry,
        'oauth_manager': oauth_manager,
        'connector_factory': connector_factory,
        'webhook_manager': webhook_manager,
        'version': __version__
    }
>>>>>>> origin/claude/build-integration-hub-01UtaRmVaBsWFKruxa7BHCxT
