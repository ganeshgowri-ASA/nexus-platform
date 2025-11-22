"""
OAuth 2.0 flow manager with multi-provider support.

This module handles the complete OAuth 2.0 authorization flow including
authorization URL generation, token exchange, token refresh, and state management.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from urllib.parse import urlencode, parse_qs, urlparse
import secrets
import logging
import httpx
from sqlalchemy.orm import Session

from .models import Integration, Connection, Credential, AuthType, IntegrationStatus
from .connectors import AuthenticationError

logger = logging.getLogger(__name__)


class OAuthError(Exception):
    """Base exception for OAuth errors."""
    pass


class OAuthStateError(OAuthError):
    """Raised when OAuth state validation fails."""
    pass


class OAuthFlowManager:
    """
    Manages OAuth 2.0 authorization flows for multiple providers.

    Handles authorization URL generation, callback processing,
    token exchange, and automatic token refresh.
    """

    def __init__(self, db: Session, encryption_key: bytes):
        """
        Initialize OAuth flow manager.

        Args:
            db: Database session
            encryption_key: Key for encrypting credentials
        """
        self.db = db
        self.encryption_key = encryption_key
        self._state_store: Dict[str, Dict[str, Any]] = {}

    def get_authorization_url(
        self,
        integration_id: int,
        redirect_uri: str,
        scopes: Optional[List[str]] = None,
        state: Optional[str] = None,
        extra_params: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """
        Generate OAuth authorization URL.

        Args:
            integration_id: Integration to authorize
            redirect_uri: Callback URL
            scopes: Requested scopes (uses integration defaults if not provided)
            state: CSRF protection state (generated if not provided)
            extra_params: Additional provider-specific parameters

        Returns:
            Dictionary with 'url' and 'state'

        Raises:
            OAuthError: If integration not found or not OAuth-enabled
        """
        # Get integration
        integration = self.db.query(Integration).filter(
            Integration.id == integration_id,
            Integration.auth_type == AuthType.OAUTH2
        ).first()

        if not integration:
            raise OAuthError(f"OAuth integration {integration_id} not found")

        # Get OAuth config
        config = integration.config
        auth_url = config.get('authorization_url')
        client_id = config.get('client_id')

        if not auth_url or not client_id:
            raise OAuthError(f"OAuth configuration incomplete for {integration.name}")

        # Generate or use provided state
        if not state:
            state = secrets.token_urlsafe(32)

        # Store state for validation
        self._state_store[state] = {
            'integration_id': integration_id,
            'redirect_uri': redirect_uri,
            'created_at': datetime.now(),
            'scopes': scopes or integration.default_scopes
        }

        # Build authorization URL
        params = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'state': state
        }

        # Add scopes
        scope_list = scopes or integration.default_scopes
        if scope_list:
            params['scope'] = ' '.join(scope_list)

        # Add provider-specific params
        if extra_params:
            params.update(extra_params)

        # Add config-specific params
        if 'authorization_params' in config:
            params.update(config['authorization_params'])

        url = f"{auth_url}?{urlencode(params)}"

        logger.info(f"Generated OAuth URL for {integration.name}: {url}")

        return {
            'url': url,
            'state': state
        }

    async def handle_callback(
        self,
        code: str,
        state: str,
        user_id: int,
        organization_id: Optional[int] = None,
        connection_name: Optional[str] = None
    ) -> Connection:
        """
        Handle OAuth callback and exchange code for tokens.

        Args:
            code: Authorization code from provider
            state: State parameter for CSRF protection
            user_id: User creating the connection
            organization_id: Organization (if applicable)
            connection_name: Custom connection name

        Returns:
            Created Connection object

        Raises:
            OAuthStateError: If state validation fails
            OAuthError: If token exchange fails
        """
        # Validate state
        if state not in self._state_store:
            raise OAuthStateError("Invalid or expired OAuth state")

        state_data = self._state_store.pop(state)

        # Check state expiry (15 minutes)
        if datetime.now() - state_data['created_at'] > timedelta(minutes=15):
            raise OAuthStateError("OAuth state expired")

        integration_id = state_data['integration_id']
        redirect_uri = state_data['redirect_uri']
        scopes = state_data['scopes']

        # Get integration
        integration = self.db.query(Integration).filter(
            Integration.id == integration_id
        ).first()

        if not integration:
            raise OAuthError(f"Integration {integration_id} not found")

        # Exchange code for tokens
        token_data = await self._exchange_code_for_tokens(
            integration=integration,
            code=code,
            redirect_uri=redirect_uri
        )

        # Get user info from provider (if supported)
        account_info = await self._get_account_info(integration, token_data)

        # Create credential
        credential = self._create_credential(
            auth_type=AuthType.OAUTH2,
            token_data=token_data
        )
        self.db.add(credential)
        self.db.flush()

        # Create connection
        connection = Connection(
            integration_id=integration_id,
            user_id=user_id,
            organization_id=organization_id,
            name=connection_name or f"{integration.name} - {account_info.get('email', 'Connection')}",
            status=IntegrationStatus.ACTIVE,
            credential_id=credential.id,
            config={},
            scopes=scopes,
            connected_account_id=account_info.get('id'),
            connected_account_name=account_info.get('name'),
            connected_account_email=account_info.get('email'),
            last_success_at=datetime.now()
        )

        # Set token expiry if available
        if 'expires_in' in token_data:
            connection.expires_at = datetime.now() + timedelta(seconds=token_data['expires_in'])

        self.db.add(connection)
        self.db.commit()
        self.db.refresh(connection)

        logger.info(f"Created OAuth connection {connection.id} for {integration.name}")

        return connection

    async def _exchange_code_for_tokens(
        self,
        integration: Integration,
        code: str,
        redirect_uri: str
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for access/refresh tokens.

        Args:
            integration: Integration object
            code: Authorization code
            redirect_uri: Redirect URI used in authorization

        Returns:
            Token data dictionary

        Raises:
            OAuthError: If token exchange fails
        """
        config = integration.config
        token_url = config.get('token_url')
        client_id = config.get('client_id')
        client_secret = config.get('client_secret')

        if not all([token_url, client_id, client_secret]):
            raise OAuthError("OAuth token exchange configuration incomplete")

        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri,
            'client_id': client_id,
            'client_secret': client_secret
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(token_url, data=data)
                response.raise_for_status()
                token_data = response.json()

            logger.info(f"Successfully exchanged code for tokens: {integration.name}")
            return token_data

        except httpx.HTTPError as e:
            logger.error(f"Token exchange failed: {str(e)}")
            raise OAuthError(f"Token exchange failed: {str(e)}")

    async def _get_account_info(
        self,
        integration: Integration,
        token_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get account information from the provider.

        Args:
            integration: Integration object
            token_data: OAuth token data

        Returns:
            Account information dictionary
        """
        config = integration.config
        user_info_url = config.get('user_info_url')

        if not user_info_url:
            return {}

        access_token = token_data.get('access_token')
        if not access_token:
            return {}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    user_info_url,
                    headers={'Authorization': f"Bearer {access_token}"}
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPError as e:
            logger.warning(f"Failed to get account info: {str(e)}")
            return {}

    def _create_credential(
        self,
        auth_type: AuthType,
        token_data: Dict[str, Any]
    ) -> Credential:
        """
        Create encrypted credential from token data.

        Args:
            auth_type: Authentication type
            token_data: Token data to encrypt

        Returns:
            Credential object
        """
        credential = Credential(
            auth_type=auth_type,
            token_type=token_data.get('token_type', 'Bearer')
        )

        # Encrypt entire token data
        credential.encrypt_data(token_data, self.encryption_key)

        # Store tokens separately (encrypted) for easy access
        if 'access_token' in token_data:
            from cryptography.fernet import Fernet
            fernet = Fernet(self.encryption_key)
            credential.access_token_encrypted = fernet.encrypt(
                token_data['access_token'].encode()
            ).decode()

        if 'refresh_token' in token_data:
            from cryptography.fernet import Fernet
            fernet = Fernet(self.encryption_key)
            credential.refresh_token_encrypted = fernet.encrypt(
                token_data['refresh_token'].encode()
            ).decode()

        # Set expiry
        if 'expires_in' in token_data:
            credential.token_expires_at = datetime.now() + timedelta(
                seconds=token_data['expires_in']
            )

        return credential

    async def refresh_token(self, connection_id: int) -> Dict[str, Any]:
        """
        Refresh OAuth access token.

        Args:
            connection_id: Connection ID

        Returns:
            New token data

        Raises:
            OAuthError: If refresh fails
        """
        # Get connection with credential
        connection = self.db.query(Connection).filter(
            Connection.id == connection_id
        ).first()

        if not connection:
            raise OAuthError(f"Connection {connection_id} not found")

        if not connection.credential:
            raise OAuthError("No credential found for connection")

        # Decrypt refresh token
        from cryptography.fernet import Fernet
        fernet = Fernet(self.encryption_key)

        if not connection.credential.refresh_token_encrypted:
            raise OAuthError("No refresh token available")

        refresh_token = fernet.decrypt(
            connection.credential.refresh_token_encrypted.encode()
        ).decode()

        # Get integration config
        integration = connection.integration
        config = integration.config
        token_url = config.get('token_url')
        client_id = config.get('client_id')
        client_secret = config.get('client_secret')

        if not all([token_url, client_id, client_secret]):
            raise OAuthError("OAuth refresh configuration incomplete")

        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': client_id,
            'client_secret': client_secret
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(token_url, data=data)
                response.raise_for_status()
                token_data = response.json()

            # Update credential
            credential = connection.credential

            # Encrypt new tokens
            if 'access_token' in token_data:
                credential.access_token_encrypted = fernet.encrypt(
                    token_data['access_token'].encode()
                ).decode()

            if 'refresh_token' in token_data:
                credential.refresh_token_encrypted = fernet.encrypt(
                    token_data['refresh_token'].encode()
                ).decode()

            # Update encrypted data
            credential.encrypt_data(token_data, self.encryption_key)

            # Update expiry
            if 'expires_in' in token_data:
                credential.token_expires_at = datetime.now() + timedelta(
                    seconds=token_data['expires_in']
                )
                connection.expires_at = credential.token_expires_at

            credential.updated_at = datetime.now()
            connection.last_success_at = datetime.now()
            connection.status = IntegrationStatus.ACTIVE

            self.db.commit()

            logger.info(f"Successfully refreshed token for connection {connection_id}")

            return token_data

        except httpx.HTTPError as e:
            logger.error(f"Token refresh failed: {str(e)}")
            connection.status = IntegrationStatus.ERROR
            connection.last_error_at = datetime.now()
            connection.last_error_message = f"Token refresh failed: {str(e)}"
            self.db.commit()
            raise OAuthError(f"Token refresh failed: {str(e)}")

    def revoke_token(self, connection_id: int) -> bool:
        """
        Revoke OAuth tokens and deactivate connection.

        Args:
            connection_id: Connection ID

        Returns:
            True if successful
        """
        connection = self.db.query(Connection).filter(
            Connection.id == connection_id
        ).first()

        if not connection:
            return False

        # Mark connection as inactive
        connection.is_active = False
        connection.status = IntegrationStatus.INACTIVE

        # Optional: Call provider's revocation endpoint
        integration = connection.integration
        revoke_url = integration.config.get('revoke_url')

        if revoke_url and connection.credential:
            try:
                # Decrypt access token
                from cryptography.fernet import Fernet
                fernet = Fernet(self.encryption_key)

                if connection.credential.access_token_encrypted:
                    access_token = fernet.decrypt(
                        connection.credential.access_token_encrypted.encode()
                    ).decode()

                    # Call revocation endpoint (synchronous for simplicity)
                    import requests
                    requests.post(
                        revoke_url,
                        data={'token': access_token},
                        timeout=10
                    )

                logger.info(f"Revoked token for connection {connection_id}")

            except Exception as e:
                logger.warning(f"Token revocation call failed: {str(e)}")

        self.db.commit()
        return True

    def get_decrypted_credentials(self, connection_id: int) -> Dict[str, Any]:
        """
        Get decrypted credentials for a connection.

        Args:
            connection_id: Connection ID

        Returns:
            Decrypted credential data

        Raises:
            OAuthError: If connection or credentials not found
        """
        connection = self.db.query(Connection).filter(
            Connection.id == connection_id
        ).first()

        if not connection or not connection.credential:
            raise OAuthError("Connection or credentials not found")

        # Decrypt credential data
        credential_data = connection.credential.decrypt_data(self.encryption_key)

        # Add separately stored tokens
        from cryptography.fernet import Fernet
        fernet = Fernet(self.encryption_key)

        if connection.credential.access_token_encrypted:
            credential_data['access_token'] = fernet.decrypt(
                connection.credential.access_token_encrypted.encode()
            ).decode()

        if connection.credential.refresh_token_encrypted:
            credential_data['refresh_token'] = fernet.decrypt(
                connection.credential.refresh_token_encrypted.encode()
            ).decode()

        if connection.credential.token_expires_at:
            credential_data['expires_at'] = connection.credential.token_expires_at

        return credential_data

    def cleanup_expired_states(self, max_age_minutes: int = 15) -> int:
        """
        Clean up expired OAuth states.

        Args:
            max_age_minutes: Maximum age in minutes

        Returns:
            Number of states removed
        """
        cutoff = datetime.now() - timedelta(minutes=max_age_minutes)
        expired_states = [
            state for state, data in self._state_store.items()
            if data['created_at'] < cutoff
        ]

        for state in expired_states:
            del self._state_store[state]

        if expired_states:
            logger.info(f"Cleaned up {len(expired_states)} expired OAuth states")

        return len(expired_states)


# Provider-specific OAuth configurations
OAUTH_PROVIDERS = {
    'google': {
        'authorization_url': 'https://accounts.google.com/o/oauth2/v2/auth',
        'token_url': 'https://oauth2.googleapis.com/token',
        'revoke_url': 'https://oauth2.googleapis.com/revoke',
        'user_info_url': 'https://www.googleapis.com/oauth2/v2/userinfo',
        'scopes': ['email', 'profile']
    },
    'microsoft': {
        'authorization_url': 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
        'token_url': 'https://login.microsoftonline.com/common/oauth2/v2.0/token',
        'user_info_url': 'https://graph.microsoft.com/v1.0/me',
        'scopes': ['User.Read']
    },
    'salesforce': {
        'authorization_url': 'https://login.salesforce.com/services/oauth2/authorize',
        'token_url': 'https://login.salesforce.com/services/oauth2/token',
        'revoke_url': 'https://login.salesforce.com/services/oauth2/revoke',
        'user_info_url': 'https://login.salesforce.com/services/oauth2/userinfo',
        'scopes': ['api', 'refresh_token']
    },
    'slack': {
        'authorization_url': 'https://slack.com/oauth/v2/authorize',
        'token_url': 'https://slack.com/api/oauth.v2.access',
        'user_info_url': 'https://slack.com/api/users.info',
        'scopes': ['chat:write', 'channels:read']
    },
    'github': {
        'authorization_url': 'https://github.com/login/oauth/authorize',
        'token_url': 'https://github.com/login/oauth/access_token',
        'user_info_url': 'https://api.github.com/user',
        'scopes': ['repo', 'user']
    },
    'hubspot': {
        'authorization_url': 'https://app.hubspot.com/oauth/authorize',
        'token_url': 'https://api.hubapi.com/oauth/v1/token',
        'user_info_url': 'https://api.hubapi.com/oauth/v1/access-tokens',
        'scopes': ['contacts', 'crm.objects.contacts.read']
    },
    'shopify': {
        'authorization_url': 'https://{shop}.myshopify.com/admin/oauth/authorize',
        'token_url': 'https://{shop}.myshopify.com/admin/oauth/access_token',
        'scopes': ['read_products', 'write_products', 'read_orders']
    },
    'zoom': {
        'authorization_url': 'https://zoom.us/oauth/authorize',
        'token_url': 'https://zoom.us/oauth/token',
        'user_info_url': 'https://api.zoom.us/v2/users/me',
        'scopes': ['meeting:read', 'meeting:write']
    }
}
