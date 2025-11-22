"""
Rate limiting middleware
"""

import time
from collections import defaultdict
from typing import Dict, Tuple
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiting middleware
    For production, consider using Redis-based rate limiting
    """

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.request_counts: Dict[str, list] = defaultdict(list)

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process each request and apply rate limiting"""

        # Skip rate limiting for certain paths
        if self._should_skip_rate_limit(request.url.path):
            return await call_next(request)

        # Get client identifier (IP address or user ID from token)
        client_id = self._get_client_identifier(request)

        # Check rate limits
        current_time = time.time()
        self._cleanup_old_requests(client_id, current_time)

        if not self._check_rate_limit(client_id, current_time):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                },
            )

        # Add request timestamp
        self.request_counts[client_id].append(current_time)

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        remaining = self._get_remaining_requests(client_id, current_time)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(int(current_time + 60))

        return response

    def _should_skip_rate_limit(self, path: str) -> bool:
        """Check if path should skip rate limiting"""
        skip_paths = [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/metrics",
        ]
        return any(path.startswith(skip_path) for skip_path in skip_paths)

    def _get_client_identifier(self, request: Request) -> str:
        """Get unique client identifier from request"""
        # Try to get user ID from request state (set by auth dependency)
        if hasattr(request.state, "user_id"):
            return f"user_{request.state.user_id}"

        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        return request.client.host if request.client else "unknown"

    def _cleanup_old_requests(self, client_id: str, current_time: float) -> None:
        """Remove request timestamps older than 1 hour"""
        hour_ago = current_time - 3600
        self.request_counts[client_id] = [
            timestamp
            for timestamp in self.request_counts[client_id]
            if timestamp > hour_ago
        ]

    def _check_rate_limit(self, client_id: str, current_time: float) -> bool:
        """Check if client has exceeded rate limits"""
        requests = self.request_counts[client_id]

        # Check requests per minute
        minute_ago = current_time - 60
        requests_last_minute = sum(1 for ts in requests if ts > minute_ago)
        if requests_last_minute >= self.requests_per_minute:
            return False

        # Check requests per hour
        hour_ago = current_time - 3600
        requests_last_hour = sum(1 for ts in requests if ts > hour_ago)
        if requests_last_hour >= self.requests_per_hour:
            return False

        return True

    def _get_remaining_requests(self, client_id: str, current_time: float) -> int:
        """Get remaining requests for the current minute"""
        minute_ago = current_time - 60
        requests_last_minute = sum(
            1 for ts in self.request_counts[client_id] if ts > minute_ago
        )
        return self.requests_per_minute - requests_last_minute
