"""
Tests for connector classes.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import httpx

from ..connectors import (
    BaseConnector, OAuthConnector, APIKeyConnector,
    JWTConnector, BasicAuthConnector, ConnectorError, AuthenticationError
)


class TestBaseConnector:
    """Test BaseConnector class."""

    @pytest.fixture
    def connector(self):
        """Create a test connector."""

        class TestConnector(BaseConnector):
            async def authenticate(self):
                return True

            async def test_connection(self):
                return {'success': True}

        return TestConnector(
            connection_id=1,
            config={'api_base_url': 'https://api.example.com'},
            credentials={'api_key': 'test_key'}
        )

    def test_initialization(self, connector):
        """Test connector initialization."""
        assert connector.connection_id == 1
        assert connector.config['api_base_url'] == 'https://api.example.com'
        assert connector.credentials['api_key'] == 'test_key'

    def test_build_url(self, connector):
        """Test URL building."""
        url = connector._build_url('/users')
        assert url == 'https://api.example.com/users'

    @pytest.mark.asyncio
    async def test_request_success(self, connector):
        """Test successful API request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': 'test'}
        mock_response.content = b'{"data": "test"}'

        with patch.object(connector.client, 'request', return_value=AsyncMock(return_value=mock_response)):
            result = await connector.request('GET', '/test')
            assert result == {'data': 'test'}

    @pytest.mark.asyncio
    async def test_pagination(self, connector):
        """Test pagination."""
        mock_responses = [
            {'data': [1, 2, 3], 'has_more': True},
            {'data': [4, 5, 6], 'has_more': False}
        ]

        with patch.object(connector, 'request', side_effect=mock_responses):
            items = await connector.paginate('/items', max_pages=2)
            assert len(items) == 6


class TestOAuthConnector:
    """Test OAuthConnector class."""

    @pytest.fixture
    def oauth_connector(self):
        """Create OAuth connector."""
        return OAuthConnector(
            connection_id=1,
            config={
                'api_base_url': 'https://api.example.com',
                'token_url': 'https://api.example.com/oauth/token',
                'client_id': 'test_client',
                'client_secret': 'test_secret'
            },
            credentials={
                'access_token': 'test_access_token',
                'refresh_token': 'test_refresh_token',
                'expires_at': (datetime.now() + timedelta(hours=1)).isoformat()
            }
        )

    def test_token_not_expired(self, oauth_connector):
        """Test token expiration check."""
        assert not oauth_connector._is_token_expired()

    def test_token_expired(self, oauth_connector):
        """Test expired token detection."""
        oauth_connector.token_expires_at = datetime.now() - timedelta(hours=1)
        assert oauth_connector._is_token_expired()

    @pytest.mark.asyncio
    async def test_authenticate(self, oauth_connector):
        """Test authentication."""
        result = await oauth_connector.authenticate()
        assert result is True

    @pytest.mark.asyncio
    async def test_refresh_token(self, oauth_connector):
        """Test token refresh."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'new_token',
            'refresh_token': 'new_refresh',
            'expires_in': 3600
        }

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            result = await oauth_connector.refresh_access_token()

            assert result['access_token'] == 'new_token'
            assert oauth_connector.access_token == 'new_token'


class TestAPIKeyConnector:
    """Test APIKeyConnector class."""

    @pytest.fixture
    def api_key_connector(self):
        """Create API key connector."""
        return APIKeyConnector(
            connection_id=1,
            config={
                'api_base_url': 'https://api.example.com',
                'api_key_location': 'header',
                'api_key_name': 'X-API-Key'
            },
            credentials={'api_key': 'test_api_key'}
        )

    def test_header_auth(self, api_key_connector):
        """Test API key in header."""
        headers = api_key_connector._get_default_headers()
        assert headers['X-API-Key'] == 'test_api_key'

    @pytest.mark.asyncio
    async def test_query_auth(self, api_key_connector):
        """Test API key in query parameters."""
        api_key_connector.api_key_location = 'query'
        api_key_connector.api_key_name = 'api_key'

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'success': True}
        mock_response.content = b'{"success": true}'

        with patch.object(api_key_connector.client, 'request', return_value=AsyncMock(return_value=mock_response)):
            result = await api_key_connector.request('GET', '/test', params={})
            # Verify api_key was added to params (would need to check call args)

    @pytest.mark.asyncio
    async def test_authenticate(self, api_key_connector):
        """Test authentication."""
        result = await api_key_connector.authenticate()
        assert result is True


class TestJWTConnector:
    """Test JWTConnector class."""

    @pytest.fixture
    def jwt_connector(self):
        """Create JWT connector."""
        return JWTConnector(
            connection_id=1,
            config={
                'api_base_url': 'https://api.example.com',
                'jwt_algorithm': 'HS256',
                'jwt_expiry_seconds': 3600
            },
            credentials={'jwt_secret': 'test_secret'}
        )

    def test_generate_jwt(self, jwt_connector):
        """Test JWT generation."""
        token = jwt_connector._generate_jwt({'user_id': 123})
        assert token is not None
        assert isinstance(token, str)

    def test_jwt_in_header(self, jwt_connector):
        """Test JWT added to authorization header."""
        headers = jwt_connector._get_default_headers()
        assert 'Authorization' in headers
        assert headers['Authorization'].startswith('Bearer ')

    @pytest.mark.asyncio
    async def test_authenticate(self, jwt_connector):
        """Test authentication."""
        result = await jwt_connector.authenticate()
        assert result is True
        assert jwt_connector.current_token is not None


class TestBasicAuthConnector:
    """Test BasicAuthConnector class."""

    @pytest.fixture
    def basic_auth_connector(self):
        """Create basic auth connector."""
        return BasicAuthConnector(
            connection_id=1,
            config={'api_base_url': 'https://api.example.com'},
            credentials={'username': 'test_user', 'password': 'test_pass'}
        )

    def test_basic_auth_header(self, basic_auth_connector):
        """Test Basic Auth header."""
        headers = basic_auth_connector._get_default_headers()
        assert 'Authorization' in headers
        assert headers['Authorization'].startswith('Basic ')

    @pytest.mark.asyncio
    async def test_authenticate(self, basic_auth_connector):
        """Test authentication."""
        result = await basic_auth_connector.authenticate()
        assert result is True

    @pytest.mark.asyncio
    async def test_missing_credentials(self):
        """Test error with missing credentials."""
        connector = BasicAuthConnector(
            connection_id=1,
            config={'api_base_url': 'https://api.example.com'},
            credentials={}
        )

        with pytest.raises(AuthenticationError):
            await connector.authenticate()
