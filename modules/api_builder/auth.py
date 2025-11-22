"""
Authentication Module

Supports API keys, JWT, OAuth2, Basic auth, and custom authentication schemes.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from datetime import datetime, timedelta
import secrets
import hashlib
import hmac
import base64
import json
import time


class AuthType(Enum):
    """Authentication types."""
    API_KEY = "apiKey"
    HTTP = "http"
    OAUTH2 = "oauth2"
    OPENID_CONNECT = "openIdConnect"
    CUSTOM = "custom"


class APIKeyLocation(Enum):
    """Where the API key should be sent."""
    HEADER = "header"
    QUERY = "query"
    COOKIE = "cookie"


class OAuth2FlowType(Enum):
    """OAuth2 flow types."""
    IMPLICIT = "implicit"
    PASSWORD = "password"
    CLIENT_CREDENTIALS = "clientCredentials"
    AUTHORIZATION_CODE = "authorizationCode"


@dataclass
class AuthScheme:
    """Base authentication scheme."""
    name: str
    type: AuthType
    description: str = ""
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for OpenAPI spec."""
        return {
            "type": self.type.value,
            "description": self.description,
        }

    def authenticate(self, credentials: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Authenticate credentials. Returns (success, error_message)."""
        raise NotImplementedError("Subclasses must implement authenticate()")


@dataclass
class APIKeyAuth(AuthScheme):
    """API Key authentication."""
    location: APIKeyLocation = APIKeyLocation.HEADER
    parameter_name: str = "X-API-Key"
    valid_keys: List[str] = field(default_factory=list)

    def __post_init__(self):
        if self.type != AuthType.API_KEY:
            self.type = AuthType.API_KEY

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for OpenAPI spec."""
        return {
            "type": self.type.value,
            "description": self.description,
            "name": self.parameter_name,
            "in": self.location.value,
        }

    def authenticate(self, credentials: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Authenticate API key."""
        api_key = credentials.get(self.parameter_name)

        if not api_key:
            return False, f"Missing {self.parameter_name}"

        if api_key in self.valid_keys:
            return True, None

        return False, "Invalid API key"

    def generate_key(self, prefix: str = "sk") -> str:
        """Generate a new API key."""
        random_part = secrets.token_urlsafe(32)
        key = f"{prefix}_{random_part}"
        self.valid_keys.append(key)
        return key

    def revoke_key(self, key: str) -> bool:
        """Revoke an API key."""
        if key in self.valid_keys:
            self.valid_keys.remove(key)
            return True
        return False


@dataclass
class BasicAuth(AuthScheme):
    """HTTP Basic authentication."""
    scheme: str = "basic"
    valid_credentials: Dict[str, str] = field(default_factory=dict)  # username: hashed_password

    def __post_init__(self):
        if self.type != AuthType.HTTP:
            self.type = AuthType.HTTP

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for OpenAPI spec."""
        return {
            "type": self.type.value,
            "description": self.description,
            "scheme": self.scheme,
        }

    def _hash_password(self, password: str, salt: Optional[str] = None) -> tuple[str, str]:
        """Hash a password with salt."""
        if salt is None:
            salt = secrets.token_hex(16)

        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return base64.b64encode(pwd_hash).decode(), salt

    def add_user(self, username: str, password: str) -> None:
        """Add a user with hashed password."""
        pwd_hash, salt = self._hash_password(password)
        self.valid_credentials[username] = f"{salt}${pwd_hash}"

    def authenticate(self, credentials: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Authenticate basic auth credentials."""
        username = credentials.get("username")
        password = credentials.get("password")

        if not username or not password:
            return False, "Missing username or password"

        if username not in self.valid_credentials:
            return False, "Invalid credentials"

        stored = self.valid_credentials[username]
        salt, stored_hash = stored.split('$')
        pwd_hash, _ = self._hash_password(password, salt)

        if pwd_hash == stored_hash:
            return True, None

        return False, "Invalid credentials"


@dataclass
class JWTAuth(AuthScheme):
    """JWT (Bearer) authentication."""
    scheme: str = "bearer"
    bearer_format: str = "JWT"
    secret_key: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    algorithm: str = "HS256"
    expiration_minutes: int = 60

    def __post_init__(self):
        if self.type != AuthType.HTTP:
            self.type = AuthType.HTTP

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for OpenAPI spec."""
        return {
            "type": self.type.value,
            "description": self.description,
            "scheme": self.scheme,
            "bearerFormat": self.bearer_format,
        }

    def _base64_url_encode(self, data: bytes) -> str:
        """Base64 URL encode."""
        return base64.urlsafe_b64encode(data).rstrip(b'=').decode()

    def _base64_url_decode(self, data: str) -> bytes:
        """Base64 URL decode."""
        padding = 4 - (len(data) % 4)
        data = data + ('=' * padding)
        return base64.urlsafe_b64decode(data)

    def create_token(self, payload: Dict[str, Any]) -> str:
        """Create a JWT token."""
        # Header
        header = {
            "alg": self.algorithm,
            "typ": "JWT"
        }

        # Add expiration
        now = int(time.time())
        payload = payload.copy()
        payload["iat"] = now
        payload["exp"] = now + (self.expiration_minutes * 60)

        # Encode
        header_encoded = self._base64_url_encode(json.dumps(header).encode())
        payload_encoded = self._base64_url_encode(json.dumps(payload).encode())

        # Sign
        message = f"{header_encoded}.{payload_encoded}"
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).digest()
        signature_encoded = self._base64_url_encode(signature)

        return f"{message}.{signature_encoded}"

    def verify_token(self, token: str) -> tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """Verify a JWT token. Returns (valid, payload, error)."""
        try:
            parts = token.split('.')
            if len(parts) != 3:
                return False, None, "Invalid token format"

            header_encoded, payload_encoded, signature_encoded = parts

            # Verify signature
            message = f"{header_encoded}.{payload_encoded}"
            expected_signature = hmac.new(
                self.secret_key.encode(),
                message.encode(),
                hashlib.sha256
            ).digest()
            expected_signature_encoded = self._base64_url_encode(expected_signature)

            if signature_encoded != expected_signature_encoded:
                return False, None, "Invalid signature"

            # Decode payload
            payload = json.loads(self._base64_url_decode(payload_encoded))

            # Check expiration
            if "exp" in payload:
                if time.time() > payload["exp"]:
                    return False, None, "Token expired"

            return True, payload, None

        except Exception as e:
            return False, None, str(e)

    def authenticate(self, credentials: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Authenticate JWT token."""
        token = credentials.get("token")

        if not token:
            return False, "Missing token"

        # Remove "Bearer " prefix if present
        if token.startswith("Bearer "):
            token = token[7:]

        valid, payload, error = self.verify_token(token)
        if not valid:
            return False, error

        return True, None


@dataclass
class OAuth2Flow:
    """OAuth2 flow configuration."""
    flow_type: OAuth2FlowType
    authorization_url: Optional[str] = None
    token_url: Optional[str] = None
    refresh_url: Optional[str] = None
    scopes: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {}

        if self.authorization_url:
            result["authorizationUrl"] = self.authorization_url
        if self.token_url:
            result["tokenUrl"] = self.token_url
        if self.refresh_url:
            result["refreshUrl"] = self.refresh_url
        if self.scopes:
            result["scopes"] = self.scopes

        return result


@dataclass
class OAuth2Auth(AuthScheme):
    """OAuth2 authentication."""
    flows: Dict[str, OAuth2Flow] = field(default_factory=dict)

    def __post_init__(self):
        if self.type != AuthType.OAUTH2:
            self.type = AuthType.OAUTH2

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for OpenAPI spec."""
        return {
            "type": self.type.value,
            "description": self.description,
            "flows": {
                flow_type: flow.to_dict()
                for flow_type, flow in self.flows.items()
            }
        }

    def add_flow(
        self,
        flow_type: OAuth2FlowType,
        authorization_url: Optional[str] = None,
        token_url: Optional[str] = None,
        scopes: Optional[Dict[str, str]] = None,
    ) -> None:
        """Add an OAuth2 flow."""
        self.flows[flow_type.value] = OAuth2Flow(
            flow_type=flow_type,
            authorization_url=authorization_url,
            token_url=token_url,
            scopes=scopes or {},
        )

    def authenticate(self, credentials: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Authenticate OAuth2 credentials."""
        # This is a simplified implementation
        # In production, you'd integrate with actual OAuth2 providers
        access_token = credentials.get("access_token")

        if not access_token:
            return False, "Missing access token"

        # Here you would validate the token with the OAuth2 provider
        # For now, we'll just check if it's not empty
        return True, None


@dataclass
class CustomAuth(AuthScheme):
    """Custom authentication scheme."""
    validator: Optional[Callable[[Dict[str, Any]], tuple[bool, Optional[str]]]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.type != AuthType.CUSTOM:
            self.type = AuthType.CUSTOM

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = super().to_dict()
        result.update(self.metadata)
        return result

    def set_validator(self, validator: Callable[[Dict[str, Any]], tuple[bool, Optional[str]]]) -> None:
        """Set the custom validation function."""
        self.validator = validator

    def authenticate(self, credentials: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Authenticate using custom validator."""
        if not self.validator:
            return False, "No validator configured"

        return self.validator(credentials)


class AuthManager:
    """Manages authentication schemes for an API."""

    def __init__(self):
        self.schemes: Dict[str, AuthScheme] = {}
        self.global_schemes: List[str] = []  # Default schemes applied to all endpoints

    def add_scheme(self, scheme: AuthScheme) -> None:
        """Add an authentication scheme."""
        self.schemes[scheme.name] = scheme

    def remove_scheme(self, name: str) -> bool:
        """Remove an authentication scheme."""
        if name in self.schemes:
            del self.schemes[name]
            if name in self.global_schemes:
                self.global_schemes.remove(name)
            return True
        return False

    def get_scheme(self, name: str) -> Optional[AuthScheme]:
        """Get an authentication scheme."""
        return self.schemes.get(name)

    def list_schemes(self) -> List[AuthScheme]:
        """List all authentication schemes."""
        return list(self.schemes.values())

    def set_global_schemes(self, scheme_names: List[str]) -> None:
        """Set schemes that apply globally to all endpoints."""
        self.global_schemes = scheme_names

    def authenticate(
        self,
        scheme_name: str,
        credentials: Dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """Authenticate credentials against a scheme."""
        scheme = self.schemes.get(scheme_name)

        if not scheme:
            return False, f"Unknown authentication scheme: {scheme_name}"

        if not scheme.enabled:
            return False, f"Authentication scheme '{scheme_name}' is disabled"

        return scheme.authenticate(credentials)

    def to_openapi_security_schemes(self) -> Dict[str, Dict[str, Any]]:
        """Convert to OpenAPI security schemes."""
        return {
            name: scheme.to_dict()
            for name, scheme in self.schemes.items()
        }

    def get_security_requirements(self) -> List[Dict[str, List[str]]]:
        """Get global security requirements for OpenAPI."""
        return [{name: []} for name in self.global_schemes]


# Utility functions for common authentication patterns

def create_api_key_auth(
    name: str = "apiKey",
    location: APIKeyLocation = APIKeyLocation.HEADER,
    parameter_name: str = "X-API-Key",
) -> APIKeyAuth:
    """Create a standard API key authentication scheme."""
    return APIKeyAuth(
        name=name,
        type=AuthType.API_KEY,
        location=location,
        parameter_name=parameter_name,
        description=f"API key authentication via {location.value}",
    )


def create_jwt_auth(
    name: str = "bearerAuth",
    expiration_minutes: int = 60,
) -> JWTAuth:
    """Create a standard JWT authentication scheme."""
    return JWTAuth(
        name=name,
        type=AuthType.HTTP,
        description="JWT bearer token authentication",
        expiration_minutes=expiration_minutes,
    )


def create_basic_auth(name: str = "basicAuth") -> BasicAuth:
    """Create a standard HTTP Basic authentication scheme."""
    return BasicAuth(
        name=name,
        type=AuthType.HTTP,
        description="HTTP Basic authentication",
    )


def create_oauth2_auth(
    name: str = "oauth2",
    authorization_url: str = "",
    token_url: str = "",
    scopes: Optional[Dict[str, str]] = None,
) -> OAuth2Auth:
    """Create a standard OAuth2 authentication scheme."""
    auth = OAuth2Auth(
        name=name,
        type=AuthType.OAUTH2,
        description="OAuth2 authentication",
    )

    auth.add_flow(
        OAuth2FlowType.AUTHORIZATION_CODE,
        authorization_url=authorization_url,
        token_url=token_url,
        scopes=scopes or {},
    )

    return auth
