"""
Integration registry and connector factory.

Manages registration of integrations, connector instantiation,
and configuration management.
"""

from typing import Dict, Any, Optional, Type, List
import logging
from sqlalchemy.orm import Session

from .models import Integration, Connection, AuthType
from .connectors import (
    BaseConnector, OAuthConnector, APIKeyConnector,
    JWTConnector, BasicAuthConnector, CustomConnector
)
from .oauth import OAuthFlowManager

logger = logging.getLogger(__name__)


class IntegrationRegistry:
    """
    Registry for managing integrations.

    Provides centralized registration and discovery of
    available integrations.
    """

    def __init__(self, db: Session):
        """
        Initialize integration registry.

        Args:
            db: Database session
        """
        self.db = db
        self._connectors: Dict[str, Type[BaseConnector]] = {
            'oauth2': OAuthConnector,
            'api_key': APIKeyConnector,
            'jwt': JWTConnector,
            'basic': BasicAuthConnector,
            'custom': CustomConnector
        }

    def register_integration(
        self,
        name: str,
        slug: str,
        provider: str,
        auth_type: AuthType,
        config: Dict[str, Any],
        **kwargs
    ) -> Integration:
        """
        Register a new integration.

        Args:
            name: Integration name
            slug: URL-friendly slug
            provider: Provider name
            auth_type: Authentication type
            config: Integration configuration
            **kwargs: Additional integration properties

        Returns:
            Created Integration object
        """
        integration = Integration(
            name=name,
            slug=slug,
            provider=provider,
            auth_type=auth_type,
            config=config,
            **kwargs
        )

        self.db.add(integration)
        self.db.commit()
        self.db.refresh(integration)

        logger.info(f"Registered integration: {name} ({provider})")

        return integration

    def get_integration(
        self,
        slug: Optional[str] = None,
        integration_id: Optional[int] = None
    ) -> Optional[Integration]:
        """
        Get integration by slug or ID.

        Args:
            slug: Integration slug
            integration_id: Integration ID

        Returns:
            Integration object or None
        """
        if integration_id:
            return self.db.query(Integration).filter(
                Integration.id == integration_id
            ).first()

        if slug:
            return self.db.query(Integration).filter(
                Integration.slug == slug
            ).first()

        return None

    def list_integrations(
        self,
        category: Optional[str] = None,
        active_only: bool = True
    ) -> List[Integration]:
        """
        List available integrations.

        Args:
            category: Optional category filter
            active_only: Only return active integrations

        Returns:
            List of integrations
        """
        query = self.db.query(Integration)

        if active_only:
            query = query.filter(Integration.is_active == True)

        if category:
            query = query.filter(Integration.category == category)

        return query.order_by(Integration.name).all()

    def register_connector_type(
        self,
        auth_type: str,
        connector_class: Type[BaseConnector]
    ) -> None:
        """
        Register a custom connector type.

        Args:
            auth_type: Authentication type identifier
            connector_class: Connector class
        """
        self._connectors[auth_type] = connector_class
        logger.info(f"Registered connector type: {auth_type}")

    def get_connector_class(self, auth_type: str) -> Optional[Type[BaseConnector]]:
        """
        Get connector class for auth type.

        Args:
            auth_type: Authentication type

        Returns:
            Connector class or None
        """
        return self._connectors.get(auth_type)


class ConnectorFactory:
    """
    Factory for creating connector instances.

    Instantiates connectors with proper configuration and credentials.
    """

    def __init__(
        self,
        db: Session,
        encryption_key: bytes,
        oauth_manager: Optional[OAuthFlowManager] = None
    ):
        """
        Initialize connector factory.

        Args:
            db: Database session
            encryption_key: Encryption key for credentials
            oauth_manager: Optional OAuth manager
        """
        self.db = db
        self.encryption_key = encryption_key
        self.oauth_manager = oauth_manager or OAuthFlowManager(db, encryption_key)
        self.registry = IntegrationRegistry(db)

    def create_connector(
        self,
        connection_id: int,
        token_refresh_callback: Optional[Any] = None
    ) -> BaseConnector:
        """
        Create connector instance for a connection.

        Args:
            connection_id: Connection ID
            token_refresh_callback: Optional callback for token refresh

        Returns:
            Connector instance

        Raises:
            ValueError: If connection not found or connector type unknown
        """
        # Get connection
        connection = self.db.query(Connection).filter(
            Connection.id == connection_id
        ).first()

        if not connection:
            raise ValueError(f"Connection {connection_id} not found")

        integration = connection.integration

        # Get connector class
        connector_class = self.registry.get_connector_class(integration.auth_type.value)

        if not connector_class:
            raise ValueError(f"Unknown connector type: {integration.auth_type.value}")

        # Build configuration
        config = {
            **integration.config,
            **connection.config,
            'api_base_url': integration.api_base_url
        }

        # Get decrypted credentials
        credentials = None
        if connection.credential:
            credentials = connection.credential.decrypt_data(self.encryption_key)

            # For OAuth, add separately stored tokens
            if integration.auth_type == AuthType.OAUTH2:
                from cryptography.fernet import Fernet
                fernet = Fernet(self.encryption_key)

                if connection.credential.access_token_encrypted:
                    credentials['access_token'] = fernet.decrypt(
                        connection.credential.access_token_encrypted.encode()
                    ).decode()

                if connection.credential.refresh_token_encrypted:
                    credentials['refresh_token'] = fernet.decrypt(
                        connection.credential.refresh_token_encrypted.encode()
                    ).decode()

                if connection.credential.token_expires_at:
                    credentials['expires_at'] = connection.credential.token_expires_at

        # Create connector
        if integration.auth_type == AuthType.OAUTH2:
            connector = connector_class(
                connection_id=connection_id,
                config=config,
                credentials=credentials,
                token_refresh_callback=token_refresh_callback or self._default_token_refresh_callback
            )
        else:
            connector = connector_class(
                connection_id=connection_id,
                config=config,
                credentials=credentials
            )

        logger.info(f"Created {integration.auth_type.value} connector for connection {connection_id}")

        return connector

    async def _default_token_refresh_callback(self, token_data: Dict[str, Any]) -> None:
        """Default callback for token refresh."""
        # This would update tokens in database
        logger.info("Token refresh callback triggered")


