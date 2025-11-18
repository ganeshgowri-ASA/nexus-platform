"""
Base connector classes for third-party integrations.

This module provides abstract base classes and concrete implementations
for different authentication methods (OAuth, API Key, JWT, etc.).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
import logging
import httpx
import jwt as jwt_lib
import hashlib
import hmac
import base64
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


class ConnectorError(Exception):
    """Base exception for connector errors."""
    pass


class AuthenticationError(ConnectorError):
    """Raised when authentication fails."""
    pass


class RateLimitError(ConnectorError):
    """Raised when rate limit is exceeded."""
    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after


class APIError(ConnectorError):
    """Raised when API call fails."""
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class BaseConnector(ABC):
    """
    Abstract base class for all integration connectors.

    Provides common functionality for making API requests, handling errors,
    and managing connections to third-party services.
    """

    def __init__(
        self,
        connection_id: int,
        config: Dict[str, Any],
        credentials: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the connector.

        Args:
            connection_id: Database ID of the connection
            config: Connection configuration
            credentials: Decrypted credentials (if applicable)
        """
        self.connection_id = connection_id
        self.config = config
        self.credentials = credentials or {}
        self.client: Optional[httpx.AsyncClient] = None
        self._setup_client()

    def _setup_client(self) -> None:
        """Set up the HTTP client with default configuration."""
        headers = self._get_default_headers()
        timeout = self.config.get('timeout', 30.0)

        self.client = httpx.AsyncClient(
            headers=headers,
            timeout=timeout,
            follow_redirects=True
        )

    def _get_default_headers(self) -> Dict[str, str]:
        """
        Get default headers for API requests.

        Returns:
            Dictionary of default headers
        """
        return {
            'User-Agent': 'NEXUS-Integration-Hub/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

    @abstractmethod
    async def authenticate(self) -> bool:
        """
        Authenticate with the third-party service.

        Returns:
            True if authentication successful, False otherwise

        Raises:
            AuthenticationError: If authentication fails
        """
        pass

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to the service.

        Returns:
            Dictionary with test results
        """
        pass

    async def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make an authenticated API request.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint path
            params: URL query parameters
            data: Form data
            json: JSON payload
            headers: Additional headers
            **kwargs: Additional arguments for httpx.request

        Returns:
            Response data as dictionary

        Raises:
            APIError: If request fails
            RateLimitError: If rate limit exceeded
        """
        if not self.client:
            self._setup_client()

        url = self._build_url(endpoint)
        request_headers = {**self.client.headers, **(headers or {})}

        try:
            logger.debug(f"Making {method} request to {url}")

            response = await self.client.request(
                method=method,
                url=url,
                params=params,
                data=data,
                json=json,
                headers=request_headers,
                **kwargs
            )

            # Handle rate limiting
            if response.status_code == 429:
                retry_after = self._parse_retry_after(response)
                raise RateLimitError(
                    f"Rate limit exceeded for {url}",
                    retry_after=retry_after
                )

            # Handle errors
            if response.status_code >= 400:
                error_msg = f"API request failed: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', error_msg)
                except Exception:
                    error_msg = response.text

                raise APIError(
                    error_msg,
                    status_code=response.status_code,
                    response=response.json() if response.content else None
                )

            # Parse response
            if response.content:
                return response.json()
            return {}

        except httpx.HTTPError as e:
            logger.error(f"HTTP error for {url}: {str(e)}")
            raise APIError(f"HTTP request failed: {str(e)}")

    def _build_url(self, endpoint: str) -> str:
        """
        Build full URL from endpoint.

        Args:
            endpoint: API endpoint path

        Returns:
            Full URL
        """
        base_url = self.config.get('api_base_url', '').rstrip('/')
        endpoint = endpoint.lstrip('/')
        return f"{base_url}/{endpoint}"

    def _parse_retry_after(self, response: httpx.Response) -> Optional[int]:
        """
        Parse Retry-After header from response.

        Args:
            response: HTTP response

        Returns:
            Seconds to wait before retry, or None
        """
        retry_after = response.headers.get('Retry-After')
        if retry_after:
            try:
                return int(retry_after)
            except ValueError:
                # Could be a date format
                pass

        # Check for X-RateLimit-Reset header
        reset = response.headers.get('X-RateLimit-Reset')
        if reset:
            try:
                reset_time = datetime.fromtimestamp(int(reset))
                delta = (reset_time - datetime.now()).total_seconds()
                return max(0, int(delta))
            except ValueError:
                pass

        return None

    async def paginate(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        page_size: int = 100,
        max_pages: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Paginate through API results.

        Args:
            endpoint: API endpoint
            method: HTTP method
            params: Query parameters
            page_size: Number of items per page
            max_pages: Maximum number of pages to fetch

        Returns:
            List of all items from all pages
        """
        items = []
        page = 1
        params = params or {}

        while True:
            page_params = {
                **params,
                **self._get_pagination_params(page, page_size)
            }

            response = await self.request(method, endpoint, params=page_params)
            page_items = self._extract_items(response)
            items.extend(page_items)

            if not self._has_next_page(response, page_items):
                break

            page += 1
            if max_pages and page > max_pages:
                break

        return items

    def _get_pagination_params(self, page: int, page_size: int) -> Dict[str, Any]:
        """
        Get pagination parameters for the API.

        Override this method for service-specific pagination.

        Args:
            page: Page number
            page_size: Items per page

        Returns:
            Pagination parameters
        """
        return {
            'page': page,
            'per_page': page_size
        }

    def _extract_items(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract items from paginated response.

        Override this method for service-specific response structure.

        Args:
            response: API response

        Returns:
            List of items
        """
        # Default: assume response is a list
        if isinstance(response, list):
            return response

        # Common patterns
        for key in ['data', 'items', 'results', 'records']:
            if key in response and isinstance(response[key], list):
                return response[key]

        return []

    def _has_next_page(self, response: Dict[str, Any], items: List[Dict[str, Any]]) -> bool:
        """
        Check if there are more pages.

        Override this method for service-specific pagination logic.

        Args:
            response: API response
            items: Items from current page

        Returns:
            True if more pages exist
        """
        # Default: check if items were returned
        if not items:
            return False

        # Common patterns
        if 'has_more' in response:
            return bool(response['has_more'])

        if 'pagination' in response:
            pag = response['pagination']
            if 'has_next' in pag:
                return bool(pag['has_next'])
            if 'total_pages' in pag and 'current_page' in pag:
                return pag['current_page'] < pag['total_pages']

        return True  # Assume more pages if not explicitly indicated

    async def close(self) -> None:
        """Close the HTTP client."""
        if self.client:
            await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


class OAuthConnector(BaseConnector):
    """
    Connector for OAuth 2.0 authentication.

    Handles access token management, refresh token rotation,
    and OAuth-specific authorization headers.
    """

    def __init__(
        self,
        connection_id: int,
        config: Dict[str, Any],
        credentials: Optional[Dict[str, Any]] = None,
        token_refresh_callback: Optional[Callable] = None
    ):
        """
        Initialize OAuth connector.

        Args:
            connection_id: Database ID of the connection
            config: Connection configuration
            credentials: OAuth credentials (access_token, refresh_token, etc.)
            token_refresh_callback: Async callback to update tokens in database
        """
        super().__init__(connection_id, config, credentials)
        self.token_refresh_callback = token_refresh_callback
        self.access_token = credentials.get('access_token') if credentials else None
        self.refresh_token = credentials.get('refresh_token') if credentials else None
        self.token_expires_at = credentials.get('expires_at') if credentials else None

    def _get_default_headers(self) -> Dict[str, str]:
        """Add OAuth authorization header."""
        headers = super()._get_default_headers()
        if self.access_token:
            headers['Authorization'] = f"Bearer {self.access_token}"
        return headers

    async def authenticate(self) -> bool:
        """
        Authenticate or refresh OAuth token.

        Returns:
            True if authentication successful
        """
        if not self.access_token:
            raise AuthenticationError("No access token available")

        # Check if token needs refresh
        if self._is_token_expired():
            if self.refresh_token:
                await self.refresh_access_token()
            else:
                raise AuthenticationError("Access token expired and no refresh token available")

        return True

    def _is_token_expired(self) -> bool:
        """Check if access token is expired."""
        if not self.token_expires_at:
            return False

        # Add 5-minute buffer
        buffer = timedelta(minutes=5)
        expires_at = datetime.fromisoformat(self.token_expires_at) if isinstance(self.token_expires_at, str) else self.token_expires_at
        return datetime.now() >= (expires_at - buffer)

    async def refresh_access_token(self) -> Dict[str, Any]:
        """
        Refresh the access token using refresh token.

        Returns:
            New token data
        """
        token_url = self.config.get('token_url')
        client_id = self.config.get('client_id')
        client_secret = self.config.get('client_secret')

        if not all([token_url, client_id, client_secret, self.refresh_token]):
            raise AuthenticationError("Missing required OAuth configuration for token refresh")

        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
            'client_id': client_id,
            'client_secret': client_secret
        }

        try:
            # Don't use self.request() to avoid recursion
            async with httpx.AsyncClient() as client:
                response = await client.post(token_url, data=data)
                response.raise_for_status()
                token_data = response.json()

            # Update tokens
            self.access_token = token_data['access_token']
            if 'refresh_token' in token_data:
                self.refresh_token = token_data['refresh_token']

            if 'expires_in' in token_data:
                self.token_expires_at = datetime.now() + timedelta(seconds=token_data['expires_in'])

            # Update headers
            if self.client:
                self.client.headers['Authorization'] = f"Bearer {self.access_token}"

            # Call callback to persist tokens
            if self.token_refresh_callback:
                await self.token_refresh_callback({
                    'access_token': self.access_token,
                    'refresh_token': self.refresh_token,
                    'expires_at': self.token_expires_at
                })

            logger.info(f"Successfully refreshed OAuth token for connection {self.connection_id}")
            return token_data

        except httpx.HTTPError as e:
            logger.error(f"Failed to refresh OAuth token: {str(e)}")
            raise AuthenticationError(f"Token refresh failed: {str(e)}")

    async def test_connection(self) -> Dict[str, Any]:
        """Test OAuth connection."""
        try:
            await self.authenticate()

            # Try a simple API call
            test_endpoint = self.config.get('test_endpoint', '/user')
            response = await self.request('GET', test_endpoint)

            return {
                'success': True,
                'message': 'Connection successful',
                'user_info': response
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Connection failed: {str(e)}'
            }


class APIKeyConnector(BaseConnector):
    """
    Connector for API Key authentication.

    Supports various API key formats (header, query parameter, custom).
    """

    def __init__(
        self,
        connection_id: int,
        config: Dict[str, Any],
        credentials: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize API Key connector.

        Args:
            connection_id: Database ID of the connection
            config: Connection configuration (must include api_key_location)
            credentials: Must include 'api_key'
        """
        super().__init__(connection_id, config, credentials)
        self.api_key = credentials.get('api_key') if credentials else None
        self.api_key_location = config.get('api_key_location', 'header')  # header, query, custom
        self.api_key_name = config.get('api_key_name', 'X-API-Key')

    def _get_default_headers(self) -> Dict[str, str]:
        """Add API key to headers if configured."""
        headers = super()._get_default_headers()

        if self.api_key and self.api_key_location == 'header':
            headers[self.api_key_name] = self.api_key

        return headers

    async def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Make request with API key in query if configured."""
        # Add API key to query parameters if needed
        if self.api_key and self.api_key_location == 'query':
            params = params or {}
            params[self.api_key_name] = self.api_key

        return await super().request(method, endpoint, params=params, **kwargs)

    async def authenticate(self) -> bool:
        """Validate API key."""
        if not self.api_key:
            raise AuthenticationError("No API key provided")
        return True

    async def test_connection(self) -> Dict[str, Any]:
        """Test API key connection."""
        try:
            await self.authenticate()

            # Try a simple API call
            test_endpoint = self.config.get('test_endpoint', '/')
            response = await self.request('GET', test_endpoint)

            return {
                'success': True,
                'message': 'API key is valid',
                'response': response
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'API key validation failed: {str(e)}'
            }


class JWTConnector(BaseConnector):
    """
    Connector for JWT (JSON Web Token) authentication.

    Generates and manages JWT tokens for API authentication.
    """

    def __init__(
        self,
        connection_id: int,
        config: Dict[str, Any],
        credentials: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize JWT connector.

        Args:
            connection_id: Database ID of the connection
            config: Connection configuration
            credentials: Must include JWT secret or private key
        """
        super().__init__(connection_id, config, credentials)
        self.jwt_secret = credentials.get('jwt_secret') if credentials else None
        self.jwt_algorithm = config.get('jwt_algorithm', 'HS256')
        self.jwt_expiry = config.get('jwt_expiry_seconds', 3600)
        self.current_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None

    def _generate_jwt(self, payload: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a JWT token.

        Args:
            payload: Additional claims to include in token

        Returns:
            JWT token string
        """
        if not self.jwt_secret:
            raise AuthenticationError("No JWT secret provided")

        now = datetime.now()
        expires_at = now + timedelta(seconds=self.jwt_expiry)

        claims = {
            'iat': now,
            'exp': expires_at,
            'connection_id': self.connection_id,
            **(payload or {})
        }

        # Add custom claims from config
        if 'jwt_claims' in self.config:
            claims.update(self.config['jwt_claims'])

        token = jwt_lib.encode(claims, self.jwt_secret, algorithm=self.jwt_algorithm)

        self.current_token = token
        self.token_expires_at = expires_at

        return token

    def _is_token_expired(self) -> bool:
        """Check if JWT token is expired."""
        if not self.token_expires_at:
            return True

        # Add 1-minute buffer
        buffer = timedelta(minutes=1)
        return datetime.now() >= (self.token_expires_at - buffer)

    def _get_default_headers(self) -> Dict[str, str]:
        """Add JWT to authorization header."""
        headers = super()._get_default_headers()

        # Ensure we have a valid token
        if not self.current_token or self._is_token_expired():
            self._generate_jwt()

        if self.current_token:
            headers['Authorization'] = f"Bearer {self.current_token}"

        return headers

    async def authenticate(self) -> bool:
        """Generate JWT token."""
        self._generate_jwt()
        return True

    async def test_connection(self) -> Dict[str, Any]:
        """Test JWT connection."""
        try:
            await self.authenticate()

            # Try a simple API call
            test_endpoint = self.config.get('test_endpoint', '/')
            response = await self.request('GET', test_endpoint)

            return {
                'success': True,
                'message': 'JWT authentication successful',
                'response': response
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'JWT authentication failed: {str(e)}'
            }


class BasicAuthConnector(BaseConnector):
    """
    Connector for HTTP Basic Authentication.

    Uses username and password for authentication.
    """

    def __init__(
        self,
        connection_id: int,
        config: Dict[str, Any],
        credentials: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Basic Auth connector.

        Args:
            connection_id: Database ID of the connection
            config: Connection configuration
            credentials: Must include 'username' and 'password'
        """
        super().__init__(connection_id, config, credentials)
        self.username = credentials.get('username') if credentials else None
        self.password = credentials.get('password') if credentials else None

    def _get_default_headers(self) -> Dict[str, str]:
        """Add Basic Auth header."""
        headers = super()._get_default_headers()

        if self.username and self.password:
            credentials = f"{self.username}:{self.password}"
            encoded = base64.b64encode(credentials.encode()).decode()
            headers['Authorization'] = f"Basic {encoded}"

        return headers

    async def authenticate(self) -> bool:
        """Validate credentials."""
        if not self.username or not self.password:
            raise AuthenticationError("Username and password required for Basic Auth")
        return True

    async def test_connection(self) -> Dict[str, Any]:
        """Test Basic Auth connection."""
        try:
            await self.authenticate()

            test_endpoint = self.config.get('test_endpoint', '/')
            response = await self.request('GET', test_endpoint)

            return {
                'success': True,
                'message': 'Basic authentication successful',
                'response': response
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Basic authentication failed: {str(e)}'
            }


class CustomConnector(BaseConnector):
    """
    Connector for custom authentication schemes.

    Allows implementing custom authentication logic through configuration.
    """

    def __init__(
        self,
        connection_id: int,
        config: Dict[str, Any],
        credentials: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Custom connector.

        Args:
            connection_id: Database ID of the connection
            config: Connection configuration with custom auth logic
            credentials: Custom credentials
        """
        super().__init__(connection_id, config, credentials)

    def _get_default_headers(self) -> Dict[str, str]:
        """Build headers from custom configuration."""
        headers = super()._get_default_headers()

        # Add custom headers from config
        if 'custom_headers' in self.config:
            for key, value_template in self.config['custom_headers'].items():
                # Replace placeholders with credential values
                value = value_template
                for cred_key, cred_value in self.credentials.items():
                    value = value.replace(f'{{{cred_key}}}', str(cred_value))
                headers[key] = value

        return headers

    async def authenticate(self) -> bool:
        """
        Custom authentication logic.

        Override this in subclasses for specific services.
        """
        return True

    async def test_connection(self) -> Dict[str, Any]:
        """Test custom connection."""
        try:
            await self.authenticate()

            test_endpoint = self.config.get('test_endpoint', '/')
            response = await self.request('GET', test_endpoint)

            return {
                'success': True,
                'message': 'Custom authentication successful',
                'response': response
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Custom authentication failed: {str(e)}'
            }
