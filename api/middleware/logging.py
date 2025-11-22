"""
Request/Response logging middleware
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse


# Configure logger
logger = logging.getLogger("nexus.api")
logger.setLevel(logging.INFO)

# Create console handler with formatting
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
handler.setFormatter(formatter)
logger.addHandler(handler)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all API requests and responses
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response details"""

        # Start timer
        start_time = time.time()

        # Get request details
        method = request.method
        url = str(request.url)
        client_host = request.client.host if request.client else "unknown"

        # Get user info if authenticated
        user_id = getattr(request.state, "user_id", None)
        user_info = f" [User: {user_id}]" if user_id else ""

        # Log request
        logger.info(f"→ {method} {url} from {client_host}{user_info}")

        try:
            # Process request
            response = await call_next(request)

            # Calculate processing time
            process_time = time.time() - start_time
            process_time_ms = round(process_time * 1000, 2)

            # Log response
            status_code = response.status_code
            status_emoji = self._get_status_emoji(status_code)

            logger.info(
                f"← {method} {url} {status_emoji} {status_code} "
                f"({process_time_ms}ms){user_info}"
            )

            # Add processing time header
            response.headers["X-Process-Time"] = str(process_time_ms)

            return response

        except Exception as e:
            # Calculate processing time
            process_time = time.time() - start_time
            process_time_ms = round(process_time * 1000, 2)

            # Log error
            logger.error(
                f"✗ {method} {url} ERROR: {str(e)} "
                f"({process_time_ms}ms){user_info}",
                exc_info=True,
            )
            raise

    def _get_status_emoji(self, status_code: int) -> str:
        """Get emoji for status code range"""
        if 200 <= status_code < 300:
            return "✓"
        elif 300 <= status_code < 400:
            return "↻"
        elif 400 <= status_code < 500:
            return "⚠"
        elif 500 <= status_code < 600:
            return "✗"
        return "?"
