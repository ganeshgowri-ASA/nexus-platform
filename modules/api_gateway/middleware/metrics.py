from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime
import time

from modules.api_gateway.database import SessionLocal
from modules.api_gateway.models.metric import Metric


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting request/response metrics"""

    async def dispatch(self, request: Request, call_next):
        """Collect metrics for each request"""

        # Start timer
        start_time = time.time()

        # Get request size
        request_size = int(request.headers.get("content-length", 0))

        # Process request
        try:
            response = await call_next(request)
            error = False
            error_message = None
            error_type = None
        except Exception as e:
            error = True
            error_message = str(e)
            error_type = type(e).__name__
            # Re-raise to let error handlers deal with it
            raise
        finally:
            # Calculate response time
            response_time = (time.time() - start_time) * 1000  # Convert to ms

            # Get response info
            status_code = response.status_code if 'response' in locals() else 500
            response_size = int(response.headers.get("content-length", 0)) if 'response' in locals() else 0

            # Get client info
            client_ip = request.client.host if request.client else "unknown"
            forwarded = request.headers.get("X-Forwarded-For")
            if forwarded:
                client_ip = forwarded.split(",")[0].strip()

            user_agent = request.headers.get("User-Agent")

            # Get auth info
            auth_info = getattr(request.state, "auth", None)
            api_key_id = auth_info.get("api_key_id") if auth_info else None

            # Get route info
            route_config = getattr(request.state, "route_config", None)
            route_name = route_config.get("name") if route_config else None

            # Get cache info
            cache_hit = getattr(request.state, "cache_hit", False)

            # Get backend info
            backend_url = getattr(request.state, "backend_url", None)
            backend_response_time = getattr(request.state, "backend_response_time", None)

            # Save metric to database (async in background)
            self.save_metric(
                timestamp=datetime.utcnow(),
                method=request.method,
                path=request.url.path,
                route_name=route_name,
                status_code=status_code,
                response_time=response_time,
                client_ip=client_ip,
                user_agent=user_agent,
                api_key_id=api_key_id,
                request_size=request_size,
                response_size=response_size,
                error=error,
                error_message=error_message,
                error_type=error_type,
                backend_url=backend_url,
                backend_response_time=backend_response_time,
                cache_hit=cache_hit,
            )

        # Add custom headers
        response.headers["X-Response-Time"] = f"{response_time:.2f}ms"

        return response

    def save_metric(self, **kwargs):
        """Save metric to database"""
        try:
            db = SessionLocal()
            metric = Metric(**kwargs)
            db.add(metric)
            db.commit()
            db.close()
        except Exception as e:
            print(f"Error saving metric: {e}")
