"""Request logging middleware for FastAPI and Streamlit applications."""

import time
import uuid
from typing import Callable, Optional

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses."""

    def __init__(
        self,
        app: ASGIApp,
        logger_name: str = "nexus.requests",
        skip_paths: Optional[list[str]] = None,
    ):
        """Initialize request logging middleware.

        Args:
            app: ASGI application
            logger_name: Name for the logger
            skip_paths: List of paths to skip logging (e.g., health checks)
        """
        super().__init__(app)
        self.logger = structlog.get_logger(logger_name)
        self.skip_paths = skip_paths or ["/health", "/metrics"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            HTTP response
        """
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Skip logging for certain paths
        if request.url.path in self.skip_paths:
            return await call_next(request)

        # Extract request information
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        method = request.method
        url = str(request.url)
        path = request.url.path

        # Start timing
        start_time = time.time()

        # Log request
        self.logger.info(
            "request_started",
            request_id=request_id,
            method=method,
            path=path,
            url=url,
            client_ip=client_ip,
            user_agent=user_agent,
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Log response
            self.logger.info(
                "request_completed",
                request_id=request_id,
                method=method,
                path=path,
                status_code=response.status_code,
                duration_ms=round(duration * 1000, 2),
                client_ip=client_ip,
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as exc:
            # Calculate duration
            duration = time.time() - start_time

            # Log error
            self.logger.error(
                "request_failed",
                request_id=request_id,
                method=method,
                path=path,
                duration_ms=round(duration * 1000, 2),
                error=str(exc),
                error_type=type(exc).__name__,
                client_ip=client_ip,
            )

            # Re-raise the exception
            raise


class StreamlitRequestLogger:
    """Request logger for Streamlit applications."""

    def __init__(self, logger_name: str = "nexus.streamlit"):
        """Initialize Streamlit request logger.

        Args:
            logger_name: Name for the logger
        """
        self.logger = structlog.get_logger(logger_name)

    def log_page_view(
        self,
        page_name: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs: str,
    ) -> None:
        """Log a page view in Streamlit.

        Args:
            page_name: Name of the page viewed
            user_id: User identifier if available
            session_id: Session identifier
            **kwargs: Additional context
        """
        log_data = {
            "event": "page_view",
            "page_name": page_name,
        }

        if user_id:
            log_data["user_id"] = user_id
        if session_id:
            log_data["session_id"] = session_id

        log_data.update(kwargs)

        self.logger.info("streamlit_page_view", **log_data)

    def log_interaction(
        self,
        interaction_type: str,
        component: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs: str,
    ) -> None:
        """Log a user interaction in Streamlit.

        Args:
            interaction_type: Type of interaction (click, input, select, etc.)
            component: Component that was interacted with
            user_id: User identifier if available
            session_id: Session identifier
            **kwargs: Additional context
        """
        log_data = {
            "event": "user_interaction",
            "interaction_type": interaction_type,
            "component": component,
        }

        if user_id:
            log_data["user_id"] = user_id
        if session_id:
            log_data["session_id"] = session_id

        log_data.update(kwargs)

        self.logger.info("streamlit_interaction", **log_data)

    def log_error(
        self,
        error: Exception,
        context: Optional[dict] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> None:
        """Log an error in Streamlit.

        Args:
            error: The exception that occurred
            context: Additional context
            user_id: User identifier if available
            session_id: Session identifier
        """
        log_data = {
            "event": "error",
            "error_type": type(error).__name__,
            "error_message": str(error),
        }

        if context:
            log_data["context"] = context
        if user_id:
            log_data["user_id"] = user_id
        if session_id:
            log_data["session_id"] = session_id

        self.logger.error("streamlit_error", **log_data)