class ConfigManager:
    """
    Manages integration and connection configurations.

    Provides configuration validation, templates, and management.
    """

    def __init__(self, db: Session):
        """
        Initialize config manager.

        Args:
            db: Database session
        """
        self.db = db

    def get_config_template(self, integration_slug: str) -> Dict[str, Any]:
        """
        Get configuration template for an integration.

        Args:
            integration_slug: Integration slug

        Returns:
            Configuration template
        """
        integration = self.db.query(Integration).filter(
            Integration.slug == integration_slug
        ).first()

        if not integration:
            return {}

        template = {
            'auth_type': integration.auth_type.value,
            'required_config': [],
            'optional_config': [],
            'scopes': integration.default_scopes,
            'api_base_url': integration.api_base_url
        }

        # Add auth-specific requirements
        if integration.auth_type == AuthType.OAUTH2:
            template['required_config'].extend([
                'client_id',
                'client_secret',
                'redirect_uri'
            ])
        elif integration.auth_type == AuthType.API_KEY:
            template['required_config'].append('api_key')
            template['optional_config'].extend([
                'api_key_location',  # header, query, custom
                'api_key_name'
            ])
        elif integration.auth_type == AuthType.JWT:
            template['required_config'].append('jwt_secret')
            template['optional_config'].extend([
                'jwt_algorithm',
                'jwt_expiry_seconds'
            ])
        elif integration.auth_type == AuthType.BASIC:
            template['required_config'].extend([
                'username',
                'password'
            ])

        return template

    def validate_config(
        self,
        integration_slug: str,
        config: Dict[str, Any]
    ) -> tuple[bool, List[str]]:
        """
        Validate configuration against requirements.

        Args:
            integration_slug: Integration slug
            config: Configuration to validate

        Returns:
            Tuple of (is_valid, errors)
        """
        template = self.get_config_template(integration_slug)
        errors = []

        # Check required fields
        for field in template.get('required_config', []):
            if field not in config:
                errors.append(f"Missing required field: {field}")

        return len(errors) == 0, errors

    def export_config(self, connection_id: int) -> Dict[str, Any]:
        """
        Export connection configuration.

        Args:
            connection_id: Connection ID

        Returns:
            Exported configuration (without sensitive data)
        """
        connection = self.db.query(Connection).filter(
            Connection.id == connection_id
        ).first()

        if not connection:
            return {}

        return {
            'integration': connection.integration.slug,
            'name': connection.name,
            'config': connection.config,
            'scopes': connection.scopes,
            'status': connection.status.value,
            'created_at': connection.created_at.isoformat()
        }

    def import_config(
        self,
        user_id: int,
        config_data: Dict[str, Any],
        credentials: Optional[Dict[str, Any]] = None
    ) -> Connection:
        """
        Import connection configuration.

        Args:
            user_id: User ID
            config_data: Configuration data
            credentials: Optional credentials

        Returns:
            Created Connection object
        """
        # Get integration
        integration = self.db.query(Integration).filter(
            Integration.slug == config_data['integration']
        ).first()

        if not integration:
            raise ValueError(f"Integration not found: {config_data['integration']}")

        # Create connection
        connection = Connection(
            integration_id=integration.id,
            user_id=user_id,
            name=config_data['name'],
            config=config_data.get('config', {}),
            scopes=config_data.get('scopes', [])
        )

        # Add credentials if provided
        if credentials:
            from .models import Credential
            credential = Credential(auth_type=integration.auth_type)
            credential.encrypt_data(credentials, self.encryption_key)
            self.db.add(credential)
            self.db.flush()
            connection.credential_id = credential.id

        self.db.add(connection)
        self.db.commit()
        self.db.refresh(connection)

        logger.info(f"Imported configuration for {config_data['name']}")

        return connection


def register_builtin_integrations(registry: IntegrationRegistry) -> None:
    """
    Register built-in integrations.

    Args:
        registry: Integration registry
    """
    # Salesforce
    registry.register_integration(
        name="Salesforce",
        slug="salesforce",
        provider="salesforce",
        auth_type=AuthType.OAUTH2,
        category="CRM",
        config={
            "authorization_url": "https://login.salesforce.com/services/oauth2/authorize",
            "token_url": "https://login.salesforce.com/services/oauth2/token",
            "api_base_url": "https://instance.salesforce.com/services/data/v57.0",
            "test_endpoint": "/query?q=SELECT+Id+FROM+User+LIMIT+1"
        },
        default_scopes=["api", "refresh_token"],
        supports_webhooks=True,
        supports_bidirectional_sync=True
    )

    # Add more built-in integrations here...
    logger.info("Registered built-in integrations")
