"""
NEXUS API Builder & Documentation Module

A comprehensive API development platform with visual designer, auto-documentation,
testing, mocking, and code generation capabilities.

Rivals: Postman, Swagger, Stoplight
"""

from .builder import APIBuilder, APIProject
from .endpoints import Endpoint, EndpointManager, HTTPMethod, ParameterType
from .auth import (
    AuthScheme,
    APIKeyAuth,
    JWTAuth,
    OAuth2Auth,
    BasicAuth,
    AuthManager,
)
from .rate_limiting import (
    RateLimiter,
    RateLimitRule,
    ThrottlePolicy,
    QuotaManager,
)
from .docs import (
    OpenAPIGenerator,
    DocumentationGenerator,
    InteractiveExplorer,
)
from .testing import (
    APITester,
    TestCase,
    TestCollection,
    ResponseValidator,
)
from .mock import (
    MockServer,
    MockResponse,
    MockScenario,
)
from .versioning import (
    APIVersion,
    VersionManager,
    DeprecationWarning as APIDeprecationWarning,
)

__version__ = "1.0.0"
__all__ = [
    # Core
    "APIBuilder",
    "APIProject",
    # Endpoints
    "Endpoint",
    "EndpointManager",
    "HTTPMethod",
    "ParameterType",
    # Authentication
    "AuthScheme",
    "APIKeyAuth",
    "JWTAuth",
    "OAuth2Auth",
    "BasicAuth",
    "AuthManager",
    # Rate Limiting
    "RateLimiter",
    "RateLimitRule",
    "ThrottlePolicy",
    "QuotaManager",
    # Documentation
    "OpenAPIGenerator",
    "DocumentationGenerator",
    "InteractiveExplorer",
    # Testing
    "APITester",
    "TestCase",
    "TestCollection",
    "ResponseValidator",
    # Mocking
    "MockServer",
    "MockResponse",
    "MockScenario",
    # Versioning
    "APIVersion",
    "VersionManager",
    "APIDeprecationWarning",
]
