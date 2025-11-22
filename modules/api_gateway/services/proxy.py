import httpx
import time
from typing import Dict, Optional, Any
from fastapi import Request, Response
from fastapi.responses import StreamingResponse

from modules.api_gateway.services.cache import CacheService
from modules.api_gateway.services.transformer import TransformerService
from modules.api_gateway.services.load_balancer import LoadBalancer
from modules.api_gateway.config import settings


class ProxyService:
    """Service for proxying requests to backend services"""

    def __init__(self):
        self.cache_service = CacheService()
        self.transformer = TransformerService()
        self.load_balancer = LoadBalancer()

    async def proxy_request(
        self,
        request: Request,
        route_config: Dict[str, Any],
    ) -> Response:
        """
        Proxy a request to the backend service.

        Args:
            request: FastAPI request object
            route_config: Route configuration dict

        Returns:
            FastAPI Response object
        """

        # Check cache if enabled
        if route_config.get("cache_enabled", False):
            cache_key = self.cache_service.generate_cache_key(
                request.method,
                request.url.path,
                dict(request.query_params),
            )

            cached_response = self.cache_service.get_cached_response(cache_key)

            if cached_response:
                # Mark as cache hit
                request.state.cache_hit = True

                return Response(
                    content=cached_response.get("content", ""),
                    status_code=cached_response.get("status_code", 200),
                    headers=cached_response.get("headers", {}),
                    media_type=cached_response.get("media_type"),
                )

        # Select backend URL (load balancing)
        target_urls = route_config.get("target_urls", [])
        if not target_urls:
            target_urls = [route_config["target_url"]]

        strategy = route_config.get("load_balance_strategy", "round_robin")
        client_ip = request.client.host if request.client else None

        backend_url = self.load_balancer.select_backend(
            target_urls, strategy, client_ip
        )

        # Store backend URL in request state for metrics
        request.state.backend_url = backend_url

        # Build target URL
        target_path = request.url.path
        if request.url.query:
            target_path = f"{target_path}?{request.url.query}"

        full_url = f"{backend_url.rstrip('/')}/{target_path.lstrip('/')}"

        # Get request body
        body = await request.body()

        # Transform request if needed
        if route_config.get("request_transform"):
            if body:
                body = self.transformer.transform_request(
                    body.decode(), route_config["request_transform"]
                )
                if isinstance(body, dict):
                    import json
                    body = json.dumps(body).encode()
                elif isinstance(body, str):
                    body = body.encode()

        # Prepare headers
        headers = dict(request.headers)

        # Remove hop-by-hop headers
        hop_by_hop = [
            "connection", "keep-alive", "proxy-authenticate",
            "proxy-authorization", "te", "trailers", "transfer-encoding", "upgrade"
        ]
        headers = {k: v for k, v in headers.items() if k.lower() not in hop_by_hop}

        # Transform headers if needed
        if route_config.get("headers_to_add"):
            headers.update(route_config["headers_to_add"])

        if route_config.get("headers_to_remove"):
            for header in route_config["headers_to_remove"]:
                headers.pop(header, None)

        # Make request to backend
        timeout = route_config.get("timeout", settings.DEFAULT_TIMEOUT)

        start_time = time.time()

        try:
            self.load_balancer.increment_connections(backend_url)

            async with httpx.AsyncClient(timeout=timeout) as client:
                backend_response = await client.request(
                    method=request.method,
                    url=full_url,
                    headers=headers,
                    content=body,
                )

            backend_response_time = (time.time() - start_time) * 1000
            request.state.backend_response_time = backend_response_time

        except httpx.TimeoutException:
            return Response(
                content='{"error": "Backend timeout"}',
                status_code=504,
                media_type="application/json",
            )
        except httpx.ConnectError:
            return Response(
                content='{"error": "Backend unavailable"}',
                status_code=503,
                media_type="application/json",
            )
        except Exception as e:
            print(f"Proxy error: {e}")
            return Response(
                content=f'{{"error": "Proxy error: {str(e)}"}}',
                status_code=502,
                media_type="application/json",
            )
        finally:
            self.load_balancer.decrement_connections(backend_url)

        # Get response content
        response_content = backend_response.content

        # Transform response if needed
        if route_config.get("response_transform"):
            try:
                response_data = backend_response.json()
                transformed = self.transformer.transform_response(
                    response_data, route_config["response_transform"]
                )
                import json
                response_content = json.dumps(transformed).encode()
            except:
                pass  # Keep original content if transformation fails

        # Prepare response headers
        response_headers = dict(backend_response.headers)

        # Cache response if enabled
        if (
            route_config.get("cache_enabled", False)
            and backend_response.status_code == 200
            and request.method == "GET"
        ):
            cache_data = {
                "content": response_content.decode(),
                "status_code": backend_response.status_code,
                "headers": response_headers,
                "media_type": backend_response.headers.get("content-type"),
            }

            cache_ttl = route_config.get("cache_ttl", settings.DEFAULT_CACHE_TTL)
            self.cache_service.cache_response(cache_key, cache_data, cache_ttl)

        return Response(
            content=response_content,
            status_code=backend_response.status_code,
            headers=response_headers,
        )
