from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime

from modules.api_gateway.database import redis_client
from modules.api_gateway.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting requests"""

    EXCLUDED_PATHS = ["/health", "/docs", "/redoc", "/openapi.json"]

    async def dispatch(self, request: Request, call_next):
        """Process rate limiting"""

        # Skip rate limiting for excluded paths
        if any(request.url.path.startswith(path) for path in self.EXCLUDED_PATHS):
            return await call_next(request)

        # Get identifier for rate limiting
        identifier = self.get_identifier(request)

        # Get rate limit configuration
        route_config = getattr(request.state, "route_config", None)
        auth_info = getattr(request.state, "auth", None)

        # Determine rate limit (priority: route config > auth config > default)
        if route_config and route_config.get("rate_limit"):
            rate_limit = route_config["rate_limit"]
            window = route_config.get("rate_limit_window", settings.DEFAULT_RATE_LIMIT_WINDOW)
        elif auth_info and auth_info.get("rate_limit"):
            rate_limit = auth_info["rate_limit"]
            window = auth_info.get("rate_limit_window", settings.DEFAULT_RATE_LIMIT_WINDOW)
        else:
            rate_limit = settings.DEFAULT_RATE_LIMIT
            window = settings.DEFAULT_RATE_LIMIT_WINDOW

        # Check rate limit
        is_allowed, remaining = redis_client.rate_limit_check(
            identifier, rate_limit, window
        )

        if not is_allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "message": f"Rate limit exceeded. Try again later.",
                    "retry_after": window,
                },
                headers={
                    "X-RateLimit-Limit": str(rate_limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(datetime.utcnow().timestamp()) + window),
                    "Retry-After": str(window),
                },
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(
            int(datetime.utcnow().timestamp()) + window
        )

        return response

    def get_identifier(self, request: Request) -> str:
        """Get identifier for rate limiting (API key, user ID, or IP)"""

        # Use API key if available
        auth_info = getattr(request.state, "auth", None)
        if auth_info:
            if auth_info.get("api_key_id"):
                return f"apikey:{auth_info['api_key_id']}"
            elif auth_info.get("user_id"):
                return f"user:{auth_info['user_id']}"

        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()

        return f"ip:{client_ip}"
