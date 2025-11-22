"""
Middleware Components

Custom middleware for FastAPI application.
"""

import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from config.settings import settings
from config.logging import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all HTTP requests."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Log request details and response time.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler

        Returns:
            HTTP response
        """
        start_time = time.time()

        # Log request
        logger.info(
            "Incoming request",
            method=request.method,
            path=request.url.path,
            client=request.client.host if request.client else None,
        )

        # Process request
        response = await call_next(request)

        # Calculate processing time
        process_time = time.time() - start_time

        # Log response
        logger.info(
            "Request completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            process_time=f"{process_time:.3f}s",
        )

        # Add processing time header
        response.headers["X-Process-Time"] = str(process_time)

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware."""

    def __init__(self, app, max_requests: int = 60, window_seconds: int = 60):
        """
        Initialize rate limiter.

        Args:
            app: FastAPI application
            max_requests: Maximum requests per window
            window_seconds: Time window in seconds
        """
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Check rate limits before processing request.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler

        Returns:
            HTTP response
        """
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()

        # Initialize or clean up request history
        if client_ip not in self.requests:
            self.requests[client_ip] = []

        # Remove old requests outside the window
        self.requests[client_ip] = [
            req_time
            for req_time in self.requests[client_ip]
            if current_time - req_time < self.window_seconds
        ]

        # Check rate limit
        if len(self.requests[client_ip]) >= self.max_requests:
            logger.warning(
                "Rate limit exceeded",
                client=client_ip,
                requests=len(self.requests[client_ip]),
            )
            return Response(
                content="Rate limit exceeded",
                status_code=429,
            )

        # Add current request
        self.requests[client_ip].append(current_time)

        # Process request
        return await call_next(request)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware to authenticate requests using JWT tokens."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Authenticate request using JWT token.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler

        Returns:
            HTTP response
        """
        from nexus.core.security import decode_access_token
        from nexus.core.exceptions import AuthenticationError

        # Skip authentication for public endpoints
        public_paths = ["/docs", "/redoc", "/openapi.json", "/health"]
        if any(request.url.path.startswith(path) for path in public_paths):
            return await call_next(request)

        # Get authorization header
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            logger.warning("Missing or invalid authorization header")
            return Response(
                content="Missing or invalid authorization header",
                status_code=401,
            )

        # Extract and validate token
        token = auth_header.split(" ")[1]

        try:
            payload = decode_access_token(token)
            request.state.user = payload
        except AuthenticationError as e:
            logger.warning(f"Authentication failed: {e.message}")
            return Response(
                content=e.message,
                status_code=401,
            )

        return await call_next(request)


def setup_cors(app) -> None:
    """
    Configure CORS middleware.

    Args:
        app: FastAPI application
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def setup_middleware(app) -> None:
    """
    Configure all middleware for the application.

    Args:
        app: FastAPI application
    """
    # Add request logging
    app.add_middleware(RequestLoggingMiddleware)

    # Add rate limiting
    app.add_middleware(
        RateLimitMiddleware,
        max_requests=settings.API_RATE_LIMIT_PER_MINUTE,
        window_seconds=60,
    )

    # Add CORS
    setup_cors(app)

    logger.info("Middleware configured successfully")
