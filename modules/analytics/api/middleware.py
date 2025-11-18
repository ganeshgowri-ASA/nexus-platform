"""
API Middleware

Middleware for request tracking and rate limiting.
"""

import logging
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from modules.analytics.core.tracker import EventTracker
from modules.analytics.storage.cache import get_cache
from modules.analytics.storage.database import get_database
from shared.constants import DEFAULT_RATE_LIMIT_PER_MINUTE

logger = logging.getLogger(__name__)


class AnalyticsMiddleware(BaseHTTPMiddleware):
    """Middleware for tracking API requests."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and track analytics."""
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Track request
        try:
            duration = time.time() - start_time

            # Get tracker
            db = get_database()
            tracker = EventTracker(db, auto_start=False)

            # Track API request event
            tracker.track(
                name="api_request",
                event_type="api_request",
                properties={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration * 1000, 2),
                },
                user_agent=request.headers.get("user-agent"),
                ip_address=request.client.host if request.client else None,
            )

            # Flush immediately for API tracking
            tracker.flush()

        except Exception as e:
            logger.error(f"Error tracking request: {e}")

        # Add response headers
        response.headers["X-Response-Time"] = f"{duration:.4f}"

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting."""

    def __init__(self, app, rate_limit: int = DEFAULT_RATE_LIMIT_PER_MINUTE):
        """Initialize rate limit middleware."""
        super().__init__(app)
        self.rate_limit = rate_limit

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting."""
        # Get client identifier
        client_id = request.client.host if request.client else "unknown"

        # Check rate limit
        try:
            cache = get_cache()
            key = f"rate_limit:{client_id}"

            # Increment request count
            count = cache.increment(key, 1, ttl=60)

            # Check if over limit
            if count > self.rate_limit:
                logger.warning(f"Rate limit exceeded for {client_id}")
                return Response(
                    content="Rate limit exceeded",
                    status_code=429,
                    headers={"Retry-After": "60"}
                )

        except Exception as e:
            logger.error(f"Error in rate limiting: {e}")
            # Continue without rate limiting on error

        # Process request
        return await call_next(request)
