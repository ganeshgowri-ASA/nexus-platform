"""
Tests for the authentication module.
"""

import pytest
from modules.api_builder.auth import (
    APIKeyAuth,
    JWTAuth,
    BasicAuth,
    OAuth2Auth,
    AuthManager,
    create_api_key_auth,
    create_jwt_auth,
    APIKeyLocation,
)


class TestAPIKeyAuth:
    """Tests for API Key authentication."""

    def test_create_api_key_auth(self):
        """Test creating API key authentication."""
        auth = create_api_key_auth()

        assert auth.name == "apiKey"
        assert auth.location == APIKeyLocation.HEADER

    def test_generate_api_key(self):
        """Test generating an API key."""
        auth = APIKeyAuth(name="test", location=APIKeyLocation.HEADER)

        key = auth.generate_key("test")

        assert key.startswith("test_")
        assert key in auth.valid_keys

    def test_authenticate_valid_key(self):
        """Test authenticating with valid API key."""
        auth = APIKeyAuth(
            name="test",
            location=APIKeyLocation.HEADER,
            parameter_name="X-API-Key",
        )

        key = auth.generate_key()

        is_valid, error = auth.authenticate({"X-API-Key": key})

        assert is_valid is True
        assert error is None

    def test_authenticate_invalid_key(self):
        """Test authenticating with invalid API key."""
        auth = APIKeyAuth(name="test", location=APIKeyLocation.HEADER)

        is_valid, error = auth.authenticate({"X-API-Key": "invalid-key"})

        assert is_valid is False
        assert "Invalid API key" in error

    def test_revoke_key(self):
        """Test revoking an API key."""
        auth = APIKeyAuth(name="test", location=APIKeyLocation.HEADER)

        key = auth.generate_key()
        result = auth.revoke_key(key)

        assert result is True
        assert key not in auth.valid_keys


class TestJWTAuth:
    """Tests for JWT authentication."""

    def test_create_jwt_auth(self):
        """Test creating JWT authentication."""
        auth = create_jwt_auth()

        assert auth.name == "bearerAuth"
        assert auth.scheme == "bearer"

    def test_create_and_verify_token(self):
        """Test creating and verifying a JWT token."""
        auth = JWTAuth(name="test", expiration_minutes=60)

        token = auth.create_token({"user_id": 123, "username": "testuser"})

        assert token is not None
        assert len(token.split('.')) == 3  # JWT has 3 parts

        is_valid, payload, error = auth.verify_token(token)

        assert is_valid is True
        assert payload["user_id"] == 123
        assert error is None

    def test_verify_invalid_token(self):
        """Test verifying an invalid token."""
        auth = JWTAuth(name="test")

        is_valid, payload, error = auth.verify_token("invalid.token.here")

        assert is_valid is False
        assert payload is None
        assert error is not None

    def test_authenticate_with_bearer(self):
        """Test authenticating with bearer token."""
        auth = JWTAuth(name="test")

        token = auth.create_token({"user_id": 123})

        is_valid, error = auth.authenticate({"token": f"Bearer {token}"})

        assert is_valid is True
        assert error is None


class TestBasicAuth:
    """Tests for Basic authentication."""

    def test_add_user(self):
        """Test adding a user."""
        auth = BasicAuth(name="test")

        auth.add_user("testuser", "password123")

        assert "testuser" in auth.valid_credentials

    def test_authenticate_valid_credentials(self):
        """Test authenticating with valid credentials."""
        auth = BasicAuth(name="test")

        auth.add_user("testuser", "password123")

        is_valid, error = auth.authenticate({
            "username": "testuser",
            "password": "password123"
        })

        assert is_valid is True
        assert error is None

    def test_authenticate_invalid_credentials(self):
        """Test authenticating with invalid credentials."""
        auth = BasicAuth(name="test")

        auth.add_user("testuser", "password123")

        is_valid, error = auth.authenticate({
            "username": "testuser",
            "password": "wrongpassword"
        })

        assert is_valid is False
        assert "Invalid credentials" in error


class TestAuthManager:
    """Tests for AuthManager."""

    def test_add_scheme(self):
        """Test adding an authentication scheme."""
        manager = AuthManager()

        auth = create_api_key_auth()
        manager.add_scheme(auth)

        assert "apiKey" in manager.schemes

    def test_remove_scheme(self):
        """Test removing an authentication scheme."""
        manager = AuthManager()

        auth = create_api_key_auth()
        manager.add_scheme(auth)

        result = manager.remove_scheme("apiKey")

        assert result is True
        assert "apiKey" not in manager.schemes

    def test_get_scheme(self):
        """Test getting an authentication scheme."""
        manager = AuthManager()

        auth = create_api_key_auth()
        manager.add_scheme(auth)

        retrieved = manager.get_scheme("apiKey")

        assert retrieved is not None
        assert retrieved.name == "apiKey"

    def test_authenticate(self):
        """Test authenticating through manager."""
        manager = AuthManager()

        auth = APIKeyAuth(name="apiKey", location=APIKeyLocation.HEADER)
        key = auth.generate_key()
        manager.add_scheme(auth)

        is_valid, error = manager.authenticate("apiKey", {"X-API-Key": key})

        assert is_valid is True
        assert error is None

    def test_set_global_schemes(self):
        """Test setting global authentication schemes."""
        manager = AuthManager()

        manager.set_global_schemes(["apiKey", "bearerAuth"])

        assert "apiKey" in manager.global_schemes
        assert "bearerAuth" in manager.global_schemes

    def test_to_openapi_security_schemes(self):
        """Test converting to OpenAPI security schemes."""
        manager = AuthManager()

        auth = create_api_key_auth()
        manager.add_scheme(auth)

        schemes = manager.to_openapi_security_schemes()

        assert "apiKey" in schemes
        assert schemes["apiKey"]["type"] == "apiKey"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
