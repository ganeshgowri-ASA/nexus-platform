from fastapi import APIRouter, Request, Response, HTTPException
from sqlalchemy.orm import Session

from modules.api_gateway.database import SessionLocal
from modules.api_gateway.models.route import Route
from modules.api_gateway.services import ProxyService


class GatewayRouter:
    """Dynamic gateway router that proxies requests based on configured routes"""

    def __init__(self):
        self.router = APIRouter(tags=["Gateway"])
        self.proxy_service = ProxyService()

        # Register dynamic route handler
        self.router.add_api_route(
            "/{path:path}",
            self.handle_request,
            methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
        )

    async def handle_request(self, path: str, request: Request) -> Response:
        """
        Handle incoming requests and route them to appropriate backend services.

        This is the main gateway logic that:
        1. Matches the request to a configured route
        2. Applies authentication, rate limiting, caching
        3. Proxies the request to the backend service
        4. Returns the response
        """

        # Get route configuration from database
        route_config = self.get_route_config(
            method=request.method,
            path=f"/{path}"
        )

        if not route_config:
            raise HTTPException(
                status_code=404,
                detail=f"No route configured for {request.method} /{path}"
            )

        # Check if route is enabled
        if not route_config.get("enabled", True):
            raise HTTPException(
                status_code=503,
                detail="This route is currently disabled"
            )

        # Store route config in request state for middleware
        request.state.route_config = route_config

        # Proxy request to backend
        response = await self.proxy_service.proxy_request(request, route_config)

        return response

    def get_route_config(self, method: str, path: str) -> dict:
        """
        Find matching route configuration from database.

        Matches by method and path pattern.
        """

        db = SessionLocal()
        try:
            # Query for exact match first
            route = db.query(Route).filter(
                Route.method == method.upper(),
                Route.path == path,
                Route.enabled == True
            ).first()

            if route:
                return self._route_to_dict(route)

            # Try to find pattern match (e.g., /api/users/:id)
            # For now, just exact match - pattern matching can be added later
            routes = db.query(Route).filter(
                Route.method == method.upper(),
                Route.enabled == True
            ).all()

            for route in routes:
                if self._path_matches(path, route.path):
                    return self._route_to_dict(route)

            return None

        finally:
            db.close()

    def _path_matches(self, request_path: str, route_path: str) -> bool:
        """
        Check if request path matches route path pattern.

        Supports:
        - Exact match: /api/users
        - Wildcard: /api/users/*
        - Parameters: /api/users/:id (future)
        """

        if request_path == route_path:
            return True

        # Wildcard matching
        if route_path.endswith("/*"):
            prefix = route_path[:-2]
            return request_path.startswith(prefix)

        # Could add more sophisticated matching here (regex, parameters, etc.)

        return False

    def _route_to_dict(self, route: Route) -> dict:
        """Convert Route model to dict for use in proxy service"""

        return {
            "id": route.id,
            "name": route.name,
            "path": route.path,
            "method": route.method,
            "target_url": route.target_url,
            "enabled": route.enabled,
            "require_auth": route.require_auth,
            "rate_limit": route.rate_limit,
            "rate_limit_window": route.rate_limit_window,
            "load_balance_strategy": route.load_balance_strategy,
            "target_urls": route.target_urls or [route.target_url],
            "cache_enabled": route.cache_enabled,
            "cache_ttl": route.cache_ttl,
            "request_transform": route.request_transform,
            "response_transform": route.response_transform,
            "headers_to_add": route.headers_to_add,
            "headers_to_remove": route.headers_to_remove,
            "timeout": route.timeout,
        }
