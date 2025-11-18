from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
import jwt

from modules.api_gateway.database import SessionLocal
from modules.api_gateway.models.api_key import APIKey
from modules.api_gateway.config import settings


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware for API authentication (API keys and JWT)"""

    EXCLUDED_PATHS = [
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/auth/login",
        "/auth/register",
    ]

    async def dispatch(self, request: Request, call_next):
        """Process authentication"""

        # Skip auth for excluded paths
        if any(request.url.path.startswith(path) for path in self.EXCLUDED_PATHS):
            return await call_next(request)

        # Get route configuration from request state (set by routing middleware)
        route_config = getattr(request.state, "route_config", None)

        # Skip auth if route doesn't require it
        if route_config and not route_config.get("require_auth", True):
            return await call_next(request)

        # Try to authenticate
        auth_result = await self.authenticate(request)

        if not auth_result["authenticated"]:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "Unauthorized",
                    "message": auth_result.get("message", "Invalid or missing authentication"),
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Store auth info in request state
        request.state.auth = auth_result

        response = await call_next(request)
        return response

    async def authenticate(self, request: Request) -> dict:
        """
        Authenticate request using API key or JWT token.

        Returns:
            dict with 'authenticated' (bool) and other auth info
        """

        # Try API Key authentication first
        api_key = request.headers.get("X-API-Key") or request.query_params.get("api_key")

        if api_key:
            return await self.authenticate_api_key(api_key)

        # Try JWT Bearer token
        auth_header = request.headers.get("Authorization")

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            return await self.authenticate_jwt(token)

        return {"authenticated": False, "message": "No authentication provided"}

    async def authenticate_api_key(self, api_key: str) -> dict:
        """Authenticate using API key"""

        db = SessionLocal()
        try:
            # Query API key from database
            key_record = db.query(APIKey).filter(APIKey.key == api_key).first()

            if not key_record:
                return {"authenticated": False, "message": "Invalid API key"}

            if not key_record.active:
                return {"authenticated": False, "message": "API key is inactive"}

            # Check expiration
            if key_record.expires_at and key_record.expires_at < datetime.utcnow():
                return {"authenticated": False, "message": "API key has expired"}

            # Update usage
            key_record.total_requests += 1
            key_record.last_used_at = datetime.utcnow()
            db.commit()

            return {
                "authenticated": True,
                "type": "api_key",
                "api_key_id": key_record.id,
                "user_id": key_record.user_id,
                "scopes": key_record.scopes,
                "rate_limit": key_record.rate_limit,
                "rate_limit_window": key_record.rate_limit_window,
            }

        except Exception as e:
            print(f"API key authentication error: {e}")
            return {"authenticated": False, "message": "Authentication error"}
        finally:
            db.close()

    async def authenticate_jwt(self, token: str) -> dict:
        """Authenticate using JWT token"""

        try:
            # Decode JWT token
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )

            # Check expiration
            exp = payload.get("exp")
            if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
                return {"authenticated": False, "message": "Token has expired"}

            return {
                "authenticated": True,
                "type": "jwt",
                "user_id": payload.get("sub"),
                "scopes": payload.get("scopes", []),
                "email": payload.get("email"),
            }

        except jwt.ExpiredSignatureError:
            return {"authenticated": False, "message": "Token has expired"}
        except jwt.InvalidTokenError:
            return {"authenticated": False, "message": "Invalid token"}
        except Exception as e:
            print(f"JWT authentication error: {e}")
            return {"authenticated": False, "message": "Authentication error"}
