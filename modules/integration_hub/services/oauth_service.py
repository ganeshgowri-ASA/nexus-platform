"""OAuth 2.0 service for handling OAuth flows."""
from typing import Dict, Any, Optional, List
from authlib.integrations.requests_client import OAuth2Session
from authlib.oauth2.rfc6749 import OAuth2Token
from datetime import datetime, timedelta
from shared.security import encrypt_data, decrypt_data
from shared.utils.logger import get_logger
from modules.integration_hub.models import OAuthConnection, Integration
from sqlalchemy.orm import Session
import uuid

logger = get_logger(__name__)


class OAuthService:
    """Service for OAuth 2.0 authentication flows."""

    def __init__(self, db: Session):
        self.db = db
        self.logger = logger

    def initiate_oauth_flow(
        self, integration_id: str, redirect_uri: str, scopes: Optional[List[str]] = None, state: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Initiate OAuth 2.0 authorization flow.

        Returns:
            Authorization URL and state
        """
        try:
            # Get integration configuration
            integration = self.db.query(Integration).filter(Integration.id == integration_id).first()
            if not integration:
                raise ValueError(f"Integration not found: {integration_id}")

            if integration.auth_type != "oauth2":
                raise ValueError(f"Integration {integration.name} does not support OAuth")

            auth_config = integration.auth_config

            # Create OAuth2 session
            client = OAuth2Session(
                client_id=auth_config.get("client_id"),
                redirect_uri=redirect_uri,
                scope=scopes or auth_config.get("default_scopes", []),
            )

            # Generate authorization URL
            authorization_endpoint = auth_config.get("authorization_endpoint")
            auth_url, state = client.create_authorization_url(authorization_endpoint, state=state)

            self.logger.info(f"OAuth flow initiated for integration: {integration.name}")

            return {
                "authorization_url": auth_url,
                "state": state,
                "integration_id": integration_id,
            }

        except Exception as e:
            self.logger.error(f"Error initiating OAuth flow: {e}")
            raise

    def handle_callback(
        self, integration_id: str, code: str, redirect_uri: str, name: Optional[str] = None
    ) -> OAuthConnection:
        """
        Handle OAuth callback and exchange code for tokens.

        Returns:
            Created OAuth connection
        """
        try:
            # Get integration configuration
            integration = self.db.query(Integration).filter(Integration.id == integration_id).first()
            if not integration:
                raise ValueError(f"Integration not found: {integration_id}")

            auth_config = integration.auth_config

            # Create OAuth2 session
            client = OAuth2Session(
                client_id=auth_config.get("client_id"),
                client_secret=auth_config.get("client_secret"),
                redirect_uri=redirect_uri,
            )

            # Exchange code for token
            token_endpoint = auth_config.get("token_endpoint")
            token = client.fetch_token(token_endpoint, code=code)

            # Get user info if userinfo_endpoint is available
            user_info = None
            provider_user_id = None
            if "userinfo_endpoint" in auth_config:
                try:
                    user_info_response = client.get(auth_config["userinfo_endpoint"])
                    user_info = user_info_response.json()
                    provider_user_id = user_info.get("id") or user_info.get("sub")
                except Exception as e:
                    self.logger.warning(f"Failed to fetch user info: {e}")

            # Calculate token expiration
            expires_at = None
            if "expires_in" in token:
                expires_at = datetime.utcnow() + timedelta(seconds=token["expires_in"])

            # Encrypt tokens
            encrypted_access_token = encrypt_data(token["access_token"])
            encrypted_refresh_token = encrypt_data(token.get("refresh_token", "")) if "refresh_token" in token else None

            # Create connection record
            connection = OAuthConnection(
                id=str(uuid.uuid4()),
                integration_id=integration_id,
                name=name or f"{integration.name} Connection",
                encrypted_access_token=encrypted_access_token,
                encrypted_refresh_token=encrypted_refresh_token,
                token_type=token.get("token_type", "Bearer"),
                scopes=token.get("scope", "").split() if isinstance(token.get("scope"), str) else token.get("scope"),
                expires_at=expires_at,
                provider_user_id=provider_user_id,
                provider_user_info=user_info,
                is_active=True,
            )

            self.db.add(connection)
            self.db.commit()
            self.db.refresh(connection)

            self.logger.info(f"OAuth connection created: {connection.id}")

            return connection

        except Exception as e:
            self.logger.error(f"Error handling OAuth callback: {e}")
            self.db.rollback()
            raise

    def get_access_token(self, connection_id: str) -> str:
        """
        Get valid access token (refresh if needed).

        Returns:
            Decrypted access token
        """
        try:
            connection = self.db.query(OAuthConnection).filter(OAuthConnection.id == connection_id).first()
            if not connection:
                raise ValueError(f"OAuth connection not found: {connection_id}")

            # Check if token needs refresh
            if connection.expires_at and connection.expires_at < datetime.utcnow():
                self.logger.info("Token expired, refreshing...")
                connection = self.refresh_token(connection_id)

            # Decrypt and return access token
            access_token = decrypt_data(connection.encrypted_access_token)

            # Update last_used
            connection.last_used = datetime.utcnow()
            self.db.commit()

            return access_token

        except Exception as e:
            self.logger.error(f"Error getting access token: {e}")
            raise

    def refresh_token(self, connection_id: str) -> OAuthConnection:
        """Refresh OAuth access token."""
        try:
            connection = self.db.query(OAuthConnection).filter(OAuthConnection.id == connection_id).first()
            if not connection:
                raise ValueError(f"OAuth connection not found: {connection_id}")

            if not connection.encrypted_refresh_token:
                raise ValueError("No refresh token available")

            # Get integration configuration
            integration = self.db.query(Integration).filter(Integration.id == connection.integration_id).first()
            auth_config = integration.auth_config

            # Decrypt refresh token
            refresh_token = decrypt_data(connection.encrypted_refresh_token)

            # Create OAuth2 session
            client = OAuth2Session(
                client_id=auth_config.get("client_id"),
                client_secret=auth_config.get("client_secret"),
                token={"refresh_token": refresh_token, "token_type": connection.token_type},
            )

            # Refresh token
            token_endpoint = auth_config.get("token_endpoint")
            new_token = client.refresh_token(token_endpoint)

            # Update connection
            connection.encrypted_access_token = encrypt_data(new_token["access_token"])
            if "refresh_token" in new_token:
                connection.encrypted_refresh_token = encrypt_data(new_token["refresh_token"])

            if "expires_in" in new_token:
                connection.expires_at = datetime.utcnow() + timedelta(seconds=new_token["expires_in"])

            self.db.commit()
            self.db.refresh(connection)

            self.logger.info(f"Token refreshed for connection: {connection_id}")

            return connection

        except Exception as e:
            self.logger.error(f"Error refreshing token: {e}")
            self.db.rollback()
            raise

    def revoke_connection(self, connection_id: str) -> bool:
        """Revoke OAuth connection."""
        try:
            connection = self.db.query(OAuthConnection).filter(OAuthConnection.id == connection_id).first()
            if not connection:
                raise ValueError(f"OAuth connection not found: {connection_id}")

            # TODO: Call provider's revoke endpoint if available

            # Mark as inactive
            connection.is_active = False
            self.db.commit()

            self.logger.info(f"OAuth connection revoked: {connection_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error revoking connection: {e}")
            return False
